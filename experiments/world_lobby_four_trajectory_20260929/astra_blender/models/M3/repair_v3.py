"""Bounded v3 edit applied once to the supplied own-method v1 script."""
from pathlib import Path
import hashlib
p=Path('build_scene.py'); s=p.read_text()
assert hashlib.sha256(p.read_bytes()).hexdigest()=='dc59de10086aee312b0dbf865b742c9bcc9c55e3cc516649089303c069c93459'
Path('build_scene_v1_reference.py').write_text(s)
s=s.replace('VERSION=1','VERSION=3')
s=s.replace("bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)","bpy.ops.wm.read_factory_settings(use_empty=True)")
# Direct mesh construction avoids thousands of context-dependent operators.
a=s.index('def box('); b=s.index('\ndef mesh(',a)
s=s[:a]+'''def box(name,loc,dims,ma,bevel=0):
 v=[(i*dims[0]/2,j*dims[1]/2,k*dims[2]/2) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 o=mesh(name,v,[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)],ma);o.location=loc
 if bevel:
  mod=o.modifiers.new('softened manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
  o.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 return o
def cyl(name,loc,r,depth,ma,verts=48,bevel=0):
 v=[(r*math.cos(math.tau*i/verts),r*math.sin(math.tau*i/verts),z) for z in [-depth/2,depth/2] for i in range(verts)]
 f=[tuple(reversed(range(verts))),tuple(range(verts,2*verts))]+[(i,(i+1)%verts,(i+1)%verts+verts,i+verts) for i in range(verts)]
 o=mesh(name,v,f,ma);o.location=loc
 for q in o.data.polygons:q.use_smooth=len(q.vertices)==4
 if bevel:
  mod=o.modifiers.new('softened manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
  o.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 return o
''' +s[b:]
# Cut actual substrate AND panels at all framed door locations, preserving closed leaves separately.
a=s.index('def wall_y('); b=s.index("wall_x('far_end_wall'",a)
s=s[:a]+'''def wall_y(id,y,x0,x1,openings=[]):
 group(id,'wall',[45,60,72,90],'Timber-clad wall with substrate and panels cut around framed door apertures',.22)
 records[id]['door_apertures']=[{'x':[a,b],'z':[0,1.90]} for a,b in openings]
 cursor=x0
 for n,(a,b) in enumerate(openings+[(x1,x1)]):
  if a>cursor:box(f'substrate_pier_{n}',((cursor+a)/2,y-.1,2.5),(a-cursor,.18,5),seam)
  if b>a:box(f'substrate_header_{n}',((a+b)/2,y-.1,3.45),(b-a,.18,3.10),seam)
  cursor=b
 for n,x in enumerate(np.arange(x0,x1,.8)):
  right=min(x+.8,x1)
  for h,(z0,z1) in enumerate([(0,1.85),(1.85,1.90),(1.90,3.7),(3.7,5)]):
   spans=[(x,right)]
   if z0<1.90:
    for a,b in openings:
     spans=[piece for l,r in spans for piece in ([(l,min(r,a))] if l<a else [])+([(max(l,b),r)] if r>b else []) if piece[1]-piece[0]>.013]
   for k,(l,r) in enumerate(spans):
    box(f'panel_{n:02}_{h}_{k}',((l+r)/2,y+.006,(z0+z1)/2),(r-l-.012,.045,z1-z0-.012),oak)
''' +s[b:]
s=s.replace("[(1.55,2.5),(8.75,9.6)]","[(1.55,2.55),(8.67,9.57)]")
s=s.replace("[(11.1,12.05),(13.65,14.6),(16.2,17.15)]","[(11.15,12.05),(13.67,14.57),(16.2,17.1)]")
a=s.index(' group(f\'interior_door_');b=s.index('# window curtain wall',a)
s=s[:a]+''' group(f'interior_door_{idx:02}','door',[45,60,72,90],'Open passage beside near end of mirror cluster' if idx==0 else 'Closed flush metal interior door; no open passage claimed',.25)
 records[active]['door_state']='open_passage_no_visible_leaf' if idx==0 else 'closed'
 records[active]['door_state_confidence']='medium' if idx in [0,2,3,4] else 'high'
 records[active]['door_state_evidence']='RGB 72 exposes floor continuation and dark return through near mirror-side aperture; no leaf angle can be reliably measured.' if idx==0 else 'RGB 45/60/72 shows flush reflective facade; recess doors partly occluded, retained closed with uncertainty.'
 width=1.0 if idx==0 else .9
 if idx!=0:box('leaf',(x,y,.935),(.8,.05,1.87),silver,.008)
 box('head',(x,y+.032,1.88),(width,.045,.035),silver)
 for side in [-1,1]:box('jamb_'+str(side),(x+side*(width/2-.02),y-.10,.94),(.035,.25,1.88),silver)
 if idx!=0:rod('pull',(x-.28,y+.08,.81),(x-.28,y+.08,1.03),.012,silver)
''' +s[b:]
# Partition overlapping cushion footprints with a small seam, keeping v1 centers and outside arcs.
a=s.index('# seating functions');b=s.index('def table(',a)
s=s[:a]+'''# Seating retains original anchors and heights. Partition intersecting circular silhouettes
# into separate upholstered modules with a 12 mm seam, including the curved backs.
far_seats=[(7.95,5.15,.45,False,0),(8.7,5.22,.45,True,1.4),(9.25,4.65,.45,True,1.0),(9.56,4.10,.49,False,0),(9.05,3.73,.47,False,0),(8.77,3.15,.45,True,-1.1)]
near_seats=[(5.5,2.77,.46,False,0),(4.75,2.79,.43,True,-1.6),(4.2,3.16,.46,True,-2.1),(4.25,4.05,.44,False,0)]
seat_measurements=[]
def clip_module(poly,x,y,others):
 for xx,yy,*_ in others:
  delta=np.array([xx-x,yy-y]);d=float(np.linalg.norm(delta))
  if d<1e-6:continue
  normal=delta/d;offset=float(normal@np.array([(xx+x)/2,(yy+y)/2]))-.006
  result=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   da=float(normal@np.array(a))-offset;db=float(normal@np.array(b))-offset
   if da<=0:result.append(a)
   if (da<=0)!=(db<=0):result.append(tuple(np.array(a)+(np.array(b)-a)*(da/(da-db))))
  poly=result
  if not poly:break
 return poly

def prism(name,poly,z0,z1,ma,bevel):
 n=len(poly);assert n>=3
 # Ensure CCW footprint; annular backrest footprint is concave but simple.
 area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
 if area<0:poly=list(reversed(poly))
 vs=[(x,y,z) for z in [z0,z1] for x,y in poly]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh(name,vs,fs,ma)
 mod=o.modifiers.new('upholstered edge','BEVEL');mod.width=bevel;mod.segments=3
 o.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 return o

def chair(id,x,y,r,back,angle,others,evidence):
 group(id,'lounge_chair' if back else 'ottoman',evidence,'Separate rounded upholstered module; clipped contact sides inferred from distinct scalloped RGB silhouettes',.16,[{'relation':'supported_by','target':'floor'}])
 poly=clip_module([(x+r*math.cos(a),y+r*math.sin(a)) for a in np.linspace(0,math.tau,48,endpoint=False)],x,y,others)
 prism('seat',poly,.08,.51,fabric,.035)
 seat_measurements.append({'id':id,'center_xy':[x,y],'original_radius_m':r,'footprint_xy':poly,'z':[.08,.51],'contact_seam_m':.012,'center_change_m':0,'provenance':'v1 anchors retained; clipped module contact sides inferred from RGB 0/45/60/135/179'})
 for k in range(4):
  a=math.pi/4+k*math.pi/2;cyl(f'foot_{k}',(x+r*.45*math.cos(a),y+r*.45*math.sin(a),.085),.023,.15,silver,12)
 if back:
  angles=np.linspace(angle-.92,angle+.92,24)
  poly=[(x+(r+.005)*math.cos(a),y+(r+.005)*math.sin(a)) for a in angles]+[(x+(r-.075)*math.cos(a),y+(r-.075)*math.sin(a)) for a in reversed(angles)]
  poly=clip_module(poly,x,y,others)
  if len(poly)>=3:prism('curved_backrest',poly,.47,.85,fabric,.025)
for prefix,seats,evidence in [('far',far_seats,[0,45,135,179]),('near',near_seats,[45,60,72,90])]:
 for k,(x,y,r,b,a) in enumerate(seats):chair(f'{prefix}_seat_{k}',x,y,r,b,a,seats,evidence)
(O/'analysis/seat_repair_measurements.json').write_text(json.dumps(seat_measurements,indent=2))
''' +s[b:]
# Relation completeness and wall/door colliders from real pieces, never a union AABB.
s=s.replace(" pts=[]\n for name", " if not r['spatial_relations']:\n  if r['category']=='mirror':r['spatial_relations']=[{'relation':'mounted_on','target':'mirror_bay_wall'}]\n  elif r['category']=='wall_art':r['spatial_relations']=[{'relation':'mounted_on','target':'far_end_wall'}]\n  elif r['category'] not in ['floor','ceiling']:r['spatial_relations']=[{'relation':'supported_by','target':'floor'}]\n  else:r['spatial_relations']=[{'relation':'below' if id=='floor' else 'above','target':'ceiling' if id=='floor' else 'floor'}]\n pts=[]\n for name")
s=s.replace(" cols.append({'object_id':id", " if r['category'] in ['wall','door']:\n  for name in r['component_names']:\n   obj=bpy.data.objects[name];pp=np.array([list(obj.matrix_world@Vector(p)) for p in obj.bound_box])\n   cols.append({'object_id':id,'component_name':name,'type':'axis_aligned_box','bounds':{'min':pp.min(0).tolist(),'max':pp.max(0).tolist()},'static':True,'friction':.5,'restitution':0,'provenance':'individual visible structural component; no aperture-spanning union box'})\n  continue\n cols.append({'object_id':id")
s=s.replace("'derivation':'RGB semantics and stable M3 depth/pose anchor consensus. No GT, other methods, old model, or previous scene code read.'", "'derivation':'Supplied own-method v1 script and original M3 measurements; bounded v3 cushion and doorway repair based on permitted RGB and initial review. No v2 geometry or other-method data used.'")
s=s.replace("'status':'building_initial_checks','quality_status':'limited_pending_review'", "'status':'building_v3_checks','quality_status':'limited'")
s=s.replace("'revisions':VERSION,'checking_render_count'", "'revisions':VERSION,'input_bvh_passes':2,'final_input_pass_owner':'coordinator','checking_render_count'")
s=s.replace("'conflicts':issues,'robust_floor_reference_m'", "'v3_seat_repairs':seat_measurements,'v3_door_states':[{k:r[k] for k in ['id','door_state','door_state_confidence','door_state_evidence']} for r in records.values() if 'door_state' in r],'conflicts':issues,'robust_floor_reference_m'")
p.write_text(s)
compile(s,str(p),'exec')
print('V3 repair edits complete; no scene build has been run.')
