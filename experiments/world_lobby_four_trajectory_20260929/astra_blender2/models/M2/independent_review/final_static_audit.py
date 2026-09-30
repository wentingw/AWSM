"""Independent read-only artifact audit; no render, BVH, or model writes."""
import json, hashlib, collections
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent.parent
read=[]
def get(p):
 p=R/p;read.append(str(p));return json.loads(p.read_text())
obj=get('objects.json')['objects']; cameras=get('cameras.json'); rods=get('analysis/rod_requests.json');col=get('colliders.json')
read.append(str(R/'scene.blend'));bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'))
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get(); meshes={}; points={}; negative=[];degen=[];badnorm=[];closed=0
for o in sc.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);m=ev.to_mesh();m.calc_loop_triangles()
 v=np.array([ev.matrix_world@x.co for x in m.vertices],dtype=float);f=np.array([t.vertices for t in m.loop_triangles]);t=v[f];a=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
 edge=collections.Counter(tuple(sorted((int(x),int(y)))) for tri in f for x,y in zip(tri,np.roll(tri,-1)))
 shut=all(n==2 for n in edge.values());local=t-v.mean(0);volume=float(np.einsum('ij,ij->i',local[:,0],np.cross(local[:,1],local[:,2])).sum()/6)
 normals=np.array([p.normal[:] for p in m.polygons]);bad=not np.isfinite(normals).all() or bool(np.any(np.linalg.norm(normals,axis=1)<.9))
 rec={'bounds':[v.min(0).tolist(),v.max(0).tolist()],'triangles':len(f),'finite':bool(np.isfinite(v).all()),'closed':shut,'signed_volume_m3':volume,'near_zero_triangles':int((a<1e-12).sum()),'bad_normals':bad,'semantic_id':o.get('semantic_id'),'hide_render':o.hide_render}
 meshes[o.name]=rec;points[o.name]=v
 if shut:closed+=1
 if shut and volume<=0:negative.append(o.name)
 if rec['near_zero_triangles']:degen.append(o.name)
 if bad:badnorm.append(o.name)
 ev.to_mesh_clear()
components=[n for r in obj for n in r['component_names']]
mapping={'object_count':len(obj),'unique_ids':len({r['id'] for r in obj})==len(obj),'components_once':len(set(components))==len(components),'exact_mesh_set':set(components)==set(meshes),'semantic_property_errors':[n for r in obj for n in r['component_names'] if meshes[n]['semantic_id']!=r['id']]}
rr=[]
for r in rods:
 o=bpy.data.objects[r['name']];z=[v.co.z for v in o.data.vertices];ends=np.array([o.matrix_world@Vector((0,0,h)) for h in [min(z),max(z)]]);target=np.array([r['a'],r['b']]);err=min(np.linalg.norm(ends-target,axis=1).max(),np.linalg.norm(ends-target[::-1],axis=1).max());rr.append({'name':r['name'],'error_m':float(err)})
def hull(v):
 p=sorted(set(map(tuple,v)))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lower=[];upper=[]
 for x in p:
  while len(lower)>=2 and cross(lower[-2],lower[-1],x)<=0:lower.pop()
  lower.append(x)
 for x in p[::-1]:
  while len(upper)>=2 and cross(upper[-2],upper[-1],x)<=0:upper.pop()
  upper.append(x)
 return np.array(lower[:-1]+upper[:-1])
def separation(a,b):
 gaps=[]
 for p in [a,b]:
  for u,v in zip(p,np.roll(p,-1,axis=0)):
   n=np.array([-(v-u)[1],(v-u)[0]]);n/=np.linalg.norm(n);pa=a@n;pb=b@n;gaps.append(max(pb.min()-pa.max(),pa.min()-pb.max()))
 return max(gaps)
bases={n:hull(v[:,:2]) for n,v in points.items() if n.endswith('__upholstered_base')};pairs=[]
names=sorted(bases)
for j,n in enumerate(names):
 for m in names[j+1:]:pairs.append({'a':n,'b':m,'separating_gap_m':float(separation(bases[n],bases[m]))})
portal=col['portals'][0];lo=np.array([portal['plane_x']-.3,portal['y_range'][0]+.025,portal['z_range'][0]+.025]);hi=np.array([portal['plane_x']+.4,portal['y_range'][1]-.025,portal['z_range'][1]-.025])
def overlap(b):return bool(np.all(np.minimum(hi,b[1])-np.maximum(lo,b[0])>1e-6))
portalcheck={'test_box':[lo.tolist(),hi.tolist()],'mesh_AABB_intersections':[n for n,m in meshes.items() if overlap(np.array(m['bounds']))],'collider_intersections':[r.get('component') or r['id'] for r in col['colliders'] if r['type']=='AABB' and overlap(np.array(r['bounds']))],'nominal_clearance_m':[portal['clear_width_m'],portal['clear_height_m']],'bounded_depth_m':portal['bounded_vestibule_depth_m']}
support=[]
floor=meshes['floor__slab']['bounds'][1][2]
for r in obj:
 if r['category'] in ['lounge_chair','ottoman','coffee_table','reception_desk','flowering_planter','plant_and_planter','potted_tree','floor_lamp','column']:
  low=min(meshes[n]['bounds'][0][2] for n in r['component_names']);support.append({'id':r['id'],'min_z_m':low,'relative_to_floor_m':low-floor})
cam=sc.camera;K=np.array(cameras['frames'][33]['intrinsics']);T=np.array(cameras['frames'][33]['camera_to_world']);probes=[]
for u,v in [(30,40),(640,480),(1200,900)]:
 xyz=T@np.array([(u-K[0,2])/K[0,0]*3,(v-K[1,2])/K[1,1]*3,3,1]);q=world_to_camera_view(sc,cam,Vector(xyz[:3]));probes.append(float(np.linalg.norm([q.x*1280-u,(1-q.y)*960-v])))
out={'model_sha256':hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),'mesh_count':len(meshes),'triangles':sum(m['triangles'] for m in meshes.values()),'closed_count':closed,'negative_closed':negative,'degenerate_components':degen,'bad_normal_components':badnorm,'semantic_mapping':mapping,'rod_count':len(rr),'max_rod_endpoint_error_m':max(r['error_m'] for r in rr),'rod_examples':[r for r in rr if r['name'] in ['pendant_00__radial_0','wall_emblem__horn_horizontal_1','coffee_table_far__rib_00','floor_lamp_0__leg_1','plant_below_mirrors__stem_00']],'seat_pair_checks':pairs,'minimum_seat_base_separating_gap_m':min(p['separating_gap_m'] for p in pairs),'portal':portalcheck,'support_bounds':support,'camera':{'name':cam.name,'max_projection_error_px':max(probes),'matrix_error':float(np.max(np.abs(np.array(cam.matrix_world)-T@np.diag([1,-1,-1,1]))))},'units':{'system':sc.unit_settings.system,'scale_length':sc.unit_settings.scale_length,'length_unit':sc.unit_settings.length_unit},'meshes':meshes,'paths_read':read,'scope':'Static mesh/topology/endpoint/convex-separation/AABB/projection checks only. No renders, no raycasts, no physics simulation.'}
(R/'independent_review/final_blender_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['meshes','seat_pair_checks','support_bounds','paths_read']},indent=2))
