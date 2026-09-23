"""Join calibrated-RGB MapAnything windows using overlapping predicted cameras.

One SE3 per window from rotation consensus and mean camera-center translation;
no scale fit, no external camera or GT access. This is a window-chain baseline.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'experiments/world_lobby/B2/depth_20260923/full4_overlap2';assert (folder/'complete.json').exists()
known={};chosen={};windows=[]
for mp in sorted(folder.glob('window_*/manifest.json')):
 m=json.loads(mp.read_text());frames=m['frames'];local={f['keyframe_index']:np.load(mp.parent/f['data'])['output_camera_pose'] for f in frames};overlap=sorted(set(local)&set(known));T=np.eye(4)
 if overlap:
  Rs=np.array([known[k][:3,:3]@local[k][:3,:3].T for k in overlap]);U,_,V=np.linalg.svd(Rs.mean(0));D=np.eye(3);D[-1,-1]=np.linalg.det(U@V);R=U@D@V;t=np.mean([known[k][:3,3]-R@local[k][:3,3] for k in overlap],axis=0);T[:3,:3]=R;T[:3,3]=t
 merged={k:T@p for k,p in local.items()};terr=[float(np.linalg.norm(merged[k][:3,3]-known[k][:3,3])) for k in overlap];rerr=[float(np.degrees(Rotation.from_matrix(known[k][:3,:3].T@merged[k][:3,:3]).magnitude())) for k in overlap]
 for i,f in enumerate(frames):
  k=f['keyframe_index'];rank=min(i,len(frames)-1-i)
  if k not in known:known[k]=merged[k]
  if k not in chosen or rank>chosen[k][0]:chosen[k]=(rank,mp.parent,f,merged[k])
 windows.append({'window':str(mp.parent),'overlap_frame_indices':overlap,'T_local_to_chain':T.tolist(),'overlap_translation_residual_m':terr,'overlap_rotation_residual_deg':rerr})
assert set(chosen)==set(range(180));rgb=json.loads((ROOT/'data/world_lobby/rgb_180_manifest.json').read_text())['frames'];out=ROOT/'data/packets/B2';out.mkdir(parents=True,exist_ok=True);rows=[];poses=[];times=[]
for f in rgb:
 k=f['keyframe_index'];rank,d,w,T=chosen[k];v=np.load(d/w['data']);dest=out/f'{k:03d}_geometry.npz';np.savez_compressed(dest,depth_z_m=v['depth_z'],intrinsics=v['intrinsics'],camera_to_world=T,valid_mask=v['mask'],confidence=v['confidence']);rows.append(dict(keyframe_index=k,timestamp_ns=f['timestamp_ns'],rgb=f['sampled_rgb'],rgb_sha256=f['sha256'],geometry=str(dest),geometry_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),processed_rgb=str(d/w['processed_image']),geometry_source=str(d/w['data'])));poses.append(T);times.append(f['timestamp_ns'])
packet={'method_id':'B2','status':'complete','geometry_frames':180,'rgb_frames':180,'input_intrinsics':[[762.8,0,640],[0,762.8,480],[0,0,1]],'pose_source':'MapAnything calibrated RGB-only joint4 predictions; overlap-SE3 window chain','depth_source':'MapAnything native predicted metric scale; no per-window scale fitting','external_pose_input':False,'GT_access':False,'frames':rows,'window_alignment':windows,'limitations':['4-view GPU-limited windows','SE3 overlap chaining without loop closure','calibration K supplied, so calibrated-RGB baseline']}
(out/'packet.json').write_text(json.dumps(packet,indent=2)+'\n');np.savez(out/'camera.npz',camera_to_world=np.array(poses),timestamps_ns=np.array(times,dtype=np.int64));tum=np.column_stack([np.array(times)/1e9,np.array(poses)[:,:3,3],Rotation.from_matrix(np.array(poses)[:,:3,:3]).as_quat()]);np.savetxt(out/'camera.tum',tum,fmt='%.12f');print('B2 consolidated 180 frames')
