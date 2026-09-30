import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.optimize import least_squares
R=Path(__file__).parent;P=json.loads((R.parent.parent/'inputs/M2/packet.json').read_text());L=json.loads((R/'layout.json').read_text());X=np.array(L['model_from_input']);F=P['frames'];results={}
def pose(i):return X@np.array(F[i]['camera_to_world'])
def proj(i,q):
 T=pose(i);q=(np.array(q)-T[:3,3])@T[:3,:3];return q[:2]/q[2]*762.8+[640,480]
def depth_point(i,uv):
 n=np.load(F[i]['geometry']);u,v=uv;d=n['depth_z_m'];K=n['intrinsics'];xx=int(u*d.shape[1]/1280);yy=int(v*d.shape[0]/960);z=float(np.median(d[max(0,yy-1):yy+2,max(0,xx-1):xx+2]));T=pose(i);return (T[:3,:3]@np.array([(u-640)*z/762.8,(v-480)*z/762.8,z])+T[:3,3]).tolist(),z
# Metadata for known full-input outliers versus adjacent frames; does not cast new rays.
n=np.load(R/'checks/input_v1/depth.npz');rows=[]
for i in [19,20,21,22,23,24,165,166,167,168,169,170,174,175,176]:
 d=np.load(F[i]['geometry']);T=pose(i);Tm=pose(max(0,i-1));ref=n['reference_z_m'][i];pred=n['prediction_z_m'][i];valid=np.isfinite(pred)&np.isfinite(ref)&(ref>=.1)&(ref<=30)
 rows.append({'sample_index':i,'selected_window':F[i].get('selected_window'),'window_local_index':F[i].get('window_local_index'),'camera_position_model':T[:3,3].tolist(),'pose_translation_step_m':float(np.linalg.norm(T[:3,3]-Tm[:3,3])),'rotation_step_deg':float(np.degrees(np.arccos(np.clip((np.trace(T[:3,:3].T@Tm[:3,:3])-1)/2,-1,1)))),'DA3_Z_quantiles':np.nanpercentile(d['depth_z_m'],[10,50,90]).tolist(),'existing_BVH_Z_quantiles':np.nanpercentile(pred,[10,50,90]).tolist(),'existing_residual_median':float(np.median((pred-ref)[valid]))})
results['input_outliers']=rows
for i in [33,61,74,82,100,108,118,129]:
 im=Image.open(F[i]['rgb']).convert('RGB');dr=ImageDraw.Draw(im)
 for li in L['lights']:
  uv=proj(i,li['center']);
  if np.isfinite(uv).all() and -100<uv[0]<1380 and -100<uv[1]<1060:
   u,v=uv;dr.ellipse((u-8,v-8,u+8,v+8),outline='red',width=3);dr.text((u+9,v),li['id'].replace('pendant_',''),fill='red',stroke_width=1,stroke_fill='white')
 for name,q in [('desk',L['reception']['center']),('recess_corner',[3.78,8,2.2])]:
  u,v=proj(i,q);dr.text((u,v),name,fill='blue',stroke_width=1,stroke_fill='white')
 im.save(R/f'analysis/repair_projected_labels_{i:04d}.jpg')
results['overlay_note']='Labels project existing semantic centers on source RGB for correspondence inspection; no Blender render or new depth cast.'
(R/'analysis/repair_measurements_pre.json').write_text(json.dumps(results,indent=2));print(json.dumps(rows,indent=2))
