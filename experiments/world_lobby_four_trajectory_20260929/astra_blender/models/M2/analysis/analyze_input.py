import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
P=Path('/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2'); O=Path('/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2'); J=json.load(open(P/'packet.json'))
R=np.array([[1,0,0],[0,0,1],[0,-1,0.]])
def points(i,step=4):
 a=np.load(P/f'geometry/{i:04d}.npz');z=a['depth_z_m'];h,w=z.shape;v,u=np.mgrid[:h:step,:w:step];uv=np.stack([u,v,np.ones_like(u)],-1);x=(uv@np.linalg.inv(a['intrinsics']).T)*z[::step,::step,None];C=np.array(J['frames'][i]['camera_to_world']);x=(x@C[:3,:3].T+C[:3,3])@R.T; c=np.array(Image.open(P/f'rgb/{i:04d}.png').resize((w,h)))[::step,::step];return x,c,a
stats=[]
for i in range(180):
 a=np.load(P/f'geometry/{i:04d}.npz');stats.append({'sample_index':i,'depth_quantiles':np.percentile(a['depth_z_m'],[10,50,90]).tolist()})
print('depth medians',[(i,round(s['depth_quantiles'][1],2)) for i,s in enumerate(stats)])
# Floor patches selected by direct RGB inspection, normalized 1280x960 pixels
patches={0:[(550,850,1150,940)],45:[(350,770,880,950)],60:[(30,560,380,720)],90:[(300,600,850,940)],110:[(600,530,1220,920)],135:[(350,650,750,940)],150:[(380,720,700,930)],179:[(300,700,600,920)]}
measure={}
for i,boxes in patches.items():
 x,c,a=points(i,1);h,w=x.shape[:2];pts=[]
 for u0,v0,u1,v1 in boxes:pts.extend(x[int(v0*h/960):int(v1*h/960),int(u0*w/1280):int(u1*w/1280)].reshape(-1,3))
 pts=np.array(pts);pts=pts[::4];cen=np.median(pts,0);_,_,vt=np.linalg.svd(pts-cen);n=vt[-1];n*=np.sign(n[2]);d=np.median(pts@n);dist=abs(pts@n-d);measure[i]={'normal':n.tolist(),'offset':float(d),'median_distance':float(np.median(dist)),'point_median':cen.tolist()};print(i,measure[i])
json.dump({'stats':stats,'floor_patches':measure},open(O/'analysis/depth_diagnostics.json','w'),indent=2)
allx=[];allc=[]
for i in list(range(0,150,3)):
 x,c,_=points(i,5);allx.append(x.reshape(-1,3));allc.append(c.reshape(-1,3))
x=np.concatenate(allx);c=np.concatenate(allc);np.savez_compressed(O/'analysis/sampled_measurement_points.npz',points=x,colors=c)
for name,axis,bound in [('top',[0,1],[-7,8,-5,20]),('side',[1,2],[-5,20,-4,5])]:
 im=Image.new('RGB',(900,1300),'#252525');draw=ImageDraw.Draw(im)
 # show furniture height roughly native floor -2.4
 keep=(x[:,2]>-2.7)&(x[:,2]<-0.8) if name=='top' else np.ones(len(x),bool)
 xx=x[keep];cc=c[keep]
 for pp,co in zip(xx,cc):
  u=int((pp[axis[0]]-bound[0])/(bound[1]-bound[0])*900);v=int(1300-(pp[axis[1]]-bound[2])/(bound[3]-bound[2])*1300)
  if 0<=u<900 and 0<=v<1300:draw.point((u,v),fill=tuple(co))
 for k in range(int(bound[0]),int(bound[1])+1):
  u=int((k-bound[0])/(bound[1]-bound[0])*900);draw.line((u,0,u,1300),fill='#555555');draw.text((u+2,10),str(k))
 for k in range(int(bound[2]),int(bound[3])+1):
  v=int(1300-(k-bound[2])/(bound[3]-bound[2])*1300);draw.line((0,v,900,v),fill='#555555');draw.text((1,v+1),str(k))
 im.save(O/f'analysis/{name}_measurements.png')
