import json,numpy as np,hashlib,datetime
from pathlib import Path
B=Path(__file__).resolve().parent;p=json.load(open(B.parents[3]/'data/packets/M4/packet.json'))
def ray(i,uv,axis,value):
 a=np.load(p['frames'][i]['geometry']);K=a['intrinsics'].copy();K[0]*=780/a['depth_z_m'].shape[1];K[1]*=585/a['depth_z_m'].shape[0];T=a['camera_to_world'];r=T[:3,:3]@np.linalg.inv(K)@np.array([*uv,1]);return T[:3,3]+r*((value-T[axis,3])/r[axis])
lamps=[]
for k,(u,v,r) in enumerate([(233,12,63),(280,73,43),(274,111,34),(350,116,30),(331,157,20),(375,141,23),(388,164,18),(412,149,22),(458,162,20),(488,135,31),(442,124,48),(429,100,42),(477,77,59),(694,57,100)]):
 z=4.48 if k%3 else 4.63;q=ray(0,(u,v),2,z);q2=ray(0,(u+r,v),2,z);rad=np.linalg.norm(q2[:2]-q[:2]);lamps.append({'id':f'pendant_{k:02d}','center':q.tolist(),'radius':min(1.15,max(.45,rad)),'evidence':[0,126,138]})
print('LAMPS',[(np.round(x['center'],2).tolist(),round(x['radius'],2)) for x in lamps]);print('column',ray(0,(170,250),1,25.2));print('frontwall',ray(90,(350,257),2,.03))
# Add front-half ceiling bowls beyond view 0, observed in reverse frame 90.
for k,(u,v,r) in enumerate([(243,120,34),(318,109,36),(366,118,28),(401,112,24),(438,103,26)]):
 q=ray(90,(u,v),2,4.48);q2=ray(90,(u+r,v),2,4.48);rad=np.linalg.norm(q2[:2]-q[:2]);
 if all(np.linalg.norm(q[:2]-np.array(x['center'])[:2])>1 for x in lamps):lamps.append({'id':f'pendant_front_{k:02d}','center':q.tolist(),'radius':min(1.1,max(.5,rad)),'evidence':[90]})
json.dump({'lamps':lamps,'room':{'xmin':9.0,'xmax':26.8,'ymin':15.55,'ymax':25.8,'wall_south_near_y':18.1,'wall_return_x':18.55,'floor_z':.025,'ceiling_z':5.0},'measurement_rule':'No depth rescaling. Local close depth and RGB triangulation reconciliation; geometric uncertainty explicitly retained.'},open(B/'layout_parameters.json','w'),indent=2)
Path(B/'packet_frozen.json').write_text(json.dumps(p,indent=2));meta={'packet_sha256':hashlib.sha256((B.parents[3]/'data/packets/M4/packet.json').read_bytes()).hexdigest(),'status':p['status'],'frames':len(p['frames']),'geometry_frames':p['geometry_frames'],'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};json.dump(meta,open(B/'input_freeze.json','w'),indent=2)
