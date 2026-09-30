import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
from pathlib import Path
import json,hashlib,numpy as np,trimesh
R=Path(__file__).parent;s=trimesh.load(R/'scene.glb',force='scene',process=False);a=json.loads((R/'checks/author_geometry_audit.json').read_text());rows=[];bad=[]
for node in s.graph.nodes_geometry:
 T,name=s.graph[node];m=s.geometry[name].copy();m.apply_transform(T);mm=m.copy();mm.merge_vertices(merge_tex=True,merge_norm=True);area=m.area_faces;v=float(m.volume);closed=mm.is_watertight
 r={'node':node,'geometry':name,'closed_after_position_weld':closed,'signed_volume_m3':v,'min_triangle_area_m2':float(area.min()),'near_zero_triangles':int((area<1e-12).sum()),'finite_normals':bool(np.isfinite(m.vertex_normals).all())};rows.append(r)
 if r['near_zero_triangles'] or ((closed or a['meshes'][node]['closed']) and v<=0) or not r['finite_normals']:bad.append(r)
blender_mesh_names=set(a['meshes']);gltf_nodes={r['node'] for r in rows};report={'role':'author artifact validation; not independent review','glb_sha256':hashlib.sha256((R/'scene.glb').read_bytes()).hexdigest(),'status':'PASS' if not bad and gltf_nodes==blender_mesh_names else 'FAIL','issues':bad,'node_set_equals_blender_meshes':gltf_nodes==blender_mesh_names,'mesh_count':len(rows),'closed_count':sum(r['closed_after_position_weld'] for r in rows),'meshes':rows};(R/'checks/author_glb_geometry_audit.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='meshes'})
assert report['status']=='PASS'
