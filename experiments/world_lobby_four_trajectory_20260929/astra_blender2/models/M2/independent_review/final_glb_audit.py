import json,struct,hashlib
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parent.parent
raw=(R/'scene.glb').read_bytes();n,kind=struct.unpack('<II',raw[12:20]);g=json.loads(raw[20:20+n]);s=trimesh.load(R/'scene.glb',force='scene',process=False)
bl=json.loads((R/'independent_review/final_blender_audit.json').read_text());obj=json.loads((R/'objects.json').read_text())['objects'];col=json.loads((R/'colliders.json').read_text());errors=[];closed=0;records=[]
if raw[:4]!=b'glTF' or struct.unpack('<I',raw[8:12])[0]!=len(raw):errors.append('GLB header/length')
external=[x['uri'] for k in ['buffers','images'] for x in g.get(k,[]) if 'uri' in x and not x['uri'].startswith('data:')]
if external:errors.append('external resources')
convert=np.array([[1,0,0],[0,0,-1],[0,1,0]])
for node in s.graph.nodes_geometry:
 trans,geo=s.graph[node];m=s.geometry[geo].copy();m.apply_transform(trans);verts=np.asarray(m.vertices)@convert.T;bounds=np.array([verts.min(0),verts.max(0)]);m.merge_vertices(merge_tex=True,merge_norm=True);shut=bool(m.is_watertight)
 if shut:closed+=1
 delta=float(np.max(np.abs(bounds-np.array(bl['meshes'][node]['bounds']))));bad=not np.isfinite(m.vertices).all() or not np.isfinite(m.vertex_normals).all()
 if bad or delta>1e-5 or (shut and m.volume<=0) or np.min(m.area_faces)<1e-12:errors.append(node)
 records.append({'node':node,'closed_after_position_weld':shut,'signed_volume_m3':float(m.volume),'minimum_triangle_area_m2':float(m.area_faces.min()),'bounds_difference_m':delta,'finite_vertices_normals':not bad})
expected={n for o in obj for n in o['component_names']};actual={n for n in s.graph.nodes_geometry}
if expected!=actual:errors.append('semantic node set mismatch')
missing_normals=[i for i,m in enumerate(g['meshes']) if any('NORMAL' not in p['attributes'] for p in m['primitives'])]
if missing_normals:errors.append('missing exported normals')
metadata=[]
for o in obj:
 names=o['component_names'];bounds=np.array([bl['meshes'][n]['bounds'] for n in names]);truebounds=np.array([bounds[:,0].min(0),bounds[:,1].max(0)]);delta=float(np.max(np.abs(truebounds-np.array(o['bounds']))))
 if delta>1e-5 or not o['category'] or not o['evidence_frames'] or not o['provenance'] or not o['relations']:metadata.append(o['id'])
for c in col['colliders']:
 if c['type']=='convex_prism':
  node=c['id']+'__upholstered_base';trans,geo=s.graph[node];v=trimesh.transform_points(s.geometry[geo].vertices,trans)@convert.T;poly=np.array(c['polygon_xy']);dist=np.linalg.norm(poly[:,None,:]-v[None,:,:2],axis=2).min(1)
  if dist.max()>1e-5:errors.append('seat collider '+c['id'])
if metadata:errors.append('semantic metadata bounds/fields')
out={'status':'PASS' if not errors else 'FAIL','errors':errors,'glb_sha256':hashlib.sha256(raw).hexdigest(),'mesh_count':len(records),'closed_count':closed,'external_resource_uris':external,'missing_normal_attributes':missing_normals,'semantic_mapping_exact':expected==actual,'metadata_errors':metadata,'maximum_bounds_error_m':max(r['bounds_difference_m'] for r in records),'meshes':records,'paths_read':[str(R/f) for f in ['scene.glb','objects.json','colliders.json','independent_review/final_blender_audit.json']]}
(R/'independent_review/final_glb_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='meshes'},indent=2))
