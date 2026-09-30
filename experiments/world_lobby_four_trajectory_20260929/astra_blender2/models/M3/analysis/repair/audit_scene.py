import bpy,bmesh,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'));scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();rows=[];bad=[]
for ob in scene.objects:
 if ob.type!='MESH':continue
 ev=ob.evaluated_get(deps);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 row=dict(name=ob.name,winding=sum(e.is_manifold and not e.is_contiguous for e in bm.edges),boundary=sum(e.is_boundary for e in bm.edges),zero_area=sum(f.calc_area()<1e-12 for f in bm.faces),volume=bm.calc_volume(signed=True))
 if 'curved_back' in ob.name or 'reception_desk' in ob.name:rows.append(row)
 if row['winding'] or (row['boundary']==0 and row['volume']< -1e-8):bad.append(row)
 bm.free();ev.to_mesh_clear()
seats=[o for o in scene.objects if o.name.endswith('__seat')];penetrations=[]
for j,a in enumerate(seats):
 for b in seats[:j]:
  overlap=(a.dimensions.x+b.dimensions.x)/2-(a.location.xy-b.location.xy).length
  if overlap>.001:penetrations.append([a.name,b.name,overlap])
col=scene.objects['window_column__shaft'];pot=scene.objects['window_grass_middle__ceramic_pot'];inside=[]
for v in pot.data.vertices:
 p=pot.matrix_world@v.co;dep=col.dimensions.x/2-(p.xy-col.location.xy).length
 if dep>0:inside.append(dep)
ca=json.loads((R/'cameras.json').read_text());pa=json.loads((R.parents[1]/'inputs/M3/packet.json').read_text());X=np.array(json.loads((R/'layout.json').read_text())['model_from_input']);errs=[];pr=[]
for f,g in zip(ca['frames'],pa['frames']):
 errs.append(float(np.max(np.abs(np.array(f['camera_to_world'])-X@np.array(g['camera_to_world'])))))
 ob=scene.objects['native_'+str(f['sample_index']).zfill(4)];T=np.array(f['camera_to_world']);K=np.array(f['intrinsics'],float);K[:2]*=.5
 for u,v in [(80.5,70.5),(320.5,240.5),(550.5,400.5)]:
  pc=np.linalg.inv(K)@np.array([u,v,1])*3;pw=T[:3,:3]@pc+T[:3,3];n=world_to_camera_view(scene,ob,Vector(pw));pr.append(max(abs(n.x*640-u),abs((1-n.y)*480-v)))
coll=json.loads((R/'colliders.json').read_text())['colliders'];portal=next(c for c in coll if c['id']=='mirror_partition');blocks=[]
for c in portal['parts']:
 if c['shape']!='aabb':continue
 lo,hi=np.array(c['bounds']);
 if min(hi[0],.45)-max(lo[0],-.6)>1e-5 and min(hi[2],2.25)-max(lo[2],0)>1e-5:blocks.append(c)
pl=scene.objects['reception_desk__concealed_plinth'];base=min((pl.matrix_world@Vector(v)).z for v in pl.bound_box)
report=dict(author_validation=True,independent_review=False,model_sha256=hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),repaired_topology=rows,bad_winding_all_meshes=bad,seat_penetrations=penetrations,pot_vertices_inside_column=len(inside),max_pot_intrusion=max(inside,default=0),desk_plinth_bottom_z=base,desk_floor_gap_m=base-.018,portal_blocking_parts=blocks,cameras_exact_max_error=max(errs),saved_camera_max_projection_error_px=max(pr),camera_count=len(ca['frames']),threads=scene.render.threads,samples=scene.cycles.samples)
(R/f"checks/author_scene_audit_v{json.loads((R/'layout.json').read_text())['version']}.json").write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
