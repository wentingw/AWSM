import json,numpy as np
from pathlib import Path
B=Path(__file__).resolve().parent;cams={x['frame_id']:x for x in json.load(open(B/'cameras.json'))['cameras']}
def P(i):
 c=cams[i];K=np.array(c['K']);K[0]*=780/c['image_size'][0];K[1]*=585/c['image_size'][1];return K@np.linalg.inv(np.array(c['camera_to_world']))[:3]
qs=[('pendant_13',[(0,694,57),(60,376,110)]),('pendant_12',[(0,477,77),(60,202,78)]),('pendant_10',[(0,442,124),(60,43,112)]),('pendant_11',[(0,429,100),(60,6,61)]),('pendant_07',[(0,412,149),(108,447,57)]),('pendant_04',[(0,331,157),(108,646,133)]),('pendant_06',[(0,388,164),(108,755,119)]),('pendant_reverse_6',[(90,480,19),(108,239,78)])]
out=[];L=json.load(open(B/'layout_parameters_v2.json'))
for name,ms in qs:
 A=np.array([v*P(i)[2]-P(i)[k] for i,u,vv in ms for k,v in [(0,u),(1,vv)]]);_,_,V=np.linalg.svd(A);X=V[-1]/V[-1,3];err=[]
 for i,u,v in ms:q=P(i)@X;err.append(float(np.linalg.norm(q[:2]/q[2]-[u,v])))
 accept=bool(max(err)<2.5 and 3<X[2]<5)
 out.append({'object_id':name,'measurements_frame_u_v_780':ms,'point_world':X[:3].tolist(),'reprojection_errors_px':err,'accepted':accept,'threshold_px':2.5});print(name,X[:3].round(3),np.round(err,2),accept)
 if accept:
  m=next(x for x in L['lamps'] if x['id']==name);old=np.array(m['center']);cam=np.array(cams[ms[0][0]]['camera_to_world'])[:3,3];m['radius']*=float(np.linalg.norm(X[:3]-cam)/np.linalg.norm(old-cam));m['center']=X[:3].tolist();m['provenance']='revision3 explicitly accepted two-view RGB centre match; residual below2.5px at780px; depth conflict retained';m['evidence']=list(sorted(set(m['evidence']+[i for i,u,v in ms])))
json.dump(out,open(B/'revision3_pendant_matches.json','w'),indent=2);json.dump(L,open(B/'layout_parameters.json','w'),indent=2)
