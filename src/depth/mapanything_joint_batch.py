"""Same four-view inference as M4, retaining model weights between windows."""
import argparse,copy,gc,json,sys,time
from pathlib import Path
from types import SimpleNamespace
from mapanything_window import frame_rows,calibration,match_pose,infer,sha
ROOT=Path(__file__).resolve().parents[2]

def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['M3','B2'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 base=ROOT.parent;frames=base/'vio-reconstruction/runs/stable_orbit_20260921T044401/keyframes_180/frames.csv';cal=ROOT/'data/world_lobby/calibration/camera_imu.json';rows=frame_rows(frames,frames.parent);K,c=calibration(cal)
 if a.mode=='M3':rows=match_pose(rows[5:],ROOT/'experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_180.tum')
 sys.path.insert(0,'/home/hchen/Documents/map-anything');import torch
 from mapanything.models.mapanything.model import MapAnything
 torch.set_num_threads(4);start=time.monotonic();model=MapAnything.from_pretrained('facebook/map-anything').to('cuda').eval()
 starts=list(range(0,len(rows)-3,2))
 if starts[-1]!=len(rows)-4:starts.append(len(rows)-4)
 prog={'status':'running','mode':a.mode,'frames_expected':len(rows),'windows_total':len(starts),'shared_weights':True,'configuration':'joint4 overlap2 with end-anchored final window','runner_sha256':sha(__file__),'window_runner_sha256':sha(Path(__file__).with_name('mapanything_window.py')),'completed':0}
 for wi,s in enumerate(starts):
  out=a.output/f'window_{wi:03d}';expected=[r['keyframe_index'] for r in rows[s:s+4]]
  if (out/'manifest.json').exists():
   old=json.loads((out/'manifest.json').read_text());assert [r['keyframe_index'] for r in old['frames']]==expected
  else:
   args=SimpleNamespace(repo='/home/hchen/Documents/map-anything',checkpoint='facebook/map-anything',device='cuda',output=out,resolution=518,minibatch=1,amp_dtype='bf16',no_amp=False)
   with torch.inference_mode():m=infer(args,copy.deepcopy(rows[s:s+4]),K,a.mode,model=model)
   m.update(calibration=c,calibration_sha256=sha(cal));(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
   gc.collect();torch.cuda.empty_cache()
  prog.update(completed=wi+1,elapsed_seconds=time.monotonic()-start,keyframes_last=expected);(a.output/'progress.json').write_text(json.dumps(prog,indent=2)+'\n');print(json.dumps(prog),flush=True)
 assert set(r['keyframe_index'] for mp in a.output.glob('window_*/manifest.json') for r in json.loads(mp.read_text())['frames'])==set(r['keyframe_index'] for r in rows)
 prog['status']='complete';(a.output/'complete.json').write_text(json.dumps(prog,indent=2)+'\n')
if __name__=='__main__':main()
