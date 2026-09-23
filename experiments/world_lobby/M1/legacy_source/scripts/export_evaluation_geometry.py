import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
r=Path(__file__).resolve().parents[1];out=r/'evaluation';out.mkdir(exist_ok=True)
rng=np.random.default_rng(6042);deps=bpy.context.evaluated_depsgraph_get();triangles=[];groups=[];rows=[];names=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.get('render_only'):continue
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=np.array([tuple(e.matrix_world @ p.co) for p in m.vertices]);f=np.array([list(t.vertices) for t in m.loop_triangles])
 if len(f):
  triangles.append(v[f]);groups.extend([len(rows)]*len(f));mn=v.min(0);mx=v.max(0)
  rows.append({'name':o.name,'collection':o.users_collection[0].name,'min':mn.tolist(),'max':mx.tolist(),'center':((mn+mx)/2).tolist(),'dimensions':(mx-mn).tolist()})
 e.to_mesh_clear()
t=np.concatenate(triangles);g=np.array(groups);cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(cross,axis=1)*.5
idx=rng.choice(len(t),size=200000,p=area/area.sum());u=rng.random((len(idx),1));v=rng.random((len(idx),1));u=np.sqrt(u);pts=(1-u)*t[idx,0]+u*(1-v)*t[idx,1]+u*v*t[idx,2]
np.savez_compressed(out/'visual_surface.npz',points=pts.astype('float32'),object_index=g[idx],triangle_count=len(t),surface_area=area.sum())
(out/'visual_objects.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('Exported',len(rows),'objects',len(t),'triangles',len(pts),'sampled surface points')
