import json,numpy as np,cv2
from pathlib import Path
from PIL import Image,ImageDraw
OUT=Path(__file__).parent;ROOT=OUT.parents[3]
p=json.load(open(ROOT/'data/packets/M3/packet.json'));frames={f['keyframe_index']:f for f in p['frames']}
a=json.load(open(OUT/'annotations.json'));q=np.load(OUT/'rgb_pose_triangulation.npz');X=q['xyz'];rgb=q['rgb'];K=np.array([[762.8,0,640],[0,762.8,480],[0,0,1.]])
# Re-mark initial image against directly inspected frame 5 which has a pose.
boxes={'reception':[.456,.426,.577,.474],'planter_center_left':[.387,.505,.496,.571],'planter_center_right':[.542,.507,.649,.577],'table_middle':[.417,.601,.515,.668],'seat_middle_left_front':[.328,.574,.413,.683],'seat_middle_left_back':[.391,.529,.436,.591],'seat_middle_center':[.429,.539,.514,.598],'seat_middle_right_front':[.478,.560,.536,.622],'seat_middle_right_back':[.537,.533,.590,.625],'planter_window_mid':[.182,.584,.283,.645],'planter_mirror':[.844,.611,.917,.705],'planter_back_left':[.419,.421,.441,.46],'planter_back_right':[.599,.423,.619,.456],'planter_back_corner':[.706,.444,.747,.467]}
for o in a['objects']:
 for ob in o['observations']:
  if ob['frame']==0:ob['frame']=5;ob['box']=boxes[o['id']]
for r in a['planar_regions']:
 if r['frame']==0:r['frame']=5
json.dump(a,open(OUT/'annotations.json','w'),indent=2)
def project(f):
 T=np.array(frames[f]['camera_to_world']);v=np.c_[X,np.ones(len(X))]@np.linalg.inv(T).T;uv=v[:,:3]@K.T;return uv[:,:2]/uv[:,2:]/np.array([1280,960]),v[:,2]
report=[]
for o in a['objects']:
 obs=[]
 for ob in o['observations']:
  uv,z=project(ob['frame']);x0,y0,x1,y1=ob['box'];ok=(uv[:,0]>x0)&(uv[:,0]<x1)&(uv[:,1]>y0)&(uv[:,1]<y1)&(z>0);xx=X[ok];zz=z[ok]
  obs.append({'frame':ob['frame'],'n':len(xx),'xyz_quantiles':np.quantile(xx,[.1,.5,.9],axis=0).tolist() if len(xx) else None,'depth_quantiles':np.quantile(zz,[.1,.5,.9]).tolist() if len(xx) else None})
 report.append({'id':o['id'],'observations':obs})
json.dump(report,open(OUT/'rgb_semantic_measurements.json','w'),indent=2)
for axis in range(3):
 h,e=np.histogram(X[:,axis],bins=np.arange(-35,15,.15));peaks=np.argsort(h)[-12:];print('axis',axis,sorted([(round(float((e[k]+e[k+1])/2),2),int(h[k])) for k in peaks]))
im=Image.new('RGB',(1100,700),'white');d=ImageDraw.Draw(im)
for xyz,c in zip(X,rgb):
 xx=int((xyz[0]+32)*30);yy=int((xyz[1]+10)*30)
 if 0<=xx<1100 and 0<=yy<700:d.ellipse((xx-1,yy-1,xx+1,yy+1),fill=tuple(c.astype(int)))
for f in frames.values():
 if 'camera_to_world' in f:
  t=np.array(f['camera_to_world'])[:3,3];xx=int((t[0]+32)*30);yy=int((t[1]+10)*30);d.ellipse((xx-2,yy-2,xx+2,yy+2),fill='red')
for x in range(-30,5,5):d.text(((x+32)*30,5),str(x),fill='blue')
for y in range(-10,12,2):d.text((5,(y+10)*30),str(y),fill='blue')
im.save(OUT/'triangulated_topdown.jpg')
print(json.dumps(report,indent=1))
