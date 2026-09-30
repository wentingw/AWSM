import json,numpy as np
from skimage.feature import SIFT
from scipy.spatial import cKDTree
from PIL import Image
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;p=json.load(open(B.parents[3]/'data/packets/M4/packet.json'));log=json.load(open(B/'input_access_log.json'));sift=SIFT(c_dog=.009);fs={}; ids=[0]+list(range(42,128,3))
for i in ids:
 f=p['frames'][i];a=np.load(f['geometry']);D=a['depth_z_m'];h,w=D.shape;im=np.asarray(Image.open(f['rgb']).resize((w,h)));sift.detect_and_extract(im.mean(2)/255);kp=sift.keypoints[:,::-1];de=sift.descriptors;T=a['camera_to_world'];P=a['intrinsics']@np.linalg.inv(T)[:3];fs[i]=(im,kp,de,P,T,a['intrinsics']);log['accessed'].append({'path':f['rgb'],'purpose':'SIFT RGB multiview triangulation permitted camera poses','frame_id':i})
points=[];colors=[];indices=[];matches=[];matcher=None
for ii,i in enumerate(ids):
 for j in ids[ii+1:]:
  im,kp,de,P,T,K=fs[i];jm,jp,je,Q,U,L=fs[j];base=np.linalg.norm(T[:3,3]-U[:3,3]);dot=T[:3,2]@U[:3,2]
  if base<.3 or base>7 or dot<.1:continue
  dist,idx=cKDTree(je).query(de,k=2);good=np.flatnonzero(dist[:,0]<.62*dist[:,1])
  if len(good)<5:continue
  a=kp[good].astype(float);b=jp[idx[good,0]].astype(float)
  mats=np.stack([a[:,0,None]*P[2]-P[0],a[:,1,None]*P[2]-P[1],b[:,0,None]*Q[2]-Q[0],b[:,1,None]*Q[2]-Q[1]],axis=1);_,_,V=np.linalg.svd(mats);X=V[:,-1,:3]/V[:,-1,3,None]
  xa=np.c_[X,np.ones(len(X))]@P.T;xb=np.c_[X,np.ones(len(X))]@Q.T;err=np.maximum(np.linalg.norm(xa[:,:2]/xa[:,2,None]-a,axis=1),np.linalg.norm(xb[:,:2]/xb[:,2,None]-b,axis=1));ok=(err<.7)&(xa[:,2]>.5)&(xb[:,2]>.5)&(xa[:,2]<30)&(X[:,2]>-.3)&(X[:,2]<6)
  for pt,uv,vv,valid in zip(X,a,b,ok):
   if valid:points.append(pt);colors.append(im[round(uv[1]),round(uv[0])]);indices.append([i,j]);matches.append([*uv,*vv])
ps=np.asarray(points);cs=np.asarray(colors);np.savez_compressed(B/'rgb_triangulated_measurements.npz',points=ps,colors=cs,frame_pairs=indices,pixels=matches);print('Triangulated',len(ps),'quantiles',np.percentile(ps,[1,5,50,95,99],axis=0).round(3))
fig,ax=plt.subplots(1,3,figsize=(18,7));
for a,ij in zip(ax,[(0,1),(0,2),(1,2)]):
 a.scatter(ps[:,ij[0]],ps[:,ij[1]],s=1,c=cs/255);a.set_aspect('equal');a.set_xlabel('xyz'[ij[0]]);a.set_ylabel('xyz'[ij[1]]);a.grid();a.set_xlim(np.percentile(ps[:,ij[0]],[.5,99.5]));a.set_ylim(np.percentile(ps[:,ij[1]],[.5,99.5]))
fig.savefig(B/'rgb_triangulated_overview.jpg',dpi=100)
for k in range(3):
 hist,ed=np.histogram(ps[:,k],bins=np.arange(-2,32,.05));ix=np.argsort(hist)[-15:];print('RGB_PEAKS','xyz'[k],sorted([(round(float((ed[j]+ed[j+1])/2),3),int(hist[j])) for j in ix]))
json.dump(log,open(B/'input_access_log.json','w'),indent=2)
