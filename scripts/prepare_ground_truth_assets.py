#!/usr/bin/env python3
"""Create small, auditable GT manifests without copying the 10M-triangle USD.

The output contains references and hashes only. GT assets are never passed to a
modelling input manifest. An independent trajectory is intentionally marked
missing until a new capture is supplied.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np

def sha(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--workspace',default='/home/hchen/Documents/astraBlenderTest/world_model_blog'); ap.add_argument('--project-root',default='/home/hchen/Documents/astraBlenderTest'); a=ap.parse_args()
    w=Path(a.workspace); root=Path(a.project_root); run=root/'vio-reconstruction/sessions/stable_orbit_20260921T044401'; gt=run/'ground_truth/camera_tum.txt'; frames=root/'vio-reconstruction/runs/stable_orbit_20260921T044401/keyframes_180/frames.csv'; calib=run/'inputs/calibration.json'; usd=root/'drone-web/scenes/world_lobby/Collected_World_Lobby/World_Lobby.usd'; scene=root/'drone-web/scenes/world_lobby/scene.json'
    rows=list(csv.DictReader(frames.open())); tum=np.loadtxt(gt,comments='#',ndmin=2)
    mapping=[]
    for r in rows:
        t=float(r['timestamp_ns'])/1e9; i=int(np.argmin(abs(tum[:,0]-t))); mapping.append({'keyframe_index':int(r['keyframe_index']),'source_frame_index':int(r['source_frame_index_zero_based']),'timestamp_s':t,'image_path':r['selected_rgb_absolute_path'],'gt_tum_row':i,'image_sha256':r['original_rgb_sha256']})
    # Deliberately same-video diagnostic frames; they are not independent holdout.
    diag=[mapping[i] for i in np.linspace(0,len(mapping)-1,20,dtype=int)]
    out=w/'results/ground_truth'; out.mkdir(parents=True,exist_ok=True)
    manifest={'schema_version':1,'scene_id':'WorldLobby360s','status':'references_only','gt_is_evaluation_only':True,'coordinate_convention':{'pose_file_format':'TUM timestamp tx ty tz qx qy qz qw','pose_frame':'world ENU metres; camera optical x-right y-down z-forward','intrinsics_fx_fy_cx_cy':[762.8,762.8,640.0,480.0],'distortion':[0,0,0,0],'T_imu_camera':json.loads(calib.read_text())['T_imu_camera'],'transform_convention':'p_imu = T_imu_camera @ p_camera'},'sources':{'camera_tum':{'path':str(gt),'sha256':sha(gt)},'calibration':{'path':str(calib),'sha256':sha(calib)},'ground_truth_usd':{'path':str(usd),'sha256':sha(usd)},'scene_json':{'path':str(scene),'sha256':sha(scene)}},'mapping':{'raw_frames':8999,'fps':25,'resolution':[1280,960],'sample_count':180,'sample_indices':'0,50,...,8950','frames':mapping},'same_video_withheld_from_modeller':{'count':20,'frames':diag,'is_true_holdout':False,'reason':'frontends may have observed the same video'},'independent_holdout':{'status':'missing','required':'new camera trajectory, RGB, GT pose, GT depth; hidden from every frontend','count':20},'gt_zdepth':{'status':'not_rendered','renderer_interface':'scripts/render_gt_depth_blender.py','required_camera_source':'mapping.frames and independent_holdout.frames','depth_axis':'camera optical z','resolution':[1280,960]},'gt_geometry':{'status':'referenced','mesh_path':str(usd),'triangles':9984967,'copy_policy':'do not copy or expose to modeller'}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n'); (out/'mapping_gt_tum.txt').write_text('\n'.join(' '.join(f'{x:.12g}' for x in tum[r['gt_tum_row']]) for r in mapping)+'\n')
    (out/'same_video_diagnostic_20.json').write_text(json.dumps(diag,indent=2)+'\n'); print(json.dumps({'manifest':str(out/'manifest.json'),'mapping_count':len(mapping),'independent_holdout':'missing','gt_usd_sha256':sha(usd)},indent=2))
if __name__=='__main__': main()
