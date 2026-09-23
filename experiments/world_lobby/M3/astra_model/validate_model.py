"""Meaningful analytic/artifact validation for clean-review physical and interface fixes."""
import json,math,itertools,struct
from pathlib import Path
from collections import Counter,deque
import numpy as np
OUT=Path(__file__).parent
plan=json.load(open(OUT/'geometry_plan.json'));od=json.load(open(OUT/'objects.json'));cd=json.load(open(OUT/'colliders.json'));cams=json.load(open(OUT/'cameras.json'))['cameras'];packet=json.load(open(plan['packet_path']));objects=od['objects'];cols=cd['colliders'];by={o['object_id']:o for o in objects};pb={o['object_id']:o for o in plan['objects']}
# Synchronize provenance-only correction after construction; no geometry changes.
for o in objects:
 for k in ['geometry_provenance','confidence','spatial_relations','unresolved_localization','local_layout_adjustment']:
  if k in pb[o['object_id']]:o[k]=pb[o['object_id']][k]
for c in cols:
 if c['object_id'] in pb:c['geometry_provenance']=pb[c['object_id']]['geometry_provenance']
json.dump(od,open(OUT/'objects.json','w'),indent=2);json.dump(cd,open(OUT/'colliders.json','w'),indent=2)
ids={o['object_id'] for o in objects}|{o['object_id'] for o in od['scene_entities']}
assert len(by)==len(objects)
missing=[(o['object_id'],r) for o in objects for r in o['spatial_relations'] if r['object_id'] not in ids];assert not missing
for o in objects:
 assert all(math.isfinite(v) for b in o['bounds'] for v in b)
 assert all(o['bounds'][0][j]<=o['bounds'][1][j] for j in range(3))
 assert isinstance(o['geometry_provenance']['conflict_present'],bool)
seats=[o for o in plan['objects'] if o['category'] in ['lounge_chair','ottoman']];seatpairs=[];intersections=[]
for a,b in itertools.combinations(seats,2):
 ra=min(a['size'][:2])/2;rb=min(b['size'][:2])/2;gap=float(np.linalg.norm(np.array(a['center'][:2])-b['center'][:2])-ra-rb);bottom_a=a['center'][2]-a['size'][2]/2;bottom_b=b['center'][2]-b['size'][2]/2;za=[bottom_a+a['size'][2]*(.34-.275),bottom_a+a['size'][2]*(.34+.275)];zb=[bottom_b+b['size'][2]*(.34-.275),bottom_b+b['size'][2]*(.34+.275)];zoverlap=min(za[1],zb[1])-max(za[0],zb[0]);row={'pair':[a['object_id'],b['object_id']],'radial_clearance_m':gap,'vertical_overlap_m':zoverlap};seatpairs.append(row)
 if gap<0 and zoverlap>0:intersections.append(row)
assert not intersections
floor=next(c for c in cols if c['object_id']=='floor');assert floor['role']=='floor';assert abs(floor['bounds'][1][2]-plan['floor_z'])<1e-8
assert len(cams)==175
pose_error=max(float(np.max(abs(np.array(c['camera_to_world'])-np.array(packet['frames'][c['frame_id']]['camera_to_world'])))) for c in cams);assert pose_error==0
nav=json.load(open(OUT/'navigation_constraints.json'));assert nav['unknown_regions'] and not nav['unknown_regions_are_physical_colliders'];assert all(c.get('physical_obstacle') is True for c in cols)
for oid in ['floor_lamp_0','floor_lamp_1']:
 c=next(c for c in cols if c['object_id']==oid);o=by[oid];assert all(c['bounds'][0][k]<=o['bounds'][0][k]+1e-5 and c['bounds'][1][k]>=o['bounds'][1][k]-1e-5 for k in range(3))
assert sum(c['role']=='overhead_obstacle' for c in cols)==20
magic,version,total=struct.unpack('<4sII',open(OUT/'scene.glb','rb').read(12));assert magic==b'glTF' and version==2
category=Counter(o['category'] for o in objects);architecture=sum(category[k] for k in ['floor','ceiling','window','wall','door','column']);inventory={'named_model_elements':len(objects),'trim_elements':category['trim'],'non_trim_entries':len(objects)-category['trim'],'architectural_entities':architecture,'other_non_trim_entries':len(objects)-category['trim']-architecture,'scene_roots_and_groups_not_counted':len(od['scene_entities']),'category_counts':dict(category),'verified_real_instance_count':None,'interpretation':'Named model inventory only; not independent object detection or coverage performance.'}
# A coarse model-space traversability sanity check, not a real-world safety claim.
lo,hi=np.array(nav['known_navigation_bounds']);step=.20;xs=np.arange(lo[0]+.45,hi[0]-.45,step);ys=np.arange(lo[1]+.45,hi[1]-.45,step);xx,yy=np.meshgrid(xs,ys,indexing='ij');occ=np.zeros(xx.shape,bool)
for c in cols:
 if c['role']=='floor':continue
 a,b=np.array(c['bounds']);
 if b[2]<plan['floor_z']+.02 or a[2]>plan['floor_z']+1.65:continue
 occ|=(xx>=a[0]-.45)&(xx<=b[0]+.45)&(yy>=a[1]-.45)&(yy<=b[1]+.45)
for c in nav['unknown_regions']+nav.get('vegetation_keepouts',[]):
 a,b=np.array(c['bounds']);occ|=(xx>=a[0]-.45)&(xx<=b[0]+.45)&(yy>=a[1]-.45)&(yy<=b[1]+.45)
free=~occ;seen=np.zeros_like(free);components=[]
for seed in zip(*np.where(free)):
 if seen[seed]:continue
 q=deque([seed]);seen[seed]=True;n=0
 while q:
  x,y=q.popleft();n+=1
  for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=nx<free.shape[0] and 0<=ny<free.shape[1] and free[nx,ny] and not seen[nx,ny]:seen[nx,ny]=True;q.append((nx,ny))
 components.append(n)
assert components
checks={'status':'passed','revision':3,'inventory':inventory,'seat_cylinder_intersections':intersections,'minimum_seat_radial_clearance_m':min(x['radial_clearance_m'] for x in seatpairs),'maximum_seat_translation_m':max(o['local_layout_adjustment']['translation_norm_m'] for o in seats),'seat_pair_measurements':seatpairs,'all_relation_targets_resolve':True,'floor_top_z':plan['floor_z'],'camera_count':len(cams),'camera_pose_max_abs_error':pose_error,'physical_colliders':len(cols),'unknown_regions_counted_as_physical_colliders':False,'floor_lamp_full_shade_coverage':True,'overhead_shade_colliders':20,'glb_v2_bytes':total,'model_space_ground_sanity':{'grid_m':step,'footprint_radius_plus_margin_m':.45,'body_height_m':1.65,'free_area_estimate_m2':float(free.sum()*step**2),'connected_free_component_areas_m2':sorted([n*step**2 for n in components],reverse=True),'caveat':'Coarse check of this uncertain static model only; no GT and no real-world safety validation.'}}
json.dump(checks,open(OUT/'artifact_checks.json','w'),indent=2);print(json.dumps({k:v for k,v in checks.items() if k!='seat_pair_measurements'},indent=2))
