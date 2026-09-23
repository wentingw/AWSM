"""Create method-isolated modelling packet from allowed observations only."""
from pathlib import Path
import argparse,hashlib,json,numpy as np
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--method',choices=['M3','M4'],required=True);ap.add_argument('--windows',type=Path,required=True);a=ap.parse_args()
 poses={}
 if a.method=='M3':
  from scipy.spatial.transform import Rotation
  path=ROOT/'experiments/world_lobby/M3/openvins_20260923/openvins_camera_pose_180.tum'
  for row in np.loadtxt(path):
   T=np.eye(4);T[:3,:3]=Rotation.from_quat(row[4:8]).as_matrix();T[:3,3]=row[1:4];poses[int(round(row[0]*1e9))]=T.tolist()
 rgb=json.loads((ROOT/'data/world_lobby/rgb_180_manifest.json').read_text())['frames'];chosen={}
 for mp in sorted(a.windows.glob('window_*/manifest.json')):
  d=json.loads(mp.read_text());n=len(d['frames'])
  if d.get('status')!='complete':continue
  for i,f in enumerate(d['frames']):
   k=f['keyframe_index'];rank=min(i,n-1-i)
   if k not in chosen or rank>chosen[k][0]:chosen[k]=(rank,mp.parent,f)
 out=ROOT/'data/packets'/a.method;out.mkdir(parents=True,exist_ok=True)
 records=[]
 for f in rgb:
  k=f['keyframe_index'];row={'keyframe_index':k,'timestamp_ns':f['timestamp_ns'],'rgb':f['sampled_rgb'],'rgb_sha256':f['sha256']}
  if poses:
   t=min(poses,key=lambda t:abs(t-f['timestamp_ns']))
   if abs(t-f['timestamp_ns'])<10000:row.update(camera_to_world=poses[t],pose_convention='OpenCV optical RDF camera-to-world',pose_units='m')
  if k in chosen:
   rank,folder,d=chosen[k];p=folder/d['data'];v=np.load(p);target=out/f'{k:03d}_geometry.npz'
   np.savez_compressed(target,depth_z_m=v['depth_z'],intrinsics=v['intrinsics'],camera_to_world=v['input_camera_pose'],valid_mask=v['mask'],confidence=v['confidence'])
   row.update(geometry=str(target),geometry_sha256=sha(target),geometry_source=str(p),processed_rgb=str(folder/d['processed_image']),pose_convention='OpenCV optical RDF camera-to-world',units='m',depth_axis='optical_z',window_selection_centrality=rank)
  records.append(row)
 packet={'method_id':a.method,'status':'complete' if len(chosen)==(180 if a.method=='M4' else 175) else 'partial','geometry_frames':len(chosen),'rgb_frames':180,'allowed_inputs':'sampled RGB + supplied metric camera poses + MapAnything depth; no GT mesh/depth/object labels','pose_source':'GT camera poses only' if a.method=='M4' else 'OpenVINS estimated camera poses','depth_source':'MapAnything joint 4-view windows overlap2, native output without GT depth fitting','input_intrinsics':[[762.8,0,640],[0,762.8,480],[0,0,1]],'input_resolution_wh':[1280,960],'coordinate_frame':'native input-camera world; preserve axes/units or export exact transform','deduplication':'largest min(local_index,window_length-1-local_index); earliest window breaks ties','frames':records,'forbidden_inputs':['other reconstructed models','GT geometry/depth','evaluation reports','other methods scene programs'],'output_contract':str(ROOT/'configs/astra_modelling_contract.md')}
 temp=out/'packet.tmp.json';temp.write_text(json.dumps(packet,indent=2)+'\n');temp.replace(out/'packet.json')
 print(json.dumps({'packet':str(out/'packet.json'),'geometry_frames':len(chosen),'status':packet['status']}))
if __name__=='__main__':main()
