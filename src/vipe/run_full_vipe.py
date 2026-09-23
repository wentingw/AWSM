"""RGB-only ViPE, checkpointed SLAM and streamed native optical-Z depth.

Input is exclusively the named PNG directory. Timestamp mapping comes from its
filenames. No calibration, IMU, SfM, MapAnything, or truth files are opened.
"""
import gc
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import hydra
import numpy as np
import torch

VENDOR = Path('/home/hchen/Documents/astraBlenderTest/reconstruction/vendor/vipe')

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

@hydra.main(version_base=None, config_path=str(VENDOR/'configs'), config_name='default')
def run(args):
    from vipe.config import validate_typed_config
    from vipe.pipeline import make_pipeline
    from vipe.streams.base import StreamList, AssignAttributesProcessor, FrameAttribute, ProcessedVideoStream
    from vipe.pipeline.processors import AdaptiveDepthProcessor
    from vipe.utils.logging import configure_logging
    from vipe.utils.cameras import CameraType
    start = time.monotonic()
    workspace = Path(__file__).resolve().parents[2]
    config = validate_typed_config(args)
    logger = configure_logging()
    streams = StreamList.make(config.streams)
    stream = streams[0]
    assert hasattr(stream, 'frame_files'), 'Only original PNG directory accepted'
    files = stream.frame_files[stream.start:stream.end:stream.step]
    timestamps_ns = np.array([int(p.stem.split('_')[-1]) for p in files], dtype=np.int64)
    assert len(files) >= 8 and np.all(np.diff(timestamps_ns) > 0)
    stream._fps = 1e9 / float(np.median(np.diff(timestamps_ns)))
    from rgb_reference_cache import install
    install(files)
    out = Path(config.pipeline.output.path)
    assert out.resolve().is_relative_to(workspace / 'experiments'), 'Output must stay in independent experiments'
    out.mkdir(parents=True, exist_ok=True)
    identity = dict(streams=config.streams.model_dump(), init=config.pipeline.init.model_dump(),
                    slam=config.pipeline.slam.model_dump(), post=config.pipeline.post.model_dump(),
                    source_frames=[dict(index=i, path=str(p.resolve()), timestamp_ns=int(t), sha256=sha(p))
                                   for i, (p,t) in enumerate(zip(files, timestamps_ns))],
                    target_pixels=os.environ.get('VIPE_SLAM_TARGET_PIXELS'),
                    rgb_cache='immutable PNG readthrough; metadata cached; exact pixel equality checked',
                    inference_inputs='RGB PNG files only', fps=stream.fps(),
                    vipe_git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=VENDOR,text=True).strip(),
                    runner_sha256=sha(__file__))
    (out/'vendor_changes.patch').write_bytes(subprocess.check_output(['git','diff','--','vipe'],cwd=VENDOR))
    checkpoint = out/'slam_checkpoint.pt'
    provenance = out/'input_provenance.json'
    pipeline = make_pipeline(config.pipeline)
    pipeline.return_payload = True
    if checkpoint.exists():
        previous=json.loads(provenance.read_text())
        before=dict(previous);after=dict(identity)
        before.pop('runner_sha256');after.pop('runner_sha256')
        assert before == after, 'Checkpoint inputs/configuration differ'
        if previous['runner_sha256'] != identity['runner_sha256']:
            assert os.environ.get('VIPE_ALLOW_SCHEDULER_RESUME') == '1', 'Explicit scheduler-only resume approval required'
        (out/'resume_provenance.json').write_text(json.dumps(dict(previous_runner=previous['runner_sha256'],current_runner=identity['runner_sha256'],identity_fields_equal_excluding_runner_hash=True,change_scope='depth scheduling only; existing SLAM outputs unchanged'),indent=2)+'\n')
        slam = torch.load(checkpoint, weights_only=False)
        logger.info('Resumed ViPE camera checkpoint')
    else:
        provenance.write_text(json.dumps(identity, indent=2)+'\n')
        result = pipeline.run(stream)
        slam = result.payload
        assert slam is not None
        torch.save(slam, out/'slam_checkpoint.partial.pt')
        (out/'slam_checkpoint.partial.pt').replace(checkpoint)
        logger.info('CHECKPOINTED ViPE camera solution')
    pipeline.model_cache.clear()
    gc.collect()
    torch.cuda.empty_cache()
    n = len(stream)
    poses = slam.get_view_trajectory(0).matrix().cpu().numpy()
    K = slam.intrinsics[0].cpu().numpy()
    assert poses.shape == (n,4,4) and np.isfinite(poses).all()
    np.savez(out/'camera.npz', camera_to_world=poses, intrinsics=K, timestamps_ns=timestamps_ns,
             indices=np.arange(n), source_resolution_wh=np.array([stream.frame_size()[1],stream.frame_size()[0]]))
    slam.slam_map.save(out/'slam_map.pt')
    init = AssignAttributesProcessor({FrameAttribute.POSE:slam.get_view_trajectory(0),
        FrameAttribute.INTRINSICS:[slam.intrinsics[0]]*n, FrameAttribute.CAMERA_TYPE:[CameraType.PINHOLE]*n})
    processor = AdaptiveDepthProcessor(slam,0,config.pipeline.post.depth_align_model)
    assert processor.video_depth_model is None
    processor.require_cache = False
    from indexed_depth import scheduled_depth
    phase=os.environ.get("VIPE_DEPTH_PHASE","keyframes")
    assert phase in ("keyframes","rest","all")
    depthdir = out/'depth'; depthdir.mkdir(exist_ok=True)
    records=[];existing_indices=[]
    if phase == 'rest':
        for target in sorted(depthdir.glob('[0-9][0-9][0-9][0-9][0-9][0-9].npz')):
            i=int(target.stem)
            with np.load(target) as v:
                assert int(v['timestamp_ns'])==int(timestamps_ns[i]) and np.allclose(v['camera_to_world'],poses[i])
                shape=list(v['depth_z_m'].shape)
            records.append(dict(index=i,path=str(target.resolve()),sha256=sha(target),shape=shape,timestamp_ns=int(timestamps_ns[i])))
            existing_indices.append(i)
    output_stream, selected_count, depth_schedule_hash = scheduled_depth(processor,files,slam.get_view_trajectory(0),slam.intrinsics[0],phase,skip=existing_indices)
    with torch.inference_mode():
        for completed,(i,frame) in enumerate(output_stream,1):
            depth = frame.metric_depth.cpu().numpy().astype(np.float32)
            target = depthdir/f'{i:06d}.npz'
            partial = depthdir/f'{i:06d}.partial.npz'
            np.savez_compressed(partial, depth_z_m=depth, intrinsics=frame.intrinsics.cpu().numpy(),
                                timestamp_ns=timestamps_ns[i], camera_to_world=poses[i])
            partial.replace(target)
            records.append(dict(index=i,path=str(target.resolve()),sha256=sha(target),shape=list(depth.shape),timestamp_ns=int(timestamps_ns[i])))
            (out/'progress.json').write_text(json.dumps(dict(stage='depth',completed_frames=len(records),total_frames=n,current_source_index=i))+'\n')
            if phase != "rest" and completed == selected_count:
                (out/'modelling_ready.json').write_text(json.dumps(dict(status='SAMPLED_DEPTH_COMPLETE_FULL_DEPTH_CONTINUES',full_video_pose=str(out/'camera.npz'),sampled_depth=records.copy(),sampling_stride=50,depth_schedule_hash=depth_schedule_hash),indent=2)+'\n')
            if completed%10==0: logger.info('VIPE_DEPTH_FRAME %d/%d original_index=%d',completed,n,i)
    if phase == "keyframes":
        assert len(records)==selected_count
        (out/'keyframe_stage_complete.json').write_text(json.dumps(dict(status='FULL_POSE_AND_KEYFRAME_DEPTH_COMPLETE_REST_PENDING',pose_frames=n,depth_frames=len(records),seconds=time.monotonic()-start),indent=2)+'\n')
        logger.info('VIPE keyframe stage done; releasing GPU; remaining frame depths queued separately')
        return
    assert len(records)==n
    records.sort(key=lambda r:r['index'])
    result = dict(status='COMPLETE',frames=n,backend='ViPE no_vda + UniDepth V2 small',
                  camera='ViPE SLAM with learned metric depth; GeoCalib initial intrinsics, joint intrinsics optimization',
                  depth='ViPE AdaptiveDepthProcessor adaptive_unidepth-s; optical Z in native near-metric units',
                  inference_inputs=f'{n} original RGB PNG images only; no IMU, external poses/depth, or truth',
                  scale_fitted_to_truth=False,seconds=time.monotonic()-start,
                  camera_sha256=sha(out/'camera.npz'),input_provenance_sha256=sha(provenance),depth_frames=records)
    (out/'complete.json').write_text(json.dumps(result,indent=2)+'\n')
    logger.info('VIPE_STABLE_COMPLETE %d frames in %.1f seconds',n,result['seconds'])

if __name__=='__main__': run()
