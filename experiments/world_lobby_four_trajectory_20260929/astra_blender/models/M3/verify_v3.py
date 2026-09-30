"""Author geometry checks only: no renders and no all-frame depth pass."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
import numpy as np
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'scene.blend'))
bpy.context.view_layer.update(); deps=bpy.context.evaluated_depsgraph_get()
records=json.loads((O/'objects.json').read_text())['objects']
actual={o.name for o in bpy.context.scene.objects if o.type=='MESH'}
recorded=[n for r in records for n in r['component_names']]
assert set(recorded)==actual and len(recorded)==len(actual)
seats=json.loads((O/'analysis/seat_repair_measurements.json').read_text())
checks=[]
for a in seats:
 x,y=a['center_xy']; verts=[]
 for component in ['seat','curved_backrest']:
  obj=bpy.data.objects.get(a['id']+'__'+component)
  if obj is None:continue
  ev=obj.evaluated_get(deps);me=ev.to_mesh()
  verts.extend([list(ev.matrix_world@v.co)[:2] for v in me.vertices]);ev.to_mesh_clear()
 for b in seats:
  if a['id']==b['id'] or a['id'].split('_')[0]!=b['id'].split('_')[0]:continue
  xx,yy=b['center_xy'];d=np.array([xx-x,yy-y]);normal=d/np.linalg.norm(d)
  clearance=-float(np.max((np.array(verts)-np.array([(x+xx)/2,(y+yy)/2]))@normal))
  assert clearance>=.00599,(a['id'],b['id'],clearance)
  checks.append({'object_id':a['id'],'other_id':b['id'],'evaluated_seat_and_back_clearance_to_midplane_m':clearance})
scene=bpy.context.scene
rays=[]
for x in [1.65,1.85,2.05,2.25,2.45]:
 for z in [.2,.9,1.7]:
  hit=scene.ray_cast(deps,Vector((x,.15,z)),Vector((0,-1,0)),distance=.65)
  rays.append({'x':x,'z':z,'blocked':bool(hit[0]),'object':hit[4].name if hit[0] else None})
assert not any(r['blocked'] for r in rays),rays
hit=scene.ray_cast(deps,Vector((9.12,.15,.9)),Vector((0,-1,0)),distance=.65)
assert hit[0] and hit[4].name=='interior_door_01__leaf'
colliders=json.loads((O/'colliders.json').read_text())['colliders']
blocked=[]
for c in colliders:
 if c['object_id'] not in ['mirror_bay_wall','interior_door_00']:continue
 lo=c['bounds']['min'];hi=c['bounds']['max']
 if lo[0]<2.45 and hi[0]>1.65 and lo[2]<1.7 and hi[2]>.2 and lo[1]<.15 and hi[1]>-.5:blocked.append(c)
assert not blocked
P=Path('/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3')
j=json.loads((P/'packet.json').read_text());cams=json.loads((O/'cameras.json').read_text());t=np.load(O/'analysis/model_from_input.npy')
pose_error=max(float(np.max(np.abs(np.array(a['camera_to_world'])-t@np.array(b['camera_to_world'])))) for a,b in zip(cams['frames'],j['frames']))
assert pose_error==0 and len(cams['frames'])==180
assert all(a['intrinsics']==b['intrinsics'] for a,b in zip(cams['frames'],j['frames']))
old=json.loads((O/'analysis/v3_baseline_hashes.json').read_text())
unchanged={p:hashlib.sha256((O/p).read_bytes()).hexdigest()==sha for p,sha in old.items()}
assert all(unchanged.values())
result={'status':'PASS','check_type':'author scoped actual candidate verification, not independent review','model_sha256':hashlib.sha256((O/'scene.blend').read_bytes()).hexdigest(),'mesh_object_count':len(actual),'semantic_object_count':len(records),'component_mapping_exact':True,'evaluated_cushion_partition_checks':checks,'open_passage_rays':rays,'closed_door_01_hit':hit[4].name,'aperture_collider_blockers':blocked,'camera_count':180,'camera_max_transform_error':pose_error,'baseline_files_unchanged':unchanged,'extra_render_count':0,'extra_full_input_passes':0,'limitations':['Partition checks cover seats and curved backs, not exhaustive scene collisions.','Door rays test the model wall thickness; unseen space beyond the aperture is not reconstructed.','No new input depth agreement metric computed.']}
(O/'checks/v3_author_geometry_checks.json').write_text(json.dumps(result,indent=2))
print('V3 AUTHOR GEOMETRY CHECKS PASS',flush=True)
