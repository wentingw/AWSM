from pathlib import Path
import json,shutil
R=Path(__file__).parent
# Preserve v1 auxiliary artifacts omitted by generic snapshot tool.
for f in ['colliders.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json']:
 d=R/'versions/v1'/f;d.parent.mkdir(parents=True,exist_ok=True)
 if not d.exists():shutil.copyfile(R/f,d)
L=json.loads((R/'analysis/proposed_layout_v2.json').read_text());(R/'layout.json').write_text(json.dumps(L,indent=2)+'\n')
p=R/'build_scene.py';s=p.read_text();s=s.replace('import bpy,math,json,sys,argparse,random','import bpy,bmesh,math,json,sys,argparse,random')
s=s.replace("records={};current=None","records={};current=None;rod_requests=[];wall_parts={};seat_polygons={}")
s=s.replace("(.48,.46,.40),.2,noise=110","(.36,.34,.29),.16,noise=110")
s=s.replace("(.034,.030,.025),.12,metal=.2,noise=180","(.016,.014,.012),.13,metal=.3")
s=s.replace("(.47,.42,.33),.42,noise=65","(.27,.23,.17),.43,noise=65")
s=s.replace("(.32,.32,.29),.48,noise=80","(.22,.22,.20),.48,noise=80")
s=s.replace("(.33,.40,.23),.79,noise=145","(.25,.31,.16),.79,noise=145")
s=s.replace("(.7,.67,.56),.75","(.48,.44,.34),.75")
s=s.replace("(.67,.64,.56),.86,noise=25","(.46,.43,.36),.86,noise=25")
s=s.replace("for p in o.data.polygons:p.use_smooth=True\n return o\ndef sphere", "for p in o.data.polygons:p.use_smooth=len(p.vertices)==4\n return o\ndef sphere")
s=s.replace("o.rotation_quaternion=d.to_track_quat('Z','Y');o.rotation_mode='QUATERNION';return o", "o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');rod_requests.append({'name':o.name,'a':list(a),'b':list(b)});return o")
s=s.replace("me.update();o=bpy.data.objects.new(suffix,me)","me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(suffix,me)")
# Material-only floor pattern in object coordinates: inferred dashes from source, no depth surface displacement.
pos=s.index('def group(')
s=s[:pos]+'''# Inferred regular brass dashes approximate the observed reflective floor pattern.
nt=M['blackfloor'].node_tree;texf=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(texf.outputs['Object'],sep.inputs[0])
def mathnode(op,a=None,b=None):
 n=nt.nodes.new('ShaderNodeMath');n.operation=op
 if a is not None:
  if isinstance(a,(int,float)):n.inputs[0].default_value=a
  else:nt.links.new(a,n.inputs[0])
 if b is not None:
  if isinstance(b,(int,float)):n.inputs[1].default_value=b
  else:nt.links.new(b,n.inputs[1])
 return n.outputs[0]
fx=mathnode('FRACT',mathnode('MULTIPLY',sep.outputs['X'],14));fy=mathnode('FRACT',mathnode('MULTIPLY',sep.outputs['Y'],14))
mask=mathnode('MULTIPLY',mathnode('LESS_THAN',fx,.23),mathnode('LESS_THAN',fy,.56));mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.014,.012,.01,1);mix.inputs[2].default_value=(.17,.125,.055,1);nt.links.new(mask,mix.inputs[0]);nt.links.new(mix.outputs[0],nt.nodes.get('Principled BSDF').inputs['Base Color'])
for key in ['stone','wood','ceiling']:
 for n in M[key].node_tree.nodes:
  if n.type=='BUMP':n.inputs['Distance'].default_value=.002
''' + s[pos:]
s=s.replace('range(35 if gold else 46)','range(65 if gold else 65)').replace('9 if gold else 5','12 if gold else 7')
start=s.index('def panelwall(');end=s.index('# Glazing emits',start)
s=s[:start]+'''def panelwall(id,start,end,material='wood',horizontal=False,doors=[]):
 group(id,'wall',[33,61,74,82,91,129],support='floor');length=math.dist(start,end);n=max(1,round(length/.86));origin=start[0] if horizontal else start[1]
 # Continuous structural backing, split at exact aperture boundaries. Seams are shallow finish joints.
 cuts=sorted(set([origin,origin+length]+[v+d*w/2 for v,w in doors for d in [-1,1]]));parts=[]
 for j,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
  if hi<=origin or lo>=origin+length:continue
  lo=max(lo,origin);hi=min(hi,origin+length);mid=(lo+hi)/2;opening=any(abs(mid-v)<w/2 for v,w in doors);bottom=fz+L['passage']['height'] if opening else fz
  loc=(mid,start[1]+.10,(bottom+cz)/2) if horizontal else (start[0]+.10,mid,(bottom+cz)/2)
  dims=(hi-lo,.10,cz-bottom) if horizontal else (.10,hi-lo,cz-bottom)
  o=box(f'backing_{j}',loc,dims,'dark');parts.append(o.name)
 for j in range(n):
  lo=origin+j*length/n+.011;hi=origin+(j+1)*length/n-.011
  for k,(zlo,zhi) in enumerate([(fz,2.06),(2.085,3.9),(3.925,cz)]):
   segments=[(lo,hi)]
   if k==0:
    for v,w in doors:
     result=[]
     for a,b in segments:
      if b<=v-w/2 or a>=v+w/2:result.append((a,b))
      else:
       if a<v-w/2:result.append((a,v-w/2))
       if b>v+w/2:result.append((v+w/2,b))
     segments=result
   for sub,(a,b) in enumerate(segments):
    if b-a<1e-5:continue
    mid=(a+b)/2;loc=(mid,start[1],(zlo+zhi)/2) if horizontal else (start[0],mid,(zlo+zhi)/2);dims=(b-a,.14,zhi-zlo) if horizontal else (.14,b-a,zhi-zlo);box(f'panel_{j}_{k}_{sub}',loc,dims,material)
 wall_parts[id]=parts
rstart=L['bounds']['recess_start_y']
panelwall('end_wall',(wx,yf),(ry,yf),horizontal=True);panelwall('near_wall',(wx,yn),(sy,yn),horizontal=True)
panelwall('mirror_wall',(sy,yn),(sy,rstart),doors=[(5.95,.9),(L['passage']['center_y'],L['passage']['width'])]);panelwall('recess_wall',(ry,rstart),(ry,yf),'grey');panelwall('recess_return',(sy,rstart),(ry,rstart),'grey',True)
for j,(y,x) in enumerate([(5.95,sy),(-.3,sy),(9.8,ry),(12.2,ry)]):
 if j==1:
  p=L['passage'];h=p['height'];w=p['width'];depth=p['return_depth'];group('service_door_1','open_passage',[61,74,82],'Observed open RGB passage; exact clearance and bounded hidden returns inferred');records[current]['state']='open'
  for k,dy in enumerate([-w/2-.06,w/2+.06]):box('return_'+str(k),(x+depth/2,y+dy,fz+h/2),(depth,.12,h),'grey')
  box('ceiling_return',(x+depth/2,y,fz+h+.06),(depth,w+.24,.12),'grey');box('floor_return',(x+depth/2,y,fz-.06),(depth,w,.12),'stone');box('bounded_end',(x+depth+.06,y,fz+h/2),(.12,w+.24,h),'dark')
  records[current]['relations']['connects']=['lobby','inferred_service_vestibule'];continue
 group(f'service_door_{j}','door',[61,74,82]);records[current]['state']='closed';box('door',(x-.085,y,.93),(.035,.90,2.24),'frame');box('head',(x-.12,y,2.055),(.08,.94,.035),'shade')
''' + s[end:]
s=s.replace("(.09,.065,2.7)","(.09,.15,2.7)").replace("(.09,.9,.12)","(.09,.9,.20)")
s=s.replace("group(f'entrance_doors_{j}','double_door',[100,108,118]);","group(f'entrance_doors_{j}','double_door',[100,108,118]);records[current]['state']='closed';")
start=s.index('# Modular round seating.');end=s.index('for t in L[\'tables\']:',start)
s=s[:start]+'''# Modular seats have explicitly shared clip boundaries, with 6mm upholstery clearance.
def clip_polygon(poly,normal,offset):
 result=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=np.dot(a,normal)-offset;db=np.dot(b,normal)-offset
  if da<=0:result.append(a)
  if (da<0)!=(db<0):result.append(np.array(a)+(np.array(b)-a)*da/(da-db))
 return result
def seat_clip(poly,s):
 c=np.array(s['center'][:2])
 for other in L['seats']:
  if other['id']==s['id']:continue
  d=np.array(other['center'][:2]);delta=d-c;distance=np.linalg.norm(delta)
  if distance<s['radius']+other['radius']+.03:
   n=delta/distance;offset=np.dot((c+d)/2,n)-.003;poly=clip_polygon(poly,n,offset)
 return [list(v) for v in poly]
def prism(suffix,poly,zlo,zhi,mat):
 n=len(poly);vv=[(x,y,z) for z in [zlo,zhi] for x,y in poly];ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)];return mesh(suffix,vv,ff,mat)
for s in L['seats']:
 group(s['id'],'lounge_chair' if s['back'] else 'ottoman',s['evidence_frames']);x,y,z=s['center'];r=s['radius'];poly=seat_clip([[x+r*math.cos(a),y+r*math.sin(a)] for a in np.linspace(0,2*math.pi,65)[:-1]],s);prism('upholstered_base',poly,z-s['height']/2,z+s['height']/2,'cloth');seat_polygons[s['id']]=poly;records[current]['relations']['assembly']='far_modular_cluster' if s['id']<'lounge_seat_06' else 'near_modular_cluster'
 for j,(dx,dy) in enumerate([(-.15,-.15),(-.15,.15),(.15,-.15),(.15,.15)]):cyl('foot_%d'%j,(x+dx,y+dy,fz+.045),.021,.09,'frame',12)
 if s['back']:
  angles=np.linspace(s['yaw']+math.pi*.24,s['yaw']+math.pi*.94,33);poly=[[x+r*.99*math.cos(a),y+r*.99*math.sin(a)] for a in angles]+[[x+r*.73*math.cos(a),y+r*.73*math.sin(a)] for a in reversed(angles)];poly=seat_clip(poly,s);prism('curved_back',poly,z+.19,z+.53,'cloth')
''' + s[end:]
start=s.index("group('mirror_installation'");end=s.index('# Faceted reception',start)
s=s[:start]+'''group('mirror_installation','wall_mirrors',[61,74,82],support='mirror_wall')
for j,d in enumerate(L['mirrors']['discs']):
 o=cyl('disc_%02d'%j,d['center'],d['radius'],.032,'mirror',64);o.rotation_euler[1]=math.pi/2
''' + s[end:]
s=s.replace('data.energy=850','data.energy=420').replace('data.energy=180','data.energy=90')
start=s.index("coll=[{'id':");end=s.index('if OUT!=SRC:',start)
s=s[:start]+'''coll=[]
def addbox(id,name,bounds,category):coll.append({'id':id,'component':name,'type':'AABB','bounds':bounds,'physics':'inferred_static','category':category})
for r in records.values():
 if r['category'] in ['pendant_light','wall_decoration','wall_mirrors','flower','ceiling_trim']:continue
 if r['id'] in seat_polygons:
  coll.append({'id':r['id'],'type':'convex_prism','polygon_xy':seat_polygons[r['id']],'z_range':[fz,r['bounds'][1][2]],'physics':'inferred_static','category':r['category']});continue
 if r['id'] in wall_parts or r['category']=='open_passage':
  for name in r['component_names']:
   if r['id'] in wall_parts and name not in wall_parts[r['id']]:continue
   o=bpy.data.objects[name];a=np.array([o.matrix_world@Vector(c) for c in o.bound_box]);addbox(r['id'],name,[a.min(0).tolist(),a.max(0).tolist()],r['category'])
 else:addbox(r['id'],None,r['bounds'],r['category'])
portals=[{'id':'service_door_1','state':'open','plane_x':sy,'y_range':[L['passage']['center_y']-L['passage']['width']/2,L['passage']['center_y']+L['passage']['width']/2],'z_range':[fz,2.06],'clear_width_m':L['passage']['width'],'clear_height_m':2.06-fz,'traversable_across_wall':True,'bounded_vestibule_depth_m':L['passage']['return_depth'],'hidden_extent_inferred':True}]+[{'id':f'entrance_doors_{j}','state':'closed','traversable_in_saved_state':False,'blocking_proxy':'glazed_facade'} for j in range(2)]
(OUT/'colliders.json').write_text(json.dumps({'colliders':coll,'portals':portals,'note':'Inferred static proxies. Shared seat footprints and split wall backing; closed exterior glazing deliberately blocks entry. Open service vestibule bounded beyond traversable aperture.'},indent=2))
(OUT/'analysis').mkdir(exist_ok=True);(OUT/'analysis/rod_requests.json').write_text(json.dumps(rod_requests,indent=2))
''' + s[end:]
p.write_text(s)
m=json.loads((R/'modelling_manifest.json').read_text());m.update(revisions=2,author_phase='revision',status='repair_in_progress',quality_status='LIMITED; author technical validation pending');(R/'modelling_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
