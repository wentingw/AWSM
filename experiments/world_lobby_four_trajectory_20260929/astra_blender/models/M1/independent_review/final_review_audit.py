"""Read-only M1 artifact audit. No renders, model writes, or external scene inputs."""
import bpy, json, hashlib, math
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path("/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1")
I=Path("/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1")
O=R/'independent_review'
reads=[]
def readjson(p):
 reads.append(str(p)); return json.loads(p.read_text())
objects=readjson(R/'objects.json')['objects']; records={o['id']:o for o in objects}
colliders=readjson(R/'colliders.json')['colliders']
cams=readjson(R/'cameras.json'); packet=readjson(I/'packet.json')
checks=readjson(R/'analysis/camera_checks.json')['checks']
manifest=readjson(R/'modelling_manifest.json'); iteration=readjson(R/'iteration_log.json')
ins=readjson(O/'final_artifact_inspection.json')
reads.append(str(R/'scene.blend'))
sha=hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'))
scene=bpy.context.scene; deps=bpy.context.evaluated_depsgraph_get()
meshes={o.name:o for o in scene.objects if o.type=='MESH'}
listed=[n for o in objects for n in o['component_names']]
mapping={'unregistered_meshes':sorted(set(meshes)-set(listed)), 'missing_meshes':sorted(set(listed)-set(meshes)), 'multiply_registered':sorted({n for n in listed if listed.count(n)>1}), 'custom_property_mismatches':[n for o in objects for n in o['component_names'] if n in meshes and meshes[n].get('semantic_id')!=o['id']]}
actual={m['name']:m for m in ins['meshes']}
bounds_errors=[]
for o in objects:
 bs=[actual[n]['bounds'] for n in o['component_names']]
 lo=np.min([b[0] for b in bs],axis=0); hi=np.max([b[1] for b in bs],axis=0)
 err=max(np.max(np.abs(lo-o['bounds']['min'])),np.max(np.abs(hi-o['bounds']['max'])))
 if err>1e-4: bounds_errors.append({'id':o['id'],'max_error':float(err)})
# Exact world-space evaluated geometry duplicates; topology included, ordering-sensitive.
hashgroups={}
for name,obj in meshes.items():
 ev=obj.evaluated_get(deps); mesh=ev.to_mesh();mesh.calc_loop_triangles()
 pts=np.array([ev.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
 tris=np.array([list(t.vertices) for t in mesh.loop_triangles],dtype=np.int64)
 h=hashlib.sha256(np.round(pts,6).tobytes()+tris.tobytes()).hexdigest()
 hashgroups.setdefault(h,[]).append(name);ev.to_mesh_clear()
duplicates=[v for v in hashgroups.values() if len(v)>1]
T=np.array(cams['frames'][179]['camera_to_world'])
saved_cam=np.array(scene.camera.matrix_world)
cam_audit={'count':len(cams['frames']),'valid_true_count':sum(f['valid'] for f in cams['frames']),'check_render_usable':[f['sample_index'] for f in cams['frames'] if f['check_render_usable']], 'max_orthonormal_error':max(float(np.max(np.abs(np.array(f['camera_to_world'])[:3,:3].T@np.array(f['camera_to_world'])[:3,:3]-np.eye(3)))) for f in cams['frames']), 'rotation_determinant_range':[min(float(np.linalg.det(np.array(f['camera_to_world'])[:3,:3])) for f in cams['frames']),max(float(np.linalg.det(np.array(f['camera_to_world'])[:3,:3])) for f in cams['frames'])], 'saved_camera_sample':179,'saved_camera_cv_to_blender_max_error':float(np.max(np.abs(saved_cam-T@np.diag([1,-1,-1,1])))), 'intrinsics_from_blender_at_1280':[scene.camera.data.lens/scene.camera.data.sensor_width*1280,scene.camera.data.lens/scene.camera.data.sensor_width*1280,640.,480.], 'source_metadata_mismatches':[i for i,(f,p) in enumerate(zip(cams['frames'],packet['frames'])) if any(f[k]!=p[k] for k in ['sample_index','source_index','timestamp_ns','intrinsics'])]}
residual=[]
for c in checks:
 f=cams['frames'][c['sample_index']];T=np.array(f['camera_to_world']);K=np.array(f['intrinsics']);out=[]
 for lm in c['landmarks']:
  q=T[:3,:3].T@(np.array(lm['world_point'])-T[:3,3]);v=K@q;uv=v[:2]/v[2]
  out.append({'name':lm['name'],'observed':lm['pixel_observed'],'projected':uv.tolist(),'residual_pixels':float(np.linalg.norm(uv-lm['pixel_observed']))})
 residual.append({'frame':c['sample_index'],'rms_pixels':float(np.sqrt(np.mean([x['residual_pixels']**2 for x in out]))),'landmarks':out})
# Targeted door rays from lobby toward east. Tests are geometry, not image/depth comparison.
rays=[]
for wall,positions in [('wall_east_main',[4.8,11.3]),('wall_east_recess',[14.6,16.35])]:
 x=7.35 if wall=='wall_east_main' else 8.8
 for y in positions:
  for dy in [-.4,0,.4]:
   origin=Vector((x-.4,y+dy,1.0)); hit,loc,norm,index,obj,mat=scene.ray_cast(deps,origin,Vector((1,0,0)),distance=.7)
   rays.append({'wall':wall,'nominal_door_y':y,'offset_y':dy,'hit':obj.name if hit else None,'hit_location':list(loc) if hit else None})
# Collider occupancy using actual compound wall parts, at pedestrian height.
col_by_id={c['object_id']:c for c in colliders}
col_doors=[]
collider_component_errors=[]
for c in colliders:
 for part in c.get('parts',[]):
  n=part['component_name'];bb=part['bounds']
  if n not in actual or np.max(np.abs(np.array([bb['min'],bb['max']])-np.array(actual[n]['bounds'])))>1e-4:collider_component_errors.append(n)
for wall,y in [('wall_east_main',4.8),('wall_east_main',11.3),('wall_east_recess',14.6),('wall_east_recess',16.35)]:
 c=col_by_id[wall]
 for dy in [-.4,0,.4]:
  hits=[]
  for part in c.get('parts',[c]):
   lo=part['bounds']['min'];hi=part['bounds']['max']
   if lo[1]<y+dy<hi[1] and lo[2]<1<hi[2]:hits.append(part.get('component_name',wall))
  col_doors.append({'wall':wall,'door_y':y,'offset_y':dy,'wall_collider_type':c['type'],'wall_collider_parts_at_z1':hits})
passage_rays=[]
for y in [4.4,4.8,5.2]:
 for z in [.3,1.,1.8]:
  origin=Vector((7.0,y,z));hit,loc,norm,index,obj,mat=scene.ray_cast(deps,origin,Vector((1,0,0)),distance=1.6)
  passage_rays.append({'y':y,'z':z,'hit':obj.name if hit else None})
# Direct component support distances to z=.012 inset top (metric-like units, not real measured meters).
supports=[]
for o in objects:
 if o['category'] in ['chair','ottoman','coffee_table']:
  lo=o['bounds']['min'];hi=o['bounds']['max'];supports.append({'id':o['id'],'lowest_z':lo[2],'gap_from_inset_top':lo[2]-.012})
# Horizontal overlap between actual circular seat cushions (not AABB overlap).
seat_overlaps=[]
seats=[(o,meshes[o['id']+'__seat_cushion']) for o in objects if o['category'] in ['chair','ottoman']]
for i,(a,oa) in enumerate(seats):
 for b,ob in seats[i+1:]:
  dist=math.hypot(oa.location.x-ob.location.x,oa.location.y-ob.location.y);ra=oa.dimensions.x/2;rb=ob.dimensions.x/2
  if ra+rb-dist>.025: seat_overlaps.append({'ids':[a['id'],b['id']],'horizontal_penetration':ra+rb-dist,'center_distance':dist,'radii':[ra,rb]})
# Aperture width from panel bounds at pedestrian height; leaf overlap with panels.
door_overlap=[]
for obj in meshes.values():
 if not obj.name.startswith('elevator_') or '__leaf_' not in obj.name: continue
 a=np.array(actual[obj.name]['bounds'])
 for wall in [o for o in meshes.values() if o.name.startswith('wall_east_') and '__panel_' in o.name]:
  b=np.array(actual[wall.name]['bounds']);over=np.minimum(a[1],b[1])-np.maximum(a[0],b[0])
  if np.all(over>1e-5):door_overlap.append({'door_component':obj.name,'wall_component':wall.name,'intersection_aabb_dimensions':over.tolist()})
mats={}
for name in ['mirror','black_polished','cream_lamp','wall_oak','ivory_stone']:
 m=bpy.data.materials.get(name);p=m.node_tree.nodes.get('Principled BSDF')
 mats[name]={'base_color':list(p.inputs['Base Color'].default_value),'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value,'node_types':[n.type for n in m.node_tree.nodes]}
# Scene/model-specific projection extents of selected actual evaluated vertices; no image synthesized.
projections={}
for i in [0,45,90,135,179]:
 T=np.array(cams['frames'][i]['camera_to_world']);K=np.array(cams['frames'][i]['intrinsics']);view={}
 for sid in ['plant_glass_north','column_1','mirror_0','mirror_4','seat_S1','seat_S2','table_south','seat_N1','table_north','planter_north_left','planter_north_right']:
  pts=[]
  for n in records[sid]['component_names']:
   obj=meshes[n]; ev=obj.evaluated_get(deps); me=ev.to_mesh();pts.extend([list(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear()
  q=(np.array(pts)-T[:3,3])@T[:3,:3];q=q[q[:,2]>.05]
  if len(q):
   uv=q@K.T;uv=uv[:,:2]/uv[:,2:]
   view[sid]={'projected_bounds_1280x960':[uv.min(0).tolist(),uv.max(0).tolist()], 'vertices_inside_image':int(np.sum((uv[:,0]>=0)&(uv[:,0]<1280)&(uv[:,1]>=0)&(uv[:,1]<960)))}
  else:view[sid]={'all_vertices_behind_near_plane':True}
 projections[str(i)]=view
report={'model_sha256':sha,'intentional_reads':reads,'mesh_count':len(meshes),'semantic_object_count':len(objects),'semantic_mapping':mapping,'record_bounds_disagreements':bounds_errors,'exact_world_mesh_duplicates':duplicates,'camera_audit':cam_audit,'recomputed_author_landmark_residuals':residual,'targeted_door_rays':rays,'door_wall_collider_checks':col_doors,'collider_component_bounds_errors':collider_component_errors,'passage_rays':passage_rays,'door_leaf_panel_box_intersections':door_overlap,'seat_cushion_circular_overlaps':seat_overlaps,'furniture_floor_support_bounds':supports,'selected_materials':mats,'selected_projected_extents':projections,'scene_settings':{'engine':scene.render.engine,'cycles_device':scene.cycles.device,'samples':scene.cycles.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'lights':sum(o.type=='LIGHT' for o in scene.objects),'cameras':sum(o.type=='CAMERA' for o in scene.objects)},'limitations':['No exhaustive collision, manifoldness, topology or navigation verification.','Duplicate check requires matching evaluated vertex and triangle ordering, rounded to 1e-6.','Door intersections use axis-aligned unmodified boxes; targeted rays confirm visible obstruction.','Recomputed landmarks are author-picked RGB points conditional on assumed model geometry, not independent calibration or metric truth.','Projected extents do not account for occlusion.'],'rendering_views_added':0}
(O/'final_structural_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('M1_REVIEW_AUDIT',json.dumps({k:report[k] for k in ['model_sha256','mesh_count','semantic_object_count','semantic_mapping','record_bounds_disagreements','exact_world_mesh_duplicates','camera_audit','door_leaf_panel_box_intersections','seat_cushion_circular_overlaps']}))

