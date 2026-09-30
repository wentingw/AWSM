import bpy,bmesh,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'));bad=[];targets=[];opens=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);closed=all(e.is_manifold for e in bm.edges);winding=sum(e.is_manifold and not e.is_contiguous for e in bm.edges);vol=bm.calc_volume(signed=True) if closed else None;bm.free();o.data.calc_loop_triangles();deg=0
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[j].co for j in t.vertices]
  if (b-a).cross(c-a).length*.5<1e-12:deg+=1
 if not closed:opens.append(o.name)
 if winding or deg or (closed and vol<=0):bad.append(dict(name=o.name,winding=winding,degenerate=deg,volume=vol))
 if o.name=='reception_desk__faceted_body' or '__curved_back' in o.name:targets.append(dict(name=o.name,closed=closed,signed_volume_m3=vol,inconsistent_edges=winding,degenerate_triangles=deg))
report=dict(role='AUTHOR read-only reload validation, not independent review',model_sha256=hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),issues=bad,review_blocker_components=targets,intentional_open_leaf_components=opens)
(R/'checks/saved_mesh_validation.json').write_text(json.dumps(report,indent=2));assert not bad,bad
print('SAVED_MESH_VALIDATION_PASS',len(targets),flush=True)
