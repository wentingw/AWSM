"""Presentation-only cutaways; frozen source scenes remain untouched."""
import bpy,sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'blog/assets';records=[]
for m in ['M2','M3','M4']:
 source=ROOT/f'experiments/world_lobby/{m}/astra_model/scene.blend';bpy.ops.wm.open_mainfile(filepath=str(source));d=json.loads((source.parent/'objects.json').read_text());rows=d if isinstance(d,list) else d['objects'];hide=[]
 for o in rows:
  category=o.get('category','').lower();name=o['object_id'].lower()
  if any(x in category for x in ['wall','window','ceiling','door']) or any(x in name for x in ['mullion','ceiling','cornice']):hide.append(o['object_id'])
 hidden=[];selected=[]
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  parents=[];q=o
  while q:parents.append(q.name);q=q.parent
  omit=any(any(n==h or n.startswith(h+'.') or n.startswith(h+'_') for n in parents) for h in hide)
  if omit:hidden.append(o.name)
  else:o.select_set(True);selected.append(o.name)
 path=out/f'{m}_cutaway.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False);records.append({'method':m,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'asset':path.name,'asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'hidden_for_presentation_only':hidden,'retained_meshes':len(selected),'note':'Walls/windows/doors/ceiling removed in this display copy only. Not used for evaluation or physics.'});print('EXPORTED',m,len(hidden),len(selected),flush=True)
(out/'cutaway_provenance.json').write_text(json.dumps(records,indent=2)+'\n')
