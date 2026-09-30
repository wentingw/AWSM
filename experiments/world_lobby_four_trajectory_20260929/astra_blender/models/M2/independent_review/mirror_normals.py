import bpy,json,numpy as np
from pathlib import Path
o=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(o.parent/'scene.blend'))
records=[]
for obj in bpy.context.scene.objects:
 if obj.name.startswith('mirror_cluster__mirror_'):
  me=obj.data
  caps=[p for p in me.polygons if len(p.vertices)>4]
  rec={'name':obj.name,'caps':[]}
  for p in caps:
   norms=np.array([me.corner_normals[i].vector[:] for i in p.loop_indices])
   angles=np.degrees(np.arccos(np.clip(norms@np.array(p.normal[:]),-1,1)))
   rec['caps'].append({'smooth':p.use_smooth,'vertices':len(p.vertices),'corner_normal_angle_from_flat_face_degrees':[float(angles.min()),float(angles.max())]})
  records.append(rec)
(o/'mirror_normals.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records[:2],indent=2))

