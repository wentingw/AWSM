import json,numpy as np
from pathlib import Path
B=Path(__file__).resolve().parent;p=json.load(open(B.parents[3]/'data/packets/M4/packet.json'));out=[]
# Pixel coordinates on 780 by 585 displayed RGB. Named locations selected by Astra visual inspection.
probes={0:{'wall_rear':[(295,155),(430,185),(520,195)],'wall_right':[(665,150),(740,380),(607,206)],'ceiling':[(345,40),(515,20),(450,82)],'floor_stone':[(580,455),(190,413),(555,360)],'floor_dark':[(350,455),(414,380)],'planter_rear':[(304,318),(420,320)],'sofa_group_far':[(260,360),(303,333),(374,335),(410,350)],'sofa_group_near':[(555,495),(610,552)],'table_far':[(330,354)],'reception':[(375,267)],'column':[(167,180)],'window':[(210,190)]},60:{'mirror_wall':[(455,179),(655,163),(741,289),(452,437)],'wall_returns':[(160,228),(243,257),(127,171)],'sofa_near':[(509,457),(594,461),(658,497)],'table_near':[(534,533)],'planter_middle':[(92,367),(167,353)],'pot':[(335,362)],'mirror_centers':[(430,259),(492,307),(585,338),(645,267),(582,220)]},90:{'front_wall':[(287,142),(388,174),(435,223)],'middle_planter':[(271,442),(426,460)],'near_sofas':[(345,376)],'column':[(652,348)],'window':[(517,180)]},108:{'glass_wall':[(600,141),(412,230),(202,300)],'door':[(470,409),(484,275)],'column':[(237,294)],'floor':[(473,501),(267,531)],'reception':[(732,423)],'ceiling':[(519,60)]},126:{'reception':[(631,398)],'rearwall':[(670,332),(608,242)],'column':[(256,310)],'ceiling':[(468,54)]}}
for i,regs in probes.items():
 a=np.load(p['frames'][i]['geometry']);D=a['depth_z_m'];K=a['intrinsics'];T=a['camera_to_world'];h,w=D.shape
 print('\nFRAME',i)
 for label,pixels in regs.items():
  vals=[]
  for u,v in pixels:
   x=int(u/780*w);y=int(v/585*h);d=float(np.median(D[max(0,y-2):y+3,max(0,x-2):x+3]));c=np.array([(x-K[0,2])*d/K[0,0],(y-K[1,2])*d/K[1,1],d]);vals.append((T[:3,:3]@c+T[:3,3]).round(3).tolist())
  print(label,vals);out.append({'frame_id':i,'label':label,'pixels_780x585':pixels,'world_points':vals})
json.dump(out,open(B/'semantic_measurements.json','w'),indent=2)
pts=[];ns=[]
for f in p['frames'][::3]:
 if 'geometry' not in f:continue
 a=np.load(f['geometry']);D=a['depth_z_m'];K=a['intrinsics'];T=a['camera_to_world'];y,x=np.mgrid[:D.shape[0],:D.shape[1]];q=np.stack([(x-K[0,2])*D/K[0,0],(y-K[1,2])*D/K[1,1],D],-1);n=np.cross(q[1:-1,2:]-q[1:-1,:-2],q[2:,1:-1]-q[:-2,1:-1]);n/=np.maximum(np.linalg.norm(n,axis=-1,keepdims=True),1e-9);P=q[1:-1,1:-1]@T[:3,:3].T+T[:3,3];N=n@T[:3,:3].T;pts.append(P[::8,::8].reshape(-1,3));ns.append(N[::8,::8].reshape(-1,3))
pts=np.concatenate(pts);ns=np.concatenate(ns)
for k in range(3):
 keep=np.abs(ns[:,k])>.97
 for limit in ([0,30],):
  hist,ed=np.histogram(pts[keep,k],bins=np.arange(-2,32,.05));ix=np.argsort(hist)[-15:];print('PLANE_PEAKS','xyz'[k],sorted([(round(float((ed[j]+ed[j+1])/2),3),int(hist[j])) for j in ix]))
