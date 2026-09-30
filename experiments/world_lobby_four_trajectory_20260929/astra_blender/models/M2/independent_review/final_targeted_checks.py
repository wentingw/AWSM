import bpy,json,hashlib,itertools,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(O/'scene.blend'));scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();result={'model_sha256':hashlib.sha256((O/'scene.blend').read_bytes()).hexdigest(),'scope':'Final reviewer re-execution of inspected author targeted-check logic; no rendering or scene save'}
result['rays']=[]
for name,origin,direction,length in [('open_passage',(3,-.42,1),(1,0,0),1.2),('closed_other_door',(3,6.24,1),(1,0,0),1.2),('near_wall',(0,0,3),(0,-1,0),4)]:
 hit,loc,normal,idx,obj,mat=scene.ray_cast(deps,Vector(origin),Vector(direction),distance=length);result['rays'].append({'name':name,'hit':hit,'object':obj.name if obj else None,'point':list(loc) if hit else None})
seats=[o for o in scene.objects if o.name.endswith('__padded_seat')];trees={};boxes={}
for o in seats:
 ev=o.evaluated_get(deps);me=ev.to_mesh();v=[ev.matrix_world@p.co for p in me.vertices];f=[list(p.vertices) for p in me.polygons];trees[o.name]=BVHTree.FromPolygons(v,f);boxes[o.name]=[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]];ev.to_mesh_clear()
result['cushion_intersections']=[]
for a,b in itertools.combinations(seats,2):
 ba=boxes[a.name];bb=boxes[b.name]
 if all(min(ba[1][i],bb[1][i])-max(ba[0][i],bb[0][i])>0 for i in range(3)):
  pairs=trees[a.name].overlap(trees[b.name])
  if pairs:result['cushion_intersections'].append({'a':a.name,'b':b.name,'overlap_pairs':len(pairs)})
result['mirror_cap_normal_max_degrees']=0
for o in scene.objects:
 if o.name.startswith('mirror_cluster__mirror_'):
  me=o.data
  for p in me.polygons:
   if len(p.vertices)>4:
    for idx in p.loop_indices:result['mirror_cap_normal_max_degrees']=max(result['mirror_cap_normal_max_degrees'],math.degrees(math.acos(max(-1,min(1,me.corner_normals[idx].vector.dot(p.normal))))))
records=json.load(open(O/'objects.json'))['objects'];byid={r['id']:r for r in records};result['support_gaps_m']={}
for r in records:
 for rel in r.get('spatial_relations',[]):
  if rel['relation']=='supported_by' and rel['target'] in byid:result['support_gaps_m'][r['id']]=r['bounds_model_m']['min'][2]-byid[rel['target']]['bounds_model_m']['max'][2]
result['passage_collider']=next(c for c in json.load(open(O/'colliders.json'))['colliders'] if c['object_id']=='door_side_0')
result['actual_render_settings']={'engine':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'threads':scene.render.threads,'unit_scale':scene.unit_settings.scale_length};
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'scene.glb'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];result['glb_import']={'status':'PASS' if len(meshes)==1664 else 'CHECK','mesh_objects':len(meshes),'names_match_records':set(o.name for o in meshes)==set(n for r in records for n in r['component_names'])}
json.dump(result,open(O/'independent_review/final_targeted_checks.json','w'),indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['support_gaps_m','passage_collider']},indent=2))
