"""Generic read-only Blender artifact inspection."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.wm.open_mainfile(filepath=a.model);records=[];missing=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        pts=np.array([ev.matrix_world@v.co for v in mesh.vertices]);assert np.isfinite(pts).all(),obj.name
        bounds=[pts.min(0).tolist(),pts.max(0).tolist()] if len(pts) else None
        records.append({'name':obj.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'bounds':bounds,'hide_render':obj.hide_render,'materials':[s.material.name if s.material else None for s in obj.material_slots]})
        ev.to_mesh_clear()
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file and image.filepath:
            path=Path(bpy.path.abspath(image.filepath))
            if not path.exists():missing.append(str(path))
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'status':'PASS' if records and not missing else 'FAIL','model_sha256':hashlib.sha256(Path(a.model).read_bytes()).hexdigest(),'mesh_objects':len(records),'triangles':sum(r['triangles'] for r in records),'missing_image_dependencies':missing,'meshes':records},indent=2)+'\n')
    assert records and not missing
    print('SCENE_INSPECTION_PASS',len(records),sum(r['triangles'] for r in records))
if __name__=='__main__':main()
