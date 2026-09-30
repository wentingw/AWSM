"""Bounded read-only v2 checks on delivered geometry; no model mutation/render."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'))
sc=bpy.context.scene;dep=bpy.context.evaluated_depsgraph_get()
cols=json.loads((R/'colliders.json').read_text())['colliders'];cols={r['object_id']:r for r in cols}
raychecks=[];wall_checks=[]
for wall,x,y,kind in [('wall_east_main',7.35,4.8,'open passage'),('wall_east_main',7.35,11.3,'closed door'),('wall_east_recess',8.8,14.6,'closed door'),('wall_east_recess',8.8,16.35,'closed door')]:
 for dy in [-.4,0,.4]:
  hit,loc,n,ix,obj,mat=sc.ray_cast(dep,Vector((x-.4,y+dy,1)),Vector((1,0,0)),distance=.7)
  raychecks.append({'wall':wall,'y':y+dy,'kind':kind,'hit':obj.name if hit else None})
  occupied=[]
  for part in cols[wall]['parts']:
   lo=part['bounds']['min'];hi=part['bounds']['max']
   if lo[0]<x<hi[0] and lo[1]<y+dy<hi[1] and lo[2]<1<hi[2]:occupied.append(part['component_name'])
  wall_checks.append({'wall':wall,'y':y+dy,'occupied_by_wall_colliders':occupied})
seats=[o for o in sc.objects if o.name.endswith('__seat_cushion')];overlap=[]
for j,a in enumerate(seats):
 for b in seats[j+1:]:
  d=math.hypot(a.location.x-b.location.x,a.location.y-b.location.y);over=a.dimensions.x/2+b.dimensions.x/2-d
  if over>1e-4:overlap.append({'a':a.name,'b':b.name,'penetration':over})
support={}
for name in ['table_north','table_south']:
 low=min((o.matrix_world@Vector(v)).z for o in sc.objects if o.get('semantic_id')==name for v in o.bound_box)
 support[name]={'lowest_z':low,'floor_top_z':.012,'gap':low-.012}
report={'scene_sha256':hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),'door_rays':raychecks,'wall_collider_occupancy':wall_checks,'circular_cushion_overlaps':overlap,'table_support':support,'limitations':'Targeted geometry checks only; no exhaustive collisions or independent metric validation.','render_attempts':0}
(R/'checks/targeted_repairs_v2.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
