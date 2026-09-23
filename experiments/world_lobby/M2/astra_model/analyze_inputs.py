import json,numpy as np,hashlib,time
from pathlib import Path
from PIL import Image,ImageDraw
O=Path(__file__).parent; root=O.parents[3]; packet=root/'data/packets/M2/packet.json'; p=json.load(open(packet));
logs=[{'path':str(root/'configs/astra_modelling_contract.md'),'purpose':'contract'},{'path':str(packet),'purpose':'input packet'}]; clouds=[]; cols=[]; frs=[]; cams=[]
for i,f in enumerate(p['frames']):
 a=np.load(f['geometry']); K=a['intrinsics']; C=a['camera_to_world']; D=a['depth_z_m']; rgb=np.array(Image.open(f['rgb'])); v,u=np.mgrid[0:D.shape[0]:12,0:D.shape[1]:12]; d=D[v,u]; valid=np.isfinite(d)&(d>0)&(d<60)&a['valid_mask'][v,u]; pc=np.stack([(u-K[0,2])*d/K[0,0],(v-K[1,2])*d/K[1,1],d],-1); pw=pc@C[:3,:3].T+C[:3,3];clouds.append(pw[valid]);cols.append(rgb[v,u][valid]);frs.append(np.full(valid.sum(),i));cams.append({'frame_id':i,'rgb':f['rgb'],'K':K.tolist(),'c2w_input':C.tolist(),'width':D.shape[1],'height':D.shape[0]})
 for typ in ['rgb','geometry']:logs.append({'path':f[typ],'sha256':hashlib.sha256(open(f[typ],'rb').read()).hexdigest(),'purpose':'RGB evidence and native ViPE geometric measurement'})
P=np.concatenate(clouds);colors=np.concatenate(cols);F=np.concatenate(frs)
np.savez_compressed(O/'measurements_input.npz',points=P,colors=colors,frame_ids=F)
json.dump({'accesses':logs,'forbidden_inputs_accessed':[]},open(O/'input_access_log.json','w'),indent=2);json.dump({'cameras':cams},open(O/'cameras_input.json','w'),indent=2)
print('point quantiles',np.quantile(P,[.005,.05,.5,.95,.995],axis=0));print('camera samples',[(i,np.round(np.array(cams[i]['c2w_input'])[:3,3],3).tolist()) for i in range(0,180,10)])
# Floor first-view manually chosen visually plain stone bottom-right and black rug lower-middle.
a=np.load(p['frames'][0]['geometry']);D=a['depth_z_m'];K=a['intrinsics'];C=a['camera_to_world'];v,u=np.mgrid[600:940:4,930:1240:4];d=D[v,u];Q=np.stack([(u-K[0,2])*d/K[0,0],(v-K[1,2])*d/K[1,1],d],-1).reshape(-1,3)@C[:3,:3].T+C[:3,3]
rng=np.random.default_rng(2);best=None
for j in range(1000):
 q=Q[rng.choice(len(Q),3,False)];n=np.cross(q[1]-q[0],q[2]-q[0]);n/=np.linalg.norm(n);err=abs((Q-q[0])@n);mask=err<.025
 if best is None or mask.sum()>best.sum():best=mask
q=Q[best];_,_,vt=np.linalg.svd(q-q.mean(0),full_matrices=False);n=vt[-1];n=n if n[1]<0 else -n;offset=-n@q.mean(0)
print('floor',n,offset,'inlier',len(q),'rms',np.std(q@n));
# choose X camera right projected into floor, Y forward, Z up; exact rigid, no scale.
x=np.array([1.,0,0]);x-=n*(x@n);x/=np.linalg.norm(x);y=np.cross(n,x);R=np.stack([x,y,n]);T=np.eye(4);T[:3,:3]=R;T[2,3]=offset
Pm=P@R.T+T[:3,3];print('model quantiles',np.quantile(Pm,[.005,.05,.5,.95,.995],axis=0));print('T',T.tolist());np.savez_compressed(O/'measurements_model.npz',points=Pm,colors=colors,frame_ids=F)
json.dump({'T_input_model':T.tolist(),'scale':1.,'floor_fit':{'normal_input':n.tolist(),'offset':offset,'support_pixels_frame0':[930,600,1240,940],'inliers':len(q),'rms':float(np.std(q@n))}},open(O/'geometry_analysis.json','w'),indent=2)
for c in cams:c['c2w_model']=(T@np.array(c['c2w_input'])).tolist()
json.dump({'coordinate_frame':'model Z-up, exact rigid normalization','T_input_model':T.tolist(),'cameras':cams},open(O/'cameras.json','w'),indent=2)
