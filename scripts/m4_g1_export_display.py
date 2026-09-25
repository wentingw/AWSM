"""Export display-only M4 cutaway meshes in the physical episode's Z-up metre frame."""
import bpy,sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'experiments/world_lobby/M4/astra_model/scene.blend';out=ROOT/'experiments/tasks/g1_M4/presentation_20260924';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src));meta=json.loads((src.parent/'objects.json').read_text())['objects'];roots={o['blender_root']:o for o in meta};exclude={'wall','window_wall','door','ceiling','ceiling_decoration','wall_panel','wall_decoration','mirror','pendant_light'}
def owner(o):
 names=[]
 while o:names.append(o.name);o=o.parent
 for n in names:
  if n in roots:return roots[n]
 for n in names:
  for r in sorted(roots,key=len,reverse=True):
   if n.startswith(r+'.') or n.startswith(r+'_'):return roots[r]
 return None
def color(mat):
 if mat is None:return [.65,.65,.65,1.]
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':return [float(v) for v in n.inputs['Base Color'].default_value[:3]]+[1.]
 return list(mat.diffuse_color[:3])+[1.]
groups={};omitted=set();deps=bpy.context.evaluated_depsgraph_get();kept=0
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or not o.visible_get():continue
 semantic=owner(o)
 if semantic and semantic['category'] in exclude:omitted.add(semantic['object_id']);continue
 eo=o.evaluated_get(deps);me=eo.to_mesh();me.calc_loop_triangles();world=np.array(eo.matrix_world);vertices=[(world@np.array([*v.co,1.]))[:3].tolist() for v in me.vertices]
 bymat={}
 for t in me.loop_triangles:
  mat=me.materials[t.material_index] if t.material_index<len(me.materials) else None;key=mat.name if mat else 'default';bymat.setdefault(key,{'mat':mat,'faces':[]})['faces'].append(list(t.vertices))
 for key,m in bymat.items():
  g=groups.setdefault(key,{'vertices':[],'faces':[],'rgba':color(m['mat']),'objects':0});offset=len(g['vertices']);g['vertices'].extend(vertices);g['faces'].extend([[offset+i for i in f] for f in m['faces']]);g['objects']+=1
 eo.to_mesh_clear();kept+=1
manifest=[]
for i,(name,g) in enumerate(sorted(groups.items())):
 p=out/f'visual_{i:03d}.obj'
 with p.open('w') as f:
  f.write('# Frozen M4 display cutaway. World coordinates: Z up, metres.\n')
  for v in g['vertices']:f.write('v '+' '.join(f'{x:.9g}' for x in v)+'\n')
  for tri in g['faces']:f.write('f '+' '.join(str(k+1) for k in tri)+'\n')
 manifest.append({'name':name,'obj':p.name,'rgba':g['rgba'],'objects':g['objects'],'triangles':len(g['faces']),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
report={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'coordinate_frame':'Original M4 world; Z-up; metres; no recentering or rescaling','groups':manifest,'display_only':True,'collision':False,'omitted_objects':sorted(omitted),'omitted_categories':sorted(exclude),'mesh_objects_kept':kept,'triangles':sum(m['triangles'] for m in manifest)};(out/'material_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('DISPLAY_EXPORTED',kept,len(manifest),report['triangles'],len(omitted))
