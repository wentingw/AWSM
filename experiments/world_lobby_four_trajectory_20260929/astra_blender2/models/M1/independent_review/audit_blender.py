"""Read-only geometry, topology, units and projection inspection; no rendering/BVH."""
import json, hashlib
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent.parent;O=R/'independent_review'
bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'))
scene=bpy.context.scene; deps=bpy.context.evaluated_depsgraph_get()
report={'model_sha256':hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),'units':{'system':scene.unit_settings.system,'scale_length':scene.unit_settings.scale_length},'meshes':[]}
for obj in scene.objects:
    if obj.type!='MESH': continue
    ev=obj.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles()
    bm=bmesh.new();bm.from_mesh(m)
    closed=all(e.is_manifold for e in bm.edges)
    row={'name':obj.name,'semantic_id':obj.get('semantic_id'),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_nonboundary_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'noncontiguous_manifold_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'closed_manifold':closed,'signed_volume_local':bm.calc_volume(signed=True) if closed else None,'degenerate_faces':sum(p.area<1e-12 for p in m.polygons),'finite_normals':bool(np.isfinite(np.array([list(p.normal) for p in m.polygons])).all()),'negative_world_determinant':obj.matrix_world.to_3x3().determinant()<0}
    report['meshes'].append(row);bm.free();ev.to_mesh_clear()
frames=json.loads((R/'cameras.json').read_text())['frames']; by={f['sample_index']:f for f in frames}
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
d=bpy.data.cameras.new('review_projection_only');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam
d.type='PERSP';d.sensor_fit='HORIZONTAL';d.sensor_width=36
report['projection_tests']=[]
for i in [33,61,74,82,91,100,108,118,129,155]:
    T=np.array(by[i]['camera_to_world']);K=np.array(by[i]['intrinsics'],float);K[:2]*=.5
    d.lens=K[0,0]*36/640;d.shift_x=(320-K[0,2])/640;d.shift_y=(K[1,2]-240)/640
    cam.matrix_world=Matrix((T@np.diag([1,-1,-1,1])).tolist());bpy.context.view_layer.update();errors=[]
    for u,v in [(80.5,70.5),(320.5,240.5),(550.5,400.5)]:
        pc=np.linalg.inv(K)@np.array([u,v,1])*3;pw=T[:3,:3]@pc+T[:3,3];ndc=world_to_camera_view(scene,cam,Vector(pw))
        errors.append([ndc.x*640-u,(1-ndc.y)*480-v])
    report['projection_tests'].append({'sample_index':i,'max_pixel_error':float(np.max(np.abs(errors)))})
report['summary']={'mesh_count':len(report['meshes']),'closed_manifold_count':sum(x['closed_manifold'] for x in report['meshes']),'negative_volume_closed':[x['name'] for x in report['meshes'] if x['closed_manifold'] and x['signed_volume_local']< -1e-9],'winding_inconsistent':[x['name'] for x in report['meshes'] if x['noncontiguous_manifold_edges']],'degenerate_face_meshes':[{'name':x['name'],'count':x['degenerate_faces']} for x in report['meshes'] if x['degenerate_faces']],'nonfinite_normals':[x['name'] for x in report['meshes'] if not x['finite_normals']],'max_projection_error_pixels':max(x['max_pixel_error'] for x in report['projection_tests'])}
(O/'geometry_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'units':report['units'],'summary':report['summary']},indent=2))
