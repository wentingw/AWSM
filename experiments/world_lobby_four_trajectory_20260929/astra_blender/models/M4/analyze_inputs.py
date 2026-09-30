import json,numpy as np,hashlib,time
from pathlib import Path
from PIL import Image,ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parent;P=B.parents[3]/'data/packets/M4/packet.json';p=json.load(open(P));log=json.load(open(B/'input_access_log.json'))
def access(path,purpose,i=None):
 log['accessed'].append({'path':str(path),'purpose':purpose,'frame_id':i,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()})
ids=[0,60,90,108,126,138]
sheet=Image.new('RGB',(1560,1800),'#202020');draw=ImageDraw.Draw(sheet)
for n,i in enumerate(ids):
 f=p['frames'][i];access(f['rgb'],'detailed visual inspection',i);im=Image.open(f['rgb']).convert('RGB');print('RGB',i,im.size);im=im.resize((780,585));sheet.paste(im,((n%2)*780,(n//2)*600));draw.text(((n%2)*780+10,(n//2)*600+10),str(i),fill='yellow',stroke_width=3,stroke_fill='black')
sheet.save(B/'detailed_inputs.jpg')
ps=[];cs=[];cam=[];norm=[]
for f in p['frames']:
 if 'geometry' not in f:continue
 access(f['geometry'],'metric geometry analysis',f['keyframe_index']);a=np.load(f['geometry']);D=a['depth_z_m'];K=a['intrinsics'];T=a['camera_to_world'];h,w=D.shape;y,x=np.mgrid[0:h:8,0:w:8];d=D[::8,::8];q=np.stack([(x-K[0,2])*d/K[0,0],(y-K[1,2])*d/K[1,1],d],-1);world=q@T[:3,:3].T+T[:3,3];mask=np.isfinite(d)&(d>.1)&(d<40)&a['valid_mask'][::8,::8].astype(bool);ps.append(world[mask]);access(f['rgb'],'point measurement colors',f['keyframe_index']);im=np.asarray(Image.open(f['rgb']).resize((w,h)));cs.append(im[::8,::8][mask]);cam.append(T[:3,3]);
 camrec={'frame_id':f['keyframe_index'],'image_size':[w,h],'K':K.tolist(),'camera_to_world':T.tolist(),'timestamp_ns':f['timestamp_ns']}
 if f==next(x for x in p['frames'] if 'geometry' in x): cameras=[]
 cameras.append(camrec)
ps=np.concatenate(ps);cs=np.concatenate(cs);cam=np.asarray(cam);np.savez_compressed(B/'measurements.npz',points=ps,colors=cs,camera_centers=cam);json.dump({'cameras':cameras,'units':'m','model_world_up':[0,0,1],'T_input_model':np.eye(4).tolist(),'convention':'OpenCV optical RDF camera-to-world'},open(B/'cameras.json','w'),indent=2)
print('CAM',np.min(cam,0),np.max(cam,0));print('POINT quantiles',np.percentile(ps,[1,5,25,50,75,95,99],axis=0))
fig,ax=plt.subplots(1,3,figsize=(21,7))
for a,ij in zip(ax,[(0,1),(0,2),(1,2)]):
 a.scatter(ps[::2,ij[0]],ps[::2,ij[1]],s=.2,c=cs[::2]/255);a.plot(cam[:,ij[0]],cam[:,ij[1]],'r-',lw=1);a.set_aspect('equal');a.set_xlabel('xyz'[ij[0]]);a.set_ylabel('xyz'[ij[1]]);a.grid();a.set_xlim(np.percentile(ps[:,ij[0]],[1,99]));a.set_ylim(np.percentile(ps[:,ij[1]],[1,99]))
fig.savefig(B/'geometry_overview.png',dpi=150)
for k in range(3):
 hist,ed=np.histogram(ps[:,k],bins=np.arange(-10,45,.05));ix=np.argsort(hist)[-20:];print('PEAKS','xyz'[k],sorted([(round((ed[j]+ed[j+1])/2,3),int(hist[j])) for j in ix]))
json.dump(log,open(B/'input_access_log.json','w'),indent=2)
