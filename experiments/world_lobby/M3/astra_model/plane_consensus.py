import json,hashlib
import numpy as np
from pathlib import Path
OUT=Path(__file__).parent;ROOT=OUT.parents[3];p=json.load(open(ROOT/'data/packets/M3/packet.json'));reports=[]
ids=[5,45,60,75,90,105,120,126,135,150]
for fid in ids:
 f=p['frames'][fid];b=np.load(f['geometry']);d=b['depth_z_m'];K=b['intrinsics'];T=b['camera_to_world'];h,w=d.shape;yy,xx=np.mgrid[:h,:w];r=np.stack([(xx-K[0,2])/K[0,0],(yy-K[1,2])/K[1,1],np.ones_like(xx)],-1);X=(r*d[...,None])@T[:3,:3].T+T[:3,3];dx=X[1:-1,2:]-X[1:-1,:-2];dy=X[2:,1:-1]-X[:-2,1:-1];n=np.cross(dx,dy);n=n/(np.linalg.norm(n,axis=-1,keepdims=True)+1e-12);V=X[1:-1,1:-1];valid=b['valid_mask'][1:-1,1:-1].astype(bool)&np.isfinite(V).all(-1);rpt={'frame':fid,'planes':{}}
 for name,axis,side in [('floor',2,-1),('ceiling',2,1),('window_wall',1,-1),('mirror_wall',1,1),('end_wall',0,-1),('entry_wall',0,1)]:
  ok=valid&(abs(n[...,axis])>.985)&((V[...,axis]-T[axis,3])*side>.7);a=V[ok,axis];
  if not len(a):continue
  hist,edges=np.histogram(a,bins=np.arange(-50,30,.15));peak=np.argmax(hist);center=(edges[peak]+edges[peak+1])/2;near=a[abs(a-center)<.3];rpt['planes'][name]={'median':float(np.median(near)),'n':len(near),'all_n':len(a),'q10_q90':np.quantile(near,[.1,.9]).tolist()}
 reports.append(rpt)
json.dump({'frames':reports,'method':'Depth finite-difference normals aligned to native axes within 9.94 degrees; strongest 15cm plane mode in requested halfspace; +-30cm inliers. Ten time-spaced views have equal weight, stationary frames are not overcounted.','sources':[{'frame':i,'path':p['frames'][i]['geometry'],'sha256':p['frames'][i]['geometry_sha256']} for i in ids]},open(OUT/'plane_consensus.json','w'),indent=2)
for r in reports:print(r['frame'],{k:round(v['median'],3) for k,v in r['planes'].items()})
