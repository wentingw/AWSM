import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
INPUT=ROOT.parent.parent/'inputs/M4'
p=json.load(open(INPUT/'packet.json'))
# Hand identified original-RGB regions. All coordinates at 1280 x 960.
patches={33:{'end_wall':(560,285,940,340),'floor':(840,650,920,760),'ceiling':(500,20,680,110),'right_wall':(1070,200,1190,360),'column':(260,250,310,480)},61:{'mirror_wall':(460,160,780,300),'floor':(280,570,400,625),'ceiling':(600,10,740,50)},74:{'mirror_wall':(410,40,650,280),'floor':(330,650,470,700)},82:{'end_return':(30,220,330,400),'mirror_wall':(530,290,650,420),'ceiling':(860,30,1110,140)},91:{'far_wall':(440,130,690,250),'floor':(70,480,210,630)},100:{'glazing':(620,340,740,470),'floor':(610,855,900,925)},108:{'glazing':(920,350,1000,490),'floor':(1100,895,1250,940)},118:{'end_wall':(1080,40,1240,230)},129:{'end_wall':(950,315,1230,375),'ceiling':(710,15,860,90)},155:{'end_wall':(580,285,920,320),'floor':(860,600,930,710)}}
points={33:{'endwall_floor':(920,468),'column_foot':(293,632),'bowlplanter':(258,615),'planterA':(529,548),'planterB':(715,540),'desk':(620,459),'treeA':(507,448),'treeB':(737,450),'floorlamp':(830,452),'tableA':(575,618),'seatA1':(445,630),'seatA2':(540,575),'seatA3':(619,585),'seatA4':(689,573),'mirrorpot':(1090,640),'carpet_left':(283,790),'carpet_right':(879,720)},61:{'mirror_pot':(518,561),'silverdoor':(413,459),'tableB':(824,856),'seatB1':(761,720),'seatB2':(887,754),'seatB3':(1032,790),'plant_tall':(1250,706),'mirror_center':(739,420)},74:{'silverdoor':(470,499),'mirrorpot':(691,576),'mirror_center':(856,381),'seatA_edge':(576,889)},82:{'mirrorcorner':(510,600),'opening_right':(944,528),'plant_tall':(1049,559),'planterA':(655,771),'planterB':(1008,917),'lamp':(397,574)},91:{'planterA':(704,481),'planterB':(437,488),'bowlplanter':(835,431),'farwall_floor':(648,344),'columnfoot':(894,475),'seatB':(477,353)},100:{'door_center':(909,424),'columnfoot':(495,489),'planterA':(419,537),'planterB':(208,587)},108:{'door_bottom_left':(708,555),'door_bottom_right':(854,551),'door_top_left':(708,321),'columnfoot':(329,514),'desk':(1190,600),'tree':(1176,512)},118:{'door_bottom_left':(651,579),'door_bottom_right':(793,548),'columnfoot':(187,772),'desk':(1192,584)},129:{'desk':(951,587),'treeA':(819,554),'treeB':(1132,579),'planterA':(635,701),'planterB':(933,766),'tableA':(478,859),'seatA1':(337,839),'seatA2':(501,781),'seatA3':(635,831),'seatA4':(713,845),'columnfoot':(391,726)}}
cache={}
def data(i):
 if i not in cache:
  n=np.load(p['frames'][i]['geometry']);d=n['depth_z_m'];k=n['intrinsics'];t=np.array(p['frames'][i]['camera_to_world']); y,x=np.indices(d.shape);q=np.stack([(x-k[0,2])/k[0,0],(y-k[1,2])/k[1,1],np.ones_like(x)],-1)*d[...,None];w=q@t[:3,:3].T+t[:3,3];cache[i]=(d,k,t,w,n['valid_mask'])
 return cache[i]
records=[]
for i,ps in patches.items():
 d,k,t,w,valid=data(i)
 for name,rect in ps.items():
  x0,y0,x1,y1=np.array(rect)*392/1280;x0,x1=int(x0),int(x1);y0,y1=int(y0),int(y1);pts=w[y0:y1,x0:x1][valid[y0:y1,x0:x1]];c=np.median(pts,axis=0);_,_,v=np.linalg.svd(pts-c,full_matrices=False);n=v[-1];res=(pts-c)@n
  record=dict(sample_index=i,label=name,pixel_region=list(rect),point_count=len(pts),centroid=c.tolist(),normal=n.tolist(),plane_offset=-float(n@c),rms_m=float(np.sqrt(np.mean(res**2))),axis_spread_m=np.std(pts,axis=0).tolist());records.append(record)
  print(i,name,'c',np.round(c,3),'n',np.round(n,3),'rms',round(record['rms_m'],3))
anchors=[]
for i,ps in points.items():
 d,k,t,w,valid=data(i)
 for name,uv in ps.items():
  x,y=np.round(np.array(uv)*392/1280).astype(int);pt=np.median(w[y-1:y+2,x-1:x+2].reshape(-1,3),axis=0);anchors.append(dict(sample_index=i,label=name,pixel_uv=list(uv),world_point=pt.tolist(),optical_z_m=float(d[y,x]),method='3x3 NPZ depth median backprojection; NPZ K and packet c2w'))
  print(i,name,np.round(pt,3))
json.dump(dict(method='DA3 prediction backprojection; robust spatial median and SVD local plane; no GT depth',coordinate_frame='native_input',patch_planes=records,point_anchors=anchors,limitations=['DA3 is not truth','Reflected and glazed pixels may predict virtual or biased depth','Plane estimates are local and contain prediction distortion']),open(ROOT/'analysis/measurements.json','w'),indent=2)
