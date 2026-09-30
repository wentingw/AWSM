import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import numpy as np,trimesh,json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];version=int(sys.argv[1]);s=trimesh.load(R/'scene.glb',force='scene',process=False);rows=[];nonfinite=[]
for node in s.graph.nodes_geometry:
 T,key=s.graph[node];m=s.geometry[key]
 if not np.isfinite(m.vertices).all() or not np.isfinite(m.vertex_normals).all():nonfinite.append(node)
 if 'curved_back' not in node and 'reception_desk' not in node:continue
 m=m.copy();m.merge_vertices(merge_tex=True,merge_norm=True);edges={}
 for tri in m.faces:
  for a,b in zip(tri,np.roll(tri,-1)):
   k=tuple(sorted([int(a),int(b)]));edges.setdefault(k,[]).append((int(a),int(b)))
 bad=sum(len(es)==2 and es[0]==es[1] for es in edges.values());boundary=sum(len(es)==1 for es in edges.values());zero=int((m.area_faces<1e-12).sum())
 rows.append(dict(component_name=node,winding_edges=bad,boundary_edges=boundary,degenerate_triangles=zero,watertight=bool(m.is_watertight),volume=float(m.volume)))
out=dict(version=version,author_validation=True,independent_review=False,glb_sha256=hashlib.sha256((R/'scene.glb').read_bytes()).hexdigest(),geometry_count=len(s.geometry),nonfinite_components=nonfinite,selected_topology=rows)
(R/f'checks/author_glb_audit_v{version}.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
