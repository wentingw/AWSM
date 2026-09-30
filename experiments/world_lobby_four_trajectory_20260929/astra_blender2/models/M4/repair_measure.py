"""M4 revision measurements from allowed RGB hand picks, own DA3 and saved v1 residuals."""
import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4'
p=json.load(open(I/'packet.json'));L=json.load(open(R/'layout.json'))
def project(pt,i):
 T=np.array(p['frames'][i]['camera_to_world']);q=T[:3,:3].T@(np.array(pt)-T[:3,3]);v=np.array(p['frames'][i]['intrinsics'])@q;return v[:2]/v[2],q[2]
def ray(i,u,v):
 T=np.array(p['frames'][i]['camera_to_world']);d=T[:3,:3]@np.linalg.solve(np.array(p['frames'][i]['intrinsics']),[u,v,1]);return T[:3,3],d/np.linalg.norm(d)
def triang(obs):
 od=[ray(*v) for v in obs];ms=[np.eye(3)-np.outer(d,d) for o,d in od];pt=np.linalg.solve(sum(ms),sum(m@o for m,(o,d) in zip(ms,od)));return pt,[float(np.linalg.norm(project(pt,i)[0]-[u,v])) for i,u,v in obs]
def plane(i,u,v,z):
 o,d=ray(i,u,v);return o+d*(z-o[2])/d[2]
def residual(i,u,v,r=10):
 n=np.load(R/f'checks/v1/{i:04d}_errors.npz');a=n['signed_z_residual_m'][max(0,int(v/2-r)):min(480,int(v/2+r)),max(0,int(u/2-r)):min(640,int(u/2+r))];return dict(rect_640=[max(0,int(u/2-r)),max(0,int(v/2-r)),min(640,int(u/2+r)),min(480,int(v/2+r))],median_signed_m=float(np.nanmedian(a)),mae_m=float(np.nanmean(abs(a))))
def own_depth(i,u,v):
 n=np.load(p['frames'][i]['geometry']);K=np.array(n['intrinsics']);Krgb=np.array(p['frames'][i]['intrinsics']);q=K@np.linalg.solve(Krgb,[u,v,1]);x,y=np.round(q[:2]).astype(int);d=n['depth_z_m'];z=float(np.median(d[max(0,y-1):y+2,max(0,x-1):x+2]));q=np.linalg.solve(K,[x,y,1])*z;T=np.array(p['frames'][i]['camera_to_world']);return (T[:3,:3]@q+T[:3,3]).tolist()
if __name__=='__main__':
 for i in [61,82,91,100,108,129]:
  im=Image.open(p['frames'][i]['rgb']).convert('RGB');dr=ImageDraw.Draw(im)
  for d in L['pendants']:
   uv,z=project(d['center'],i)
   if z>0 and 0<uv[0]<1280 and 0<uv[1]<960:
    x,y=uv;dr.ellipse((x-7,y-7,x+7,y+7),outline='red',width=3);dr.text((x+8,y),d['id'][-2:],fill='red',stroke_width=1)
  im.save(R/f'analysis/pendant_projection_v1_{i}.jpg')
 for i,pts in {129:[(325,820),(414,768),(510,754),(633,755),(650,790),(738,840),(480,859)],61:[(762,695),(901,728),(1033,786),(824,856)]}.items():
  for u,v in pts:print('PLANE',i,u,v,np.round(plane(i,u,v,.52),3),'DA3',np.round(own_depth(i,u,v),3))
