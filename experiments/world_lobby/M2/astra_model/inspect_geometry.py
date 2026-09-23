import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
O=Path(__file__).parent; p=json.load(open(O.parents[3]/'data/packets/M2/packet.json'));T=np.array(json.load(open(O/'geometry_analysis.json'))['T_input_model'])
def point(frame,u,v):
 a=np.load(p['frames'][frame]['geometry']);D=a['depth_z_m'];K=a['intrinsics'];C=T@a['camera_to_world'];d=float(np.median(D[max(0,v-2):v+3,max(0,u-2):u+3]));q=np.array([(u-K[0,2])*d/K[0,0],(v-K[1,2])*d/K[1,1],d]);return C[:3,:3]@q+C[:3,3]
queries={0:{'floor_near_right':(1210,850),'floor_far_right':(960,510),'rug_frontleft':(385,710),'rug_backleft':(455,524),'rug_backright':(794,565),'planter_L_frontlow':(530,540),'planter_R_frontlow':(730,547),'chair_near_top':(445,621),'chair_backL_top':(490,542),'chair_backR_top':(698,541),'table_center':(570,605),'front_table':(690,890),'front_chair_top':(943,833),'wall_far_low':(890,460),'wall_far_up':(510,260),'wall_right':(1160,380),'ceiling_back':(670,234),'ceiling_front':(550,30),'column_mid':(280,260),'column_foot':(280,540),'window_lower':(120,650),'floor_center':(680,700),'floor_far':(890,530)}}
for f,ps in queries.items():
 print('FRAME',f)
 for name,uv in ps.items():print(name,uv,np.round(point(f,*uv),3))
a=np.load(O/'measurements_model.npz');P=a['points'];C=a['colors'];im=Image.new('RGB',(1400,1100),(235,235,235));dr=ImageDraw.Draw(im)
# ortho topdown x -7..8 y -3..18; scale45
for zlo,zhi,label,dx in [(-.3,.3,'floor',0),(.3,2.,'furniture',700)]:
 mask=(P[:,2]>zlo)&(P[:,2]<zhi);q=P[mask][::2];cc=C[mask][::2];ix=((q[:,0]+7)*42+dx).astype(int);iy=((18-q[:,1])*42).astype(int)
 for x,y,c in zip(ix,iy,cc):
  if dx<=x<dx+690 and 0<=y<1000:dr.point((int(x),int(y)),fill=tuple(c))
 for x in range(-7,9):dr.line((dx+(x+7)*42,0,dx+(x+7)*42,882),fill=(180,180,180));dr.text((dx+(x+7)*42,900),str(x),fill='black')
 for y in range(-3,19):dr.line((dx, (18-y)*42,dx+630,(18-y)*42),fill=(180,180,180));dr.text((dx+640,(18-y)*42),str(y),fill='black')
 dr.text((dx+200,950),label,fill='black')
im.save(O/'topdown.jpg')
