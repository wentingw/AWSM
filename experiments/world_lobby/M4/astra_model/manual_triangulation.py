import numpy as np,json
from pathlib import Path
B=Path(__file__).resolve().parent;p=json.load(open(B.parents[3]/'data/packets/M4/packet.json'))
pts={'far_bowl':((346,358),(254,323)),'far_left_chair_seat':((270,369),(176,332)),'planter_left_face':((324,325),(290,288)),'planter_right_face':((443,326),(405,294)),'reception_front_center':((389,274),(411,236)),'shield_bottom':((390,233),(420,198)),'shield_top':((390,204),(420,164)),'mirror_pot':((656,381),(571,369)),'ceiling_far_corner':((602,128),(607,88)),'glass_floor_rear_corner':((275,279),(306,249))}
pts.update({'lamp_left_near':((233,12),(218,27)),'lamp_left_mid':((280,73),(241,68)),'lamp_left_back':((274,111),(285,86)),'lamp_back_left_low':((331,157),(351,117)),'lamp_back_center_low':((388,164),(399,124)),'lamp_back_right_low':((458,162),(482,118)),'lamp_right_mid':((477,77),(411,41)),'lamp_right_front':((694,57),(557,1))})
cam=[]
for i in [0,138]:
 a=np.load(p['frames'][i]['geometry']);K=a['intrinsics'].copy();K[0]*=780/a['depth_z_m'].shape[1];K[1]*=585/a['depth_z_m'].shape[0];T=a['camera_to_world'];cam.append(K@np.linalg.inv(T)[:3])
out={}
for name,(a,b) in pts.items():
 P,Q=cam;M=np.array([a[0]*P[2]-P[0],a[1]*P[2]-P[1],b[0]*Q[2]-Q[0],b[1]*Q[2]-Q[1]]);_,_,V=np.linalg.svd(M);X=V[-1]/V[-1,3];re=[]
 for R,uv in zip(cam,[a,b]):
  x=R@X;re.append(float(np.linalg.norm(x[:2]/x[2]-uv)))
 print(name,X[:3].round(3),np.round(re,2));out[name]={'world_point':X[:3].tolist(),'reprojection_error_pixels_780':re,'frame_ids':[0,138],'uv_780x585':[a,b]}
json.dump(out,open(B/'manual_rgb_measurements.json','w'),indent=2)
