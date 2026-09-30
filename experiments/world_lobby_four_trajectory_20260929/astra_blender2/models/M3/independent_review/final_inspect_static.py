"""Read-only mesh/camera inspection; no render or BVH."""
import bpy,bmesh,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent.parent;O=R/'independent_review'
bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'))
scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();rows=[];bad=[]
for obj in scene.objects:
 if obj.type!='MESH':continue
 ev=obj.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 inconsistent=sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
 boundary=sum(1 for e in bm.edges if e.is_boundary)
 area_zero=sum(1 for f in bm.faces if f.calc_area()<1e-12)
 vol=bm.calc_volume(signed=True)
 r={'name':obj.name,'inconsistent_winding_edges':inconsistent,'boundary_edges':boundary,'zero_area_faces':area_zero,'signed_volume_local':vol,'semantic_id':obj.get('semantic_id')}
 rows.append(r)
 if inconsistent or (boundary==0 and vol< -1e-9):bad.append(r)
 bm.free();ev.to_mesh_clear()
objects=json.loads((R/'objects.json').read_text())['objects'];meshmap={o.name:o for o in scene.objects if o.type=='MESH'}
bounds={o.name:np.array([o.matrix_world@Vector(v) for v in o.bound_box]) for o in meshmap.values()}
physical={}
# Exact primitive circular seat/column overlap, not AABB collision assertion.
circles=[]
for o in scene.objects:
 if o.type=='MESH' and (o.name.endswith('__seat') or o.name=='window_column__shaft'):
  p=bounds[o.name];circles.append((o.name,np.array(o.location[:2]),float(o.dimensions.x/2),float(p[:,2].min()),float(p[:,2].max())))
overlap=[]
for j,a in enumerate(circles):
 for b in circles[j+1:]:
  dep=a[2]+b[2]-np.linalg.norm(a[1]-b[1]);height=min(a[4],b[4])-max(a[3],b[3])
  if dep>.005 and height>.005:overlap.append({'a':a[0],'b':b[0],'radial_overlap_m':float(dep),'vertical_overlap_m':float(height)})
physical['circular_solid_penetrations']=overlap
physical['desk_bottom_z']=float(bounds['reception_desk__faceted_shell'][:,2].min())
physical['desk_floor_gap_m']=physical['desk_bottom_z']-.018
physical['crest_shield_normal']=list(meshmap['wall_crest__shield'].data.polygons[0].normal)
physical['mirror_flat_cap_normal_examples']={}
for name in ['wall_mirror_0__reflective_disc','wall_mirror_1__reflective_disc']:
 ob=meshmap[name];caps=[p for p in ob.data.polygons if len(p.vertices)>10];physical['mirror_flat_cap_normal_examples'][name]=[{'verts':len(p.vertices),'smooth':p.use_smooth,'normal':list(p.normal)} for p in caps]
physical['portal_proxies']=[c for c in json.loads((R/'colliders.json').read_text())['colliders'] if c['id'] in ['mirror_partition','recess_wall','glazed_facade','entry_double_door_0','entry_double_door_1']]
physical['doorway_core_bounds']={name:[p.min(0).tolist(),p.max(0).tolist()] for name,p in bounds.items() if name.startswith('mirror_partition__core')}
# Check saved cameras against cameras.json and actual Blender projection, no rendering.
camrecords=json.loads((R/'cameras.json').read_text())['frames'];diff=[];proj=[]
for f in camrecords:
 ob=scene.objects['native_'+str(f['sample_index']).zfill(4)];want=np.array(f['camera_to_world'])@np.diag([1,-1,-1,1]);diff.append(float(np.max(np.abs(np.array(ob.matrix_world)-want))))
 if f['sample_index'] in [33,61,74,82,91,100,108,118,129,155]:
  T=np.array(f['camera_to_world']);K=np.array(f['intrinsics'],float);K[:2]*=.5
  for u,v in [(80.5,70.5),(320.5,240.5),(550.5,400.5)]:
   pc=np.linalg.inv(K)@np.array([u,v,1])*3;pw=T[:3,:3]@pc+T[:3,3];ndc=world_to_camera_view(scene,ob,Vector(pw));proj.append(max(abs(ndc.x*640-u),abs((1-ndc.y)*480-v)))
out={'model_sha256':hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),'unit_settings':{'system':scene.unit_settings.system,'scale_length':scene.unit_settings.scale_length},'mesh_count':len(rows),'normals':{'bad_winding':bad,'all_meshes':rows},'physical':physical,'camera':{'saved_camera_max_matrix_error':max(diff),'fixed_camera_max_projection_error_px':max(proj),'resolution':[scene.render.resolution_x,scene.render.resolution_y],'resolution_percentage':scene.render.resolution_percentage},'paths_read':[str(R/x) for x in ['scene.blend','objects.json','colliders.json','cameras.json']]}
# Additional final checks; no scene mutation, render, or BVH.
physical['repaired_topology']=[r for r in rows if 'curved_back' in r['name'] or 'reception_desk' in r['name']]
col=meshmap['window_column__shaft'];pot=meshmap['window_grass_middle__ceramic_pot'];intrusions=[]
for v in pot.data.vertices:
 p=pot.matrix_world@v.co;dep=col.dimensions.x/2-(p.xy-col.location.xy).length
 if dep>0:intrusions.append(float(dep))
physical['pot_column']={'inside_vertices':len(intrusions),'max_radial_intrusion_m':max(intrusions,default=0)}
physical['desk_support_bounds']=[bounds['reception_desk__concealed_plinth'].min(0).tolist(),bounds['reception_desk__concealed_plinth'].max(0).tolist()]
physical['desk_support_floor_gap_m']=float(bounds['reception_desk__concealed_plinth'][:,2].min()-.018)
physical['desk_shell_support_overlap_z_m']=float(bounds['reception_desk__concealed_plinth'][:,2].max()-bounds['reception_desk__faceted_shell'][:,2].min())
colliders=json.loads((R/'colliders.json').read_text())['colliders'];parts=[]
for c in colliders:
 for part in c.get('parts',[c]):
  if 'bounds' in part:parts.append((c['id'],part))
physical['portal_point_blocks']=[]
for x in [-.55,-.075,.40]:
 for z in [.1,1.,2.2]:
  for y in np.linspace(-5.9,-3.8,16):
   p=np.array([x,y,z])
   for ident,part in parts:
    lo,hi=np.array(part['bounds'])
    if np.all(p>lo+1e-5) and np.all(p<hi-1e-5):physical['portal_point_blocks'].append({'id':ident,'point':p.tolist()})
physical['flat_cap_checks']={}
for name,o in meshmap.items():
 if 'reflective_disc' in name or name.endswith('__top'):
  physical['flat_cap_checks'][name]=[p.use_smooth for p in o.data.polygons if len(p.vertices)>10]
out['semantic_property_mismatches']=[o.name for o in meshmap.values() if o.get('semantic_id')!=o.name.split('__')[0]]
out['normal_zero_area_meshes']=[r for r in rows if r['zero_area_faces']]
(O/'final_static_inspection.json').write_text(json.dumps(out,indent=2)+'\n')
print('STATIC_CHECK',json.dumps({k:v for k,v in out.items() if k not in ['normals','physical','paths_read']}));print('BAD_WINDING',json.dumps(bad));print('PHYSICAL',json.dumps(physical))
