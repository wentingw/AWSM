import json,numpy as np
from pathlib import Path
B=Path(__file__).resolve().parent;p=json.load(open(B/'packet_frozen.json'));L=json.load(open(B/'layout_parameters.json'))
def ray(i,u,v,ww=780,hh=585):
 a=np.load(p['frames'][i]['geometry']);K=a['intrinsics'].copy();K[0]*=ww/a['depth_z_m'].shape[1];K[1]*=hh/a['depth_z_m'].shape[0];T=a['camera_to_world'];return T[:3,3],T[:3,:3]@np.linalg.inv(K)@np.array([u,v,1])
def depthpt(i,u,v):
 a=np.load(p['frames'][i]['geometry']);x=int(u/780*a['depth_z_m'].shape[1]);y=int(v/585*a['depth_z_m'].shape[0]);d=float(np.median(a['depth_z_m'][max(0,y-2):y+3,max(0,x-2):x+3]));o,r=ray(i,u,v);return o+r*d
L['lamps']=[]
for k,(u,v,r) in enumerate([(233,12,63),(280,73,43),(274,111,34),(350,116,30),(331,157,20),(375,141,23),(388,164,18),(412,149,22),(458,162,20),(488,135,31),(442,124,48),(429,100,42),(477,77,59),(694,57,100)]):
 q=depthpt(0,u,v);o,rv=ray(0,u+r,v);q2=o+rv*((q[2]-o[2])/rv[2]);rad=np.linalg.norm(q2[:2]-q[:2]);L['lamps'].append({'id':f'pendant_{k:02d}','center':q.tolist(),'radius':max(.45,min(1.05,rad)),'evidence':[0,126,138],'provenance':'input depth anchor with RGB silhouette radius; weak multiview suspension height'})
for k,(u,v,r) in enumerate([(243,120,34),(318,109,36),(366,118,28),(401,112,24),(438,103,26)]):
 q=depthpt(90,u,v);o,rv=ray(90,u+r,v);q2=o+rv*((q[2]-o[2])/rv[2]);rad=np.linalg.norm(q2[:2]-q[:2]);
 if all(np.linalg.norm(q[:2]-np.array(x['center'])[:2])>1.0 for x in L['lamps']):L['lamps'].append({'id':f'pendant_front_{k:02d}','center':q.tolist(),'radius':max(.45,min(1.05,rad)),'evidence':[90],'provenance':'input depth anchor with RGB silhouette radius'})
L['mirrors']=[]
for k,(u,v,rr) in enumerate([(432,192,55),(535,225,53),(598,168,39),(562,125,30),(352,160,30),(336,210,19),(356,249,29),(470,257,16),(590,226,16),(512,163,26)]):
 o,r=ray(70,u,v,720,540);q=o+r*((18.13-o[1])/r[1]);o,r2=ray(70,u+rr,v,720,540);q2=o+r2*((18.13-o[1])/r2[1]);L['mirrors'].append({'center':q.tolist(),'radius':float(np.linalg.norm(q-q2)),'evidence':[60,70,80]})
json.dump(L,open(B/'layout_parameters.json','w'),indent=2);print(json.dumps({'lamps':L['lamps'],'mirrors':L['mirrors']},indent=2))
