"""Direct supplied optical-Z depth backprojection. Identity metric frame, no scale fitting."""
import json,hashlib,time
from pathlib import Path
import numpy as np
import cv2
OUT=Path(__file__).parent;ROOT=OUT.parents[3]
p=json.load(open(ROOT/'data/packets/M3/packet.json'));a=json.load(open(OUT/'annotations.json'));frames={f['keyframe_index']:f for f in p['frames']};cache={};access=[]

def depth_path(f):
 for key in ['geometry','depth','depth_path','depth_npy','optical_z_depth','metric_depth']:
  if key in f:
   v=f[key];return v['path'] if isinstance(v,dict) else v
 raise KeyError('No supplied depth: '+str(f.keys()))
def geometry(fid):
 if fid in cache:return cache[fid]
 f=frames[fid];path=depth_path(f);bundle=np.load(path)
 d=np.squeeze(bundle['depth_z_m']);h,w=d.shape;K=np.array(bundle['intrinsics']);supplied_valid=bundle['valid_mask'].astype(bool)
 assert np.allclose(bundle['camera_to_world'],f['camera_to_world']), 'Conflicting supplied pose copies'
 yy,xx=np.mgrid[:h,:w];rays=np.stack([(xx-K[0,2])/K[0,0],(yy-K[1,2])/K[1,1],np.ones_like(xx)],-1);cam=rays*d[...,None];T=np.array(f['camera_to_world']);xyz=cam@T[:3,:3].T+T[:3,3];valid=np.isfinite(d)&(d>0)&(d<100)&supplied_valid
 access.append({'frame':fid,'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'shape':[h,w],'K_used':K.tolist()});cache[fid]=(xyz,valid,d);return cache[fid]
def region(fid,poly=None,box=None):
 xyz,valid,d=geometry(fid);h,w=d.shape;mask=np.zeros((h,w),np.uint8)
 if box:
  x0,y0,x1,y1=box;poly=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
 cv2.fillPoly(mask,[np.rint(np.array(poly)*[w-1,h-1]).astype(np.int32)],1);ok=valid&(mask>0);return xyz[ok],d[ok]
def summary(X,z):
 if not len(X):return {'n':0}
 return {'n':len(X),'xyz_quantiles':np.quantile(X,[.05,.25,.5,.75,.95],axis=0).tolist(),'depth_quantiles':np.quantile(z,[.05,.25,.5,.75,.95]).tolist()}
report={'packet_sha256':hashlib.sha256(open(ROOT/'data/packets/M3/packet.json','rb').read()).hexdigest(),'method':'Direct optical-Z + intrinsics + supplied OpenVINS camera_to_world. No re-scaling, alignment, ICP, GT or other method inputs. Manual RGB semantic regions.','planes':[],'objects':[]}
for r in a['planar_regions']:
 X,z=region(r['frame'],r['polygon']);stats=summary(X,z)
 if len(X):
  axis=2 if r['id'] in ['floor','ceiling'] else (0 if r['id'] in ['end_wall','entry_wall'] else 1);med=np.median(X[:,axis]);stats['axis']=axis;stats['axis_median']=float(med);stats['axis_abs_residual_q50_q90']=np.quantile(abs(X[:,axis]-med),[.5,.9]).tolist()
 report['planes'].append({**r,**stats})
for o in a['objects']:
 measures=[]
 for ob in o['observations']:
  X,z=region(ob['frame'],box=ob['box']);measures.append({**ob,**summary(X,z)})
 report['objects'].append({**o,'measurements':measures})
json.dump(report,open(OUT/'depth_semantic_measurements.json','w'),indent=2);json.dump(access,open(OUT/'depth_access.json','w'),indent=2)
# Sparse depth visualization is diagnostic only and never exported as scene geometry.
cloud=[];colors=[]
for fid in sorted(set(r['frame'] for r in a['planar_regions'])|set(ob['frame'] for o in a['objects'] for ob in o['observations'])):
 xyz,valid,d=geometry(fid);im=cv2.imread(frames[fid]['rgb']);im=cv2.resize(im,(d.shape[1],d.shape[0]));ok=valid[::6,::6];cloud.extend(xyz[::6,::6][ok]);colors.extend(im[::6,::6,::-1][ok])
np.savez_compressed(OUT/'supplied_depth_diagnostic.npz',xyz=np.array(cloud),rgb=np.array(colors))
print(json.dumps(report,indent=1))
