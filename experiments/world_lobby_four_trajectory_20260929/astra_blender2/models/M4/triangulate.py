exec(open('measure_scene.py').read().split('records=[]')[0])
# Same visible physical features, hand picked original pixels.
features={
'shield_top_L':[(33,607,347),(129,948,435)],'shield_bottom':[(33,622,400),(129,975,506)],'tree_left_pot_top':[(33,505,437),(129,820,540)],'tree_right_pot_top':[(33,734,437),(129,1140,566)],'end_glass_corner_floor':[(33,424,470),(129,745,568)],'end_glass_corner_ceiling':[(33,421,230),(129,750,313)],
'door_near_bottom_L':[(108,708,555),(118,651,579)],'door_near_bottom_R':[(108,854,551),(118,793,548)],'door_near_top_L':[(108,708,321),(118,651,280)],
'desk_left_top':[(33,543,437),(129,843,544)],'desk_right_top':[(33,690,438),(129,1048,562)],
'column_floor_center':[(33,297,641),(91,894,477),(118,183,773),(129,392,731)],
'mirror_pot_base':[(61,516,594),(74,693,619)],
'mirror_big_center':[(61,742,421),(74,860,390)],
'mirror_left_door_bottom_L':[(61,363,545),(74,414,614)],
'mirror_left_door_bottom_R':[(61,451,555),(74,546,593)],
'mirror_left_door_top_L':[(61,352,341),(74,383,334)],
'planter_front_left_top':[(33,463,518),(129,541,645)],
'planter_front_right_top':[(33,597,517),(129,729,683)],
'planter_other_left_top':[(33,646,515),(129,803,700)],
'planter_other_right_top':[(33,793,513),(129,1020,733)],
'carpet_left_edge':[(33,284,790)],
}
out=[]
for name,obs in features.items():
 origins=[];dirs=[]
 for i,u,v in obs:
  T=np.array(p['frames'][i]['camera_to_world']);K=np.array(p['frames'][i]['intrinsics']);d=T[:3,:3]@np.linalg.solve(K,[u,v,1]);d/=np.linalg.norm(d);origins.append(T[:3,3]);dirs.append(d)
 if len(obs)>1:
  mats=[np.eye(3)-np.outer(d,d) for d in dirs];pt=np.linalg.solve(sum(mats),sum(m@o for m,o in zip(mats,origins)));r=[np.linalg.norm(m@(pt-o)) for m,o in zip(mats,origins)];projections=[]
  for i,u,v in obs:
   T=np.array(p['frames'][i]['camera_to_world']);q=T[:3,:3].T@(pt-T[:3,3]);uv=np.array(p['intrinsics'])@q;projections.append(float(np.linalg.norm(uv[:2]/uv[2]-[u,v])))
  out.append(dict(label=name,observations=obs,world_point=pt.tolist(),ray_residuals_m=r,reprojection_error_px=projections));print(name,np.round(pt,3),'ray',np.round(r,3),'px',np.round(projections,2))
print('RAY HEIGHT ANCHORS')
for i,names in points.items():
 for name,uv in names.items():
  if any(s in name for s in ['seat','table','planter','desk','bowl','tree','pot']):
   height=.48 if 'seat' in name else .43 if 'table' in name else .65 if 'planter' in name else .75 if 'desk' in name else .35
   T=np.array(p['frames'][i]['camera_to_world']);d=T[:3,:3]@np.linalg.solve(np.array(p['intrinsics']),[*uv,1]);pt=T[:3,3]+d*((height-T[2,3])/d[2]);print(i,name,np.round(pt,2))
json.dump(dict(triangulated_features=out,method='Least squares camera-ray intersection, original pixel correspondences, exact packet cameras'),open(ROOT/'analysis/triangulation.json','w'),indent=2)
