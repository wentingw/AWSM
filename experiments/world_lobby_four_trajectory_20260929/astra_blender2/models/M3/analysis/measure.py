import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import numpy as np,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; I=R.parents[1]/'inputs/M3';P=json.loads((I/'packet.json').read_text()); records=[]
def points(i,box,step=1):
 f=P['frames'][i];n=np.load(f['geometry']);d=n['depth_z_m'];K=n['intrinsics'];T=np.array(f['camera_to_world']); h,w=d.shape
 u,v=np.meshgrid(np.arange(w)+.5,np.arange(h)+.5);ok=n['valid_mask'].astype(bool)&np.isfinite(d)&(u>=box[0]*w/1280)&(u<box[2]*w/1280)&(v>=box[1]*h/960)&(v<box[3]*h/960)
 q=np.stack([(u-K[0,2])*d/K[0,0],(v-K[1,2])*d/K[1,1],d],-1)[ok][::step];return q@T[:3,:3].T+T[:3,3]
def fit(i,box,label):
 q=points(i,box);c=np.median(q,axis=0);_,_,vv=np.linalg.svd(q-c,full_matrices=False);normal=vv[-1];res=(q-c)@normal
 r=dict(frame=i,pixel_region=box,label=label,n=len(q),centre=c.tolist(),normal=normal.tolist(),plane_offset=float(-c@normal),rms_m=float(np.sqrt(np.mean(res**2))),quantiles_xyz=np.quantile(q,[.05,.5,.95],axis=0).tolist());records.append(r);print(label,i,'center',c.round(3),'normal',normal.round(4),'rms',round(r['rms_m'],4),'q05/95',np.quantile(q,[.05,.95],axis=0).round(3))
for args in [(33,[1010,725,1180,800],'floor'),(33,[20,760,180,940],'floor'),(61,[250,490,450,570],'floor'),(82,[20,690,350,830],'floor'),(108,[420,575,980,610],'floor'),(33,[470,295,550,420],'far_wall'),(33,[1070,210,1220,340],'mirror_wall'),(61,[400,150,1100,290],'mirror_wall'),(82,[580,280,770,400],'mirror_wall'),(108,[425,350,610,500],'glazing'),(108,[920,350,1030,500],'glazing'),(33,[460,20,680,110],'ceiling'),(82,[850,60,1100,180],'ceiling')]:fit(*args)
for i in [0,33,61,74,82,91,100,108,118,129,155,179]: print('camera',i,np.array(P['frames'][i]['camera_to_world'])[:3,3].round(3))
(R/'analysis/measurements_preliminary.json').write_text(json.dumps(records,indent=2))
