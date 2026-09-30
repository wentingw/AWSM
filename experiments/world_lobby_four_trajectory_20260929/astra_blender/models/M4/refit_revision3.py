import json,numpy as np
from pathlib import Path
from scipy.optimize import least_squares
B=Path(__file__).resolve().parent;C=json.load(open(B/'cameras.json'))['cameras'];cams={c['frame_id']:c for c in C}
def ray(i,u,v):
 c=cams[i];K=np.array(c['K']);K[0]*=780/c['image_size'][0];K[1]*=585/c['image_size'][1];T=np.array(c['camera_to_world']);return T[:3,3],T[:3,:3]@np.linalg.inv(K)@np.array([u,v,1])
def plane(i,uv,axis,value):
 o,r=ray(i,*uv);return o+r*((value-o[axis])/r[axis])
def proj(i,p):
 c=cams[i];K=np.array(c['K']);K[0]*=780/c['image_size'][0];K[1]*=585/c['image_size'][1];q=np.linalg.inv(np.array(c['camera_to_world']))@np.r_[p,1];uv=K@q[:3];return uv[:2]/uv[2]
measurements={
'near_ottoman_left':{'z':.42,'outlines':{0:[(578,468),(631,504),(578,531),(525,491)],60:[(445,416),(486,437),(450,455),(407,434)],138:[(307,455),(361,489),(306,529),(250,490)]}},
'near_table':{'z':.405,'outlines':{60:[(430,488),(508,532),(428,576),(350,534)],138:[(107,472),(207,509),(96,577),(3,544)]}},
}
out={}
for name,m in measurements.items():
 P=np.array([plane(i,uv,2,m['z']) for i,uvs in m['outlines'].items() for uv in uvs]);init=[*P[:,:2].mean(0),.5]
 fit=least_squares(lambda a:np.linalg.norm(P[:,:2]-a[:2],axis=1)-a[2],init,loss='soft_l1',f_scale=.04);xy=fit.x[:2];rad=fit.x[2];out[name]={'center':[*xy,m['z']],'radius':rad,'surface_boundary_points':P.tolist(),'rms_radial_residual_m':float(np.sqrt(np.mean(fit.fun**2))),'observations':m,'fit_type':'manual boundary rays on horizontal plane; no global scale correction'}
 print(name,fit.x.round(3),'RMS',np.sqrt(np.mean(fit.fun**2)));print('projectedcenters',[(i,proj(i,[*xy,m['z']]).round(1)) for i in [0,60,138]])
for name,uv in [('near_chair_mid',(510,454)),('near_chair_right',(568,488)),('missing_ottoman',(573,573))]:
 p=plane(60,uv,2,.42);out[name]={'center':p.tolist(),'radius':.405 if 'chair' in name else .425,'evidence_frame_ids':[60,66,138],'provenance':'RGB top-surface calibrated ray at seat z.42; radius based on observed silhouette; occluded underside inferred'};print(name,p.round(3))
# Tropical planter front face and front-wall row inferred jointly with reverse frame90.
for name,uv in [('tropical_visible_center',(752,427)),('tropical_visible_base',(754,538))]:print(name,plane(60,uv,2,.92 if 'center' in name else .03).round(3))
# Door boundaries intersect the locally constrained glazing plane, y25.78.
for name,i,uvs in [('door_rear',108,[(442,345),(520,344)]),('door_front',0,[(217,239),(244,239)])]:
 P=np.array([plane(i,uv,1,25.68) for uv in uvs]);out[name]={'edge_points':P.tolist(),'center_x':float(P[:,0].mean()),'width_x':float(abs(P[0,0]-P[1,0])),'evidence':[i]};print(name,out[name])
json.dump(out,open(B/'revision3_measurements.json','w'),indent=2)
