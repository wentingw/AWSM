import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json, hashlib, numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).parent
INPUT=ROOT.parent.parent/'inputs/M2'
P=json.loads((INPUT/'packet.json').read_text()); F=P['frames']; rng=np.random.default_rng(1702)
regions={
 'floor_33':(33,[(1080,750),(1230,810),(1230,930),(1170,940),(1050,810)]),
 'floor_61':(61,[(70,795),(290,700),(410,720),(465,860),(170,935)]),
 'floor_82':(82,[(50,620),(365,660),(435,770),(65,900)]),
 'floor_100':(100,[(200,800),(425,850),(360,930),(100,925)]),
 'floor_129':(129,[(1080,710),(1260,740),(1260,920),(1100,870)]),
 'wall_side_61':(61,[(470,150),(1220,145),(1170,295),(480,285)]),
 'wall_side_74':(74,[(400,210),(820,210),(810,315),(410,320)]),
 'wall_end_33':(33,[(450,250),(900,250),(900,340),(450,340)]),
 'wall_end_129':(129,[(1040,370),(1230,370),(1240,470),(1040,470)]),
 'ceiling_33':(33,[(530,5),(770,5),(790,110),(535,100)]),
 'window_100':(100,[(617,335),(763,334),(760,484),(612,480)]),
}
def points(i,poly=None,step=1):
 f=F[i]; n=np.load(f['geometry']); d=n['depth_z_m'];k=n['intrinsics'];h,w=d.shape; u,v=np.meshgrid(np.arange(w)+.5,np.arange(h)+.5);valid=n['valid_mask']&np.isfinite(d)&(d>.1)&(d<30)
 if poly:
  m=Image.new('1',(w,h)); ImageDraw.Draw(m).polygon([(x*w/1280,y*h/960) for x,y in poly],fill=1);valid &=np.array(m)
 mask=np.zeros_like(valid);mask[::step,::step]=1;valid &=mask
 xyz=np.stack([(u-k[0,2])/k[0,0]*d,(v-k[1,2])/k[1,1]*d,d],-1)[valid];T=np.array(f['camera_to_world']);return xyz@T[:3,:3].T+T[:3,3],np.stack([u,v],-1)[valid]*[1280/w,960/h]
def fit(a,niter=500,tol=.09):
 best=None
 for _ in range(niter):
  ps=a[rng.choice(len(a),3,False)]; n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);n/=np.linalg.norm(n)+1e-15; dd=ps[0]@n;mask=abs(a@n-dd)<tol
  if best is None or mask.sum()>best.sum():best=mask
 center=a[best].mean(0);_,_,vh=np.linalg.svd(a[best]-center,full_matrices=False);n=vh[-1];d=center@n;r=a@n-d
 return dict(normal=n.tolist(),offset=float(d),inlier_fraction=float(best.mean()),rmse_inliers=float(np.sqrt(np.mean(r[best]**2))),p10_p50_p90_signed=np.percentile(r,[10,50,90]).tolist(),points=len(a)),best
obs={}
for name,(i,poly) in regions.items():
 a,uv=points(i,poly); f,mask=fit(a);f.update(sample_index=i,rgb_polygon=poly,world_median=np.median(a,axis=0).tolist());obs[name]=f;print(name,f)
# joint floor: per-region valid RANSAC inliers, plane orientation consensus
fa=[]
for name,(i,poly) in regions.items():
 if name.startswith('floor'):
  a,_=points(i,poly);f,mask=fit(a);fa.append(a[mask])
f,mask=fit(np.concatenate(fa),tol=.16);normals=[]
for name,o in obs.items():
 if name.startswith('floor'):
  n=np.array(o['normal']);n*=np.sign(-n[1]);normals.append(n)
up=np.median(normals,axis=0);up/=np.linalg.norm(up)
right=np.array(obs['wall_side_61']['normal']);right*=np.sign(right[0]);right-=up*(right@up);right/=np.linalg.norm(right)
forward=np.cross(up,right);R=np.stack([right,forward,up]);floorcenter=np.median(np.concatenate(fa),axis=0);origin=np.array(F[33]['camera_to_world'])[:3,3];origin-=up*((origin-floorcenter)@up)
X=np.eye(4);X[:3,:3]=R;X[:3,3]=-R@origin
(ROOT/'analysis/transform.json').write_text(json.dumps({'model_from_input':X.tolist(),'floor_fit':f,'origin_input':origin.tolist(),'scale':1},indent=2))
# Backproject all frames at stride4 for measured bounds and plan inspection, not scene geometry.
pts=[];cols=[];ids=[]
for i in range(180):
 a,uv=points(i,step=4);a=a@R.T+X[:3,3];img=np.array(Image.open(F[i]['rgb']).convert('RGB'));uv=np.clip(uv.astype(int),[0,0],[1279,959]);c=img[uv[:,1],uv[:,0]];pts.append(a);cols.append(c);ids.append(np.full(len(a),i))
a=np.concatenate(pts);c=np.concatenate(cols);ids=np.concatenate(ids)
np.savez_compressed(ROOT/'analysis/measured_points.npz',points=a,colors=c,frame_ids=ids)
for name,o in obs.items():
 aa,_=points(o['sample_index'],o['rgb_polygon']);aa=aa@R.T+X[:3,3];o['model_quantiles_xyz']=np.percentile(aa,[5,50,95],axis=0).tolist()
(ROOT/'analysis/plane_observations.json').write_text(json.dumps(obs,indent=2))
print('X',X);print('point bounds',np.percentile(a,[1,50,99],axis=0));print('model region quantiles');print(json.dumps({k:v['model_quantiles_xyz'] for k,v in obs.items()},indent=2))
