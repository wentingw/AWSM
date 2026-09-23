"""Allowed RGB + fixed supplied OpenVINS pose triangulation; no pose fitting/GT."""
import json, hashlib, time
from pathlib import Path
import numpy as np
import cv2
ROOT=Path('/home/hchen/Documents/astraBlenderTest/world_model_blog')
OUT=ROOT/'experiments/world_lobby/M3/astra_model'
p=json.load(open(ROOT/'data/packets/M3/packet.json'))
K=np.array([[762.8,0,640],[0,762.8,480],[0,0,1.]])
frames={f['keyframe_index']:f for f in p['frames']}
ids=list(range(5,156,3));cache={};sift=cv2.SIFT_create(nfeatures=5500)
for i in ids:
 im=cv2.imread(frames[i]['rgb']);g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);kp,d=sift.detectAndCompute(g,None);cache[i]=(np.array([k.pt for k in kp]),d,im)
cloud=[];colors=[];meta=[];pairs=[]
matcher=cv2.BFMatcher()
for ai,i in enumerate(ids):
 for gap in [1,2,4,7]:
  if ai+gap>=len(ids):continue
  j=ids[ai+gap];T1=np.array(frames[i]['camera_to_world']);T2=np.array(frames[j]['camera_to_world']);baseline=np.linalg.norm(T1[:3,3]-T2[:3,3]);
  if baseline<.3 or baseline>9:continue
  a,d1,im=cache[i];b,d2,_=cache[j];matches=matcher.knnMatch(d1,d2,k=2);good=[m for m,n in matches if m.distance<.66*n.distance]
  if len(good)<6:continue
  aa=np.array([a[m.queryIdx] for m in good]);bb=np.array([b[m.trainIdx] for m in good]);P1=K@np.linalg.inv(T1)[:3];P2=K@np.linalg.inv(T2)[:3];h=cv2.triangulatePoints(P1,P2,aa.T,bb.T).T;X=h[:,:3]/h[:,3:]
  hom=np.column_stack([X,np.ones(len(X))]);u1=hom@P1.T;u2=hom@P2.T;err=np.maximum(np.linalg.norm(u1[:,:2]/u1[:,2:]-aa,axis=1),np.linalg.norm(u2[:,:2]/u2[:,2:]-bb,axis=1));r1=X-T1[:3,3];r2=X-T2[:3,3];cos=np.sum(r1*r2,axis=1)/(np.linalg.norm(r1,axis=1)*np.linalg.norm(r2,axis=1));ang=np.degrees(np.arccos(np.clip(cos,-1,1)));ok=(err<2.5)&(u1[:,2]>.2)&(u2[:,2]>.2)&(u1[:,2]<45)&(u2[:,2]<45)&(ang>2)
  ix=np.where(ok)[0];cloud.extend(X[ix]);colors.extend(im[np.rint(aa[ix,1]).astype(int),np.rint(aa[ix,0]).astype(int),::-1]);meta.extend(np.column_stack([np.full(len(ix),i),np.full(len(ix),j),aa[ix],bb[ix],err[ix],ang[ix]]));pairs.append({'i':i,'j':j,'baseline_m':baseline,'matches':len(good),'accepted':len(ix)})
np.savez_compressed(OUT/'rgb_pose_triangulation.npz',xyz=np.array(cloud),rgb=np.array(colors),observations=np.array(meta))
json.dump({'method':'SIFT ratio .66, fixed supplied poses, two-view linear triangulation; max reprojection 2.5px; ray angle >2 degrees; no scaling or pose adjustment','K':K.tolist(),'pairs':pairs,'accepted_points':len(cloud),'coordinate_frame':'native OpenVINS, metres','rgb_frames_read':ids},open(OUT/'triangulation_report.json','w'),indent=2)
print('points',len(cloud));print('xyz quantiles',np.quantile(np.array(cloud),[.01,.1,.5,.9,.99],axis=0))
