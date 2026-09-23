import cv2,numpy as np,json,time
from pathlib import Path
O=Path(__file__).parent;p=json.load(open(O.parents[3]/'data/packets/M2/packet.json'));T=np.array(json.load(open(O/'geometry_analysis.json'))['T_input_model']);inds=[0,45,55,65,75,85,90,95,100,105,110,115,120,125,130,140];features={};cv2.setNumThreads(4);sift=cv2.SIFT_create(nfeatures=6500)
for i in inds:
 a=np.load(p['frames'][i]['geometry']);C=T@a['camera_to_world']; K=a['intrinsics'];rgb=cv2.imread(p['frames'][i]['rgb']);kp,des=sift.detectAndCompute(cv2.cvtColor(rgb,cv2.COLOR_BGR2GRAY),None);features[i]=(np.array([k.pt for k in kp]),des,K,C,rgb)
pts=[];cols=[];frs=[];errs=[];bf=cv2.BFMatcher()
for ii,i in enumerate(inds):
 uv,di,Ki,Ci,rgb=features[i];Pi=Ki@np.linalg.inv(Ci)[:3]
 for j in inds[ii+1:]:
  uj,dj,Kj,Cj,_=features[j];base=np.linalg.norm(Ci[:3,3]-Cj[:3,3]);
  if not .35<base<9:continue
  matches=bf.knnMatch(di,dj,k=2);pairs=[(m.queryIdx,m.trainIdx) for m,n in matches if m.distance<.68*n.distance]
  if len(pairs)<10:continue
  a=uv[[q[0] for q in pairs]];b=uj[[q[1] for q in pairs]];Pj=Kj@np.linalg.inv(Cj)[:3];h=cv2.triangulatePoints(Pi,Pj,a.T,b.T).T;q=h[:,:3]/h[:,3:];qh=np.c_[q,np.ones(len(q))];qa=qh@Pi.T;qb=qh@Pj.T;err=np.maximum(np.linalg.norm(qa[:,:2]/qa[:,2:]-a,axis=1),np.linalg.norm(qb[:,:2]/qb[:,2:]-b,axis=1));va=q-Ci[:3,3];vb=q-Cj[:3,3];cos=(va*vb).sum(1)/np.linalg.norm(va,axis=1)/np.linalg.norm(vb,axis=1);mask=(err<1.8)&(qa[:,2]>.3)&(qb[:,2]>.3)&(np.linalg.norm(va,axis=1)<30)&(cos<.9998)&(q[:,2]>-2)&(q[:,2]<8);q=q[mask];a=a[mask].astype(int);pts.extend(q);cols.extend(rgb[a[:,1],a[:,0],::-1]);frs.extend([[i,j]]*len(q));errs.extend(err[mask]);print(i,j,len(q),flush=True)
np.savez_compressed(O/'triangulated_measurements.npz',points=np.array(pts),colors=np.array(cols),frame_pairs=np.array(frs),reprojection_error=np.array(errs));print('TOTAL',len(pts))
json.dump({'method':'SIFT descriptor ratio 0.68 and calibrated two-view triangulation in supplied native ViPE pose scale','frames':inds,'max_reprojection_error_px':1.8,'minimum_ray_angle_deg':1.146,'scale_adjustments':[],'count':len(pts)},open(O/'triangulation_provenance.json','w'),indent=2)
