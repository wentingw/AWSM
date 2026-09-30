"""M2 author repair measurements, no render/raycast, only authorized source arrays."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,copy,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.optimize import least_squares
R=Path(__file__).parent;I=R.parent.parent/'inputs/M2';P=json.loads((I/'packet.json').read_text());L=json.loads((R/'versions/v1/layout.json').read_text());X=np.array(L['model_from_input']);F=P['frames'];out={}
def pose(i):return X@np.array(F[i]['camera_to_world'])
def pc(i,q):
 T=pose(i);return (np.array(q)-T[:3,3])@T[:3,:3]
def proj(i,q):
 a=pc(i,q);return a[:2]/a[2]*762.8+[640,480]
def ref(i,uv):
 with np.load(F[i]['geometry']) as n:
  K=n['intrinsics'];ray=np.linalg.inv(np.array(F[i]['intrinsics']))@np.r_[uv,1];px=K@ray;u,v=np.round(px[:2]).astype(int);d=n['depth_z_m'];m=n['valid_mask'];ys=slice(max(0,v-1),min(d.shape[0],v+2));xs=slice(max(0,u-1),min(d.shape[1],u+2));a=d[ys,xs];valid=m[ys,xs]
  return float(np.median(a[valid])) if valid.any() else None
obs33=[(360,70),(464,151),(446,210),(504,220),(563,217),(604,261),(616,290),(531,281),(669,266),(734,285),(801,245),(733,238),(705,190),(793,174),(1118,159)]
obs129=[(266,127),(549,216),(598,285),(770,295),(815,286),(896,326),(933,360),(828,355),(991,326),(1131,343),(1175,277),(1060,270),(912,204),(677,126),None]
lamps=[]
for j,li in enumerate(L['lights']):
 observations=[(33,obs33[j])]
 if obs129[j]:observations.append((129,obs129[j]))
 if j==14:observations += [(61,(577,128)),(74,(891,80)),(82,(826,333))]
 before=np.array(li['center']);fit=least_squares(lambda q:np.concatenate([proj(i,q)-uv for i,uv in observations]),before,loss='soft_l1',f_scale=10).x
 # diameter from measured v1 full rim span in33; improve center via RGB independent of DA3.
 diameter=li['pixel_width']*pc(33,fit)[2]/762.8
 li['center']=fit.tolist();li['diameter']=float(diameter);li['evidence_frames']=[i for i,uv in observations];li['uncertainty']='RGB diffuser correspondence triangulation; far overlapping lamp identity tentative; native-pose consistency limits; profile and hidden weave inferred'
 rows=[]
 for i,uv in observations:
  d=ref(i,uv);rows.append({'frame':i,'rgb_point':uv,'rgb_box':[uv[0]-10,uv[1]-8,uv[0]+10,uv[1]+8],'before_projection':proj(i,before).tolist(),'after_projection':proj(i,fit).tolist(),'reprojection_error_px':float(np.linalg.norm(proj(i,fit)-uv)),'input_da3_z_m':d,'before_center_minus_da3_m':None if d is None else float(pc(i,before)[2]-d),'after_center_minus_da3_m':None if d is None else float(pc(i,fit)[2]-d)})
 lamps.append({'id':li['id'],'before_center':before.tolist(),'after_center':li['center'],'before_diameter':json.loads((R/'versions/v1/layout.json').read_text())['lights'][j]['diameter'],'after_diameter':diameter,'observations':rows})
out['lamps']=lamps
# Every mirror center is constrained to known wall plane, fitted jointly in61/74. DA3 reflection pixels are diagnostic only.
a61=[(745,423,87),(621,361,39),(594,430,25),(628,498,40),(807,529,25),(913,486,79),(870,372,38),(951,315,49),(1045,392,69),(1039,492,31)]
a74=[(864,389,85),(759,339,42),(727,418,28),(760,483,42),(915,485,24),(991,430,64),(970,335,35),(1028,283,40),(1080,339,51),(1066,423,24)]
mir=[]
for j,(a,b) in enumerate(zip(a61,a74)):
 fit=least_squares(lambda yz:np.r_[proj(61,[3.61,*yz])-a[:2],proj(74,[3.61,*yz])-b[:2]],[2.5,1.5]).x;q=np.r_[3.61,fit]
 rad=[]
 for i,s in [(61,a),(74,b)]:
  extent=max(np.linalg.norm(proj(i,q+[0,.01,0])-proj(i,q)),np.linalg.norm(proj(i,q+[0,0,.01])-proj(i,q)));rad.append(s[2]*.01/extent)
 mir.append({'center':q.tolist(),'radius':float(np.mean(rad)),'observations':[{'frame':i,'rgb_center':s[:2],'rgb_radius_px':s[2],'reprojection_px':float(np.linalg.norm(proj(i,q)-s[:2])),'center_minus_da3_m':float(pc(i,q)[2]-ref(i,s[:2]))} for i,s in [(61,a),(74,b)]]})
out['mirrors']=mir;L['mirrors']['discs']=[{'center':d['center'],'radius':d['radius']} for d in mir]
# Fit desk top front corners jointly; modest pose/depth contradictions retained.
deskobs=[(33,[(543,438),(689,437)]),(129,[(847,547),(1046,559)]),(108,[(1080,531),None]),(118,[(1080,510),None])]
def deskerr(p):
 x,y,w,top=p;pts=[[x-w/2,y,top],[x+w/2,y,top]]
 return np.concatenate([proj(i,pts[k])-uv for i,uvs in deskobs for k,uv in enumerate(uvs) if uv is not None])
fit=least_squares(deskerr,[.6,13.,3.1,.94],bounds=([-2,10,1.5,.3],[3,15,5,1.5]),loss='soft_l1',f_scale=10).x
x,y,w,top=fit;L['reception']['center']=[float(x),float(y+.525),float((top+L['floor_z'])/2)];L['reception']['dimensions']=[float(w),1.05,float(top-L['floor_z'])]
out['desk']={'before':json.loads((R/'versions/v1/layout.json').read_text())['reception'],'after':L['reception'],'observations':deskobs,'fit_corner_errors_px':deskerr(fit).tolist(),'note':'RGB top front silhouette fit; corner identification in grazing108/118 approximate. Depth sign conflict kept.'}
# Recess x is measured from DA3; identify sharp wall return corner in three RGBs at z2.3.
ys=[]
for i,u in [(61,297),(74,296),(82,508)]:
 res=least_squares(lambda y: [proj(i,[3.71,y[0],2.3])[0]-u],[8.]);ys.append({'frame':i,'rgb_u_at_z2_3':u,'fitted_y':float(res.x[0])})
out['recess_corner']=ys;L['bounds']['recess_start_y']=float(np.median([r['fitted_y'] for r in ys]))
L['version']=2;L['seat_boundary_mode']='Voronoi clipped modular shared boundaries, 6mm gap';L['passage']={'id':'service_door_1','center_y':-.3,'width':1.05,'height':2.24,'return_depth':1.5,'state':'open','provenance':'opening observed RGB61/74/82; bounded return depth inferred'}
(R/'analysis/revision_measurements.json').write_text(json.dumps(out,indent=2)+'\n');(R/'analysis/proposed_layout_v2.json').write_text(json.dumps(L,indent=2)+'\n')
for i in [33,61,74,82,100,108,118,129]:
 im=Image.open(F[i]['rgb']).convert('RGB');d=ImageDraw.Draw(im)
 for li in L['lights']:
  uv=proj(i,li['center']);u,v=uv
  if pc(i,li['center'])[2]>0 and -100<u<1380 and -100<v<1060:d.ellipse((u-6,v-6,u+6,v+6),outline='red',width=2);d.text((u+6,v),li['id'][-2:],fill='red',stroke_width=1,stroke_fill='white')
 for j,dd in enumerate(mir):
  if i not in [61,74,82]:continue
  u,v=proj(i,dd['center']);d.ellipse((u-5,v-5,u+5,v+5),outline='cyan',width=2)
 x,y,z=L['reception']['center'];w,dep,h=L['reception']['dimensions'];verts=[[x-w/2,y-dep/2,z+h/2],[x+w/2,y-dep/2,z+h/2],[x+w*.42,y-dep*.27,z-h/2],[x-w*.40,y-dep*.27,z-h/2]];d.line([tuple(proj(i,q)) for q in verts+[verts[0]]],fill='blue',width=3)
 im.save(R/f'analysis/proposed_overlay_{i:04d}.jpg')
print('Desk',out['desk']);print('recess',ys);print('lamps',[(x['id'],np.round(x['after_center'],2).tolist(),round(max(y['reprojection_error_px'] for y in x['observations']),1)) for x in lamps]);print('mirrors',[(np.round(x['center'],2).tolist(),round(x['radius'],2)) for x in mir])
