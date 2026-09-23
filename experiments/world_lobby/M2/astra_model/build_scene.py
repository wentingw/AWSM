"""M2 clean semantic reconstruction. All dimensions in unscaled native ViPE units.
Derived evidence: cameras.json, geometry_analysis.json, manual_measurements.json.
No imported scene, GT, other method, or fused point-cloud rendering.
"""
import bpy,bmesh,math,json,random,time,os,struct
from pathlib import Path
from mathutils import Vector,Matrix
O=Path(__file__).resolve().parent;START=time.time();random.seed(724);bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.world=bpy.data.worlds.new('Daylight');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.83,.9,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.40
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.4
M={}
def mat(n,c,rough=.5,metal=0,emission=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=emission
 M[n]=m;return m
mat('warm_stone',(.43,.42,.365),.18);mat('pale_oak',(.34,.31,.26),.52);mat('panel_recess',(.08,.075,.062),.45);mat('ceiling_plaster',(.7,.68,.61),.74);mat('charcoal',(.025,.024,.021),.32);mat('black_polished_inlay',(.027,.025,.020),.095,.15);mat('sage_upholstery',(.35,.43,.265),.83);mat('bronze',(.28,.22,.11),.25,.7);mat('silver',(.57,.59,.57),.25,.8);mat('mirror',(.91,.94,.90),.025,1);mat('ceramic_grey',(.53,.57,.57),.2);mat('planter_grey',(.27,.29,.28),.52);mat('soil',(.035,.028,.017),1);mat('leaf_green',(.13,.20,.05),.68);mat('leaf_light',(.30,.36,.12),.75);mat('golden_leaves',(.40,.32,.065),.65);mat('twigs',(.22,.15,.045),.9);mat('rattan',(.50,.38,.21),.55);mat('lamp_glow',(.98,.72,.34),.4,emission=3.5);mat('exterior_white',(.95,.97,1),.5,emission=1.4);mat('emblem',(.75,.74,.7),.32)
mat('closed_door_glass',(.91,.95,.93),.025);M['closed_door_glass'].node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=1;M['closed_door_glass'].node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.45
# Procedural material evidence: visible vertical wall grain and subtle stone variation.
for key,scale,strength in [('pale_oak',6,.18),('warm_stone',4,.08),('sage_upholstery',160,.08),('planter_grey',45,.1),('ceiling_plaster',7,.08)]:
 m=M[key];ns=m.node_tree.nodes;lk=m.node_tree.links;tex=ns.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;co=ns.new('ShaderNodeTexCoord');mapping=ns.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(22,22,.35) if key=='pale_oak' else (1,1,1);lk.new(co.outputs['Generated'],mapping.inputs[0]);lk.new(mapping.outputs[0],tex.inputs[0]);bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=.04 if key!='sage_upholstery' else .008;lk.new(tex.outputs['Fac'],bump.inputs['Height']);lk.new(bump.outputs[0],ns.get('Principled BSDF').inputs['Normal'])
GROUPS={};CURRENT=None
def group(id,cat,evidence,prov='Visible RGB shape with supplied ViPE depth; rigidly normalized without scale change.',**attrs):
 global CURRENT;CURRENT=id;GROUPS[id]={'object_id':id,'category':cat,'attributes':attrs,'evidence':{'frame_ids':evidence},'geometry_provenance':prov,'spatial_relations':[],'parts':[]};return id
def finish(ob,name,ma):
 ob.name=CURRENT+'.'+name;ob['object_id']=CURRENT;ob['category']=GROUPS[CURRENT]['category'];ob.data.materials.append(M[ma]);GROUPS[CURRENT]['parts'].append(ob.name);return ob
def box(n,loc,dim,ma,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(ob,n,ma)
 if bevel:b=ob.modifiers.new('soft_edges','BEVEL');b.width=bevel;b.segments=3;ob.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 return ob
def cyl(n,loc,r,dep,ma,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=dep,location=loc);ob=bpy.context.object;finish(ob,n,ma)
 for p in ob.data.polygons:p.use_smooth=(len(p.vertices)==4)
 return ob
def mesh(n,verts,faces,ma):
 me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(ob);return finish(ob,n,ma)
def sphere(n,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);ob=bpy.context.object;ob.scale=scale;finish(ob,n,ma)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
def tube(n,points,r,ma):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 cu.bevel_depth=r;cu.bevel_resolution=1;ob=bpy.data.objects.new(n,cu);bpy.context.collection.objects.link(ob);return finish(ob,n,ma)
def lathe(n,x,y,z,profile,ma,N=64):
 vs=[(x+r*math.cos(i*2*math.pi/N),y+r*math.sin(i*2*math.pi/N),z+h) for r,h in profile for i in range(N)];fs=[]
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 ob=mesh(n,vs,fs,ma)
 for p in ob.data.polygons:p.use_smooth=True
 return ob
# Architecture, including observed widening behind the mirror wall.
group('floor','floor',[0,65,85,110,130],prov='Near ViPE floor depth and far window-floor RGB triangulation; floor z=0. Thickness inferred.',friction=.55,observed_surface='top',inferred='slab underside')
box('main_slab',(-.35,6.2,-.08),(8.0,19.6,.16),'warm_stone');box('rear_extension',(4.7,11.3,-.08),(2.5,8.6,.16),'warm_stone')
group('dark_floor_inlay','rug',[0,65,85,110,130],material='glossy black woven inlay',thickness_inferred=True);box('long_inlay',(-.35,5.45,.007),(4.6,15.7,.014),'black_polished_inlay',.012)
# Fine subdued geometric weave; its bright dots in RGB are largely ceiling reflections.
for i in range(88):box('weave_%03d'%i,(-2.62+i*.052,5.45,.015),(.008,15.5,.0015),'charcoal')
def panelwall(id,axis,fixed,start,end,height=4.95,doors=()):
 group(id,'wall',[0,65,85,130],observed='panelled front face',inferred='wall thickness and backing')
 def piece(a,b,z0,z1,n):
  if b<=a:return
  loc=(fixed,(a+b)/2,(z0+z1)/2) if axis=='x' else ((a+b)/2,fixed,(z0+z1)/2);dim=(.16,b-a,z1-z0) if axis=='x' else (b-a,.16,z1-z0);box(n,loc,dim,'pale_oak')
 marks=[start]+[v for d in doors for v in d]+[end]
 for k in range(0,len(marks)-1,2):piece(marks[k],marks[k+1],0,height,'panelblock')
 for a,b in doors:piece(a,b,2.25,height,'lintel')
 for t in [start+j*.76 for j in range(int((end-start)/.76)+1)]:
  z0=2.25 if any(a<t<b for a,b in doors) else 0
  loc=(fixed-.086,t,(z0+height)/2) if axis=='x' else (t,fixed-.086,(z0+height)/2);dim=(.01,.013,height-z0) if axis=='x' else (.013,.01,height-z0);box('vertical_joint',loc,dim,'panel_recess')
 for z in [2.25,3.75]:
  loc=(fixed-.087,(start+end)/2,z) if axis=='x' else ((start+end)/2,fixed-.087,z);dim=(.012,end-start,.015) if axis=='x' else (end-start,.012,.015);box('horizontal_joint',loc,dim,'panel_recess')
panelwall('mirror_feature_wall','x',3.65,-3.6,7.15,doors=[(-2.6,-1.5),(5.7,6.75)])
panelwall('rear_right_wall','x',5.95,7.15,15.6,doors=[(10.8,12.0)])
panelwall('right_return_wall','y',7.2,3.65,5.95,doors=[(4.0,5.05)])
panelwall('reception_back_wall','y',15.65,-4.4,5.95)
panelwall('front_end_wall','y',-3.65,-4.4,3.65)
group('ceiling','ceiling',[0,85,110,130],inferred='hidden structural thickness');box('ceiling',(.7,6,5.05),(10.65,19.5,.2),'ceiling_plaster')
group('ceiling_slats','ceiling_detail',[0,85,110,130],spacing=.18)
for y in [ -3.5+i*.18 for i in range(106) ]:
 box('left_louver',(-3.4,y,4.90),(2.0,.055,.12),'charcoal');box('right_louver',(3.05,y,4.90),(2.1,.055,.12),'charcoal')
group('window_wall','window',[0,100,110,130],inferred='glazing optical constants',transmission='bright overexposed exterior in input')
box('bright_exterior',(-4.56,6,2.5),(.035,19.4,5.0),'exterior_white')
for y in [-3.5+i*.85 for i in range(23)]:box('mullion',(-4.43,y,2.48),(.09,.04,4.96),'charcoal')
for z in [.04,2.55,4.93]:box('transom',(-4.41,6,z),(.10,19.4,.065),'charcoal')
group('glass_entry_double_door','door',[0,105,110,130],hinge_inferred=True,state='closed',supports_opening=False,collision_semantics='Static closed door leaves block passage; fixed window wall excludes portal aperture.')
for y in [11.65,12.43,13.21]:box('door_stile',(-4.34,y,1.24),(.12,.075,2.48),'bronze')
for y in [12.04,12.82]:
 box('closed_leaf',( -4.34,y,1.265),(.035,.695,2.265),'closed_door_glass')
 for z in [.10,2.45]:box('door_rail',(-4.34,y,z),(.12,.80,.09),'bronze')
 tube('vertical_handle',[(-4.23,y-.20,.93),(-4.23,y-.20,1.55)],.015,'silver')
group('window_column','column',[0,110,130],prov='RGB cylinder fitted near x=-3.6,y=7.1; conflicting native depth versus triangulation retained.',radius=.43)
cyl('shaft',(-3.56,7.10,2.47),.43,4.94,'warm_stone');cyl('base',(-3.56,7.10,.045),.445,.09,'warm_stone')
# Chairs: soft cylindrical bases, optional curved shell backs.
def chair(id,x,y,r=.47,theta=0,back=True):
 r=r*.88 if id.startswith('lounge_B_') else r
 group(id,'chair' if back else 'ottoman',[0,65,85,130],seat_height=.47,observed='sage round upholstered seat',inferred='underside, foam, foot attachment')
 cyl('seat',(x,y,.29),r,.43,'sage_upholstery');cyl('seat_top',(x,y,.498),r*.985,.04,'sage_upholstery')
 for a in [45,135,225,315]:
  u=math.radians(a);cyl('foot',(x+r*.65*math.cos(u),y+r*.65*math.sin(u),.055),.026,.11,'charcoal',16)
 if back:
  vs=[];N=40
  for z,rr in [(.48,r*.89),(.48,r*1.04),(.92,r*1.04),(.92,r*.89)]:
   for i in range(N):a=theta+math.radians(-70+140*i/(N-1));vs.append((x+rr*math.cos(a),y+rr*math.sin(a),z))
  fs=[]
  for k in range(4):
   for i in range(N-1):fs.append((k*N+i,k*N+i+1,((k+1)%4)*N+i+1,((k+1)%4)*N+i))
  fs.extend([(0,N,2*N,3*N),(N-1,2*N-1,3*N-1,4*N-1)]);ob=mesh('curved_back',vs,fs,'sage_upholstery');be=ob.modifiers.new('rounded_upholstery','BEVEL');be.width=.035;be.segments=3
  for p in ob.data.polygons:p.use_smooth=True
for a in [('lounge_A_ottoman',-1.45,4.98,.43,0,False),('lounge_A_chair_left',-1.48,5.85,.40,2.9,True),('lounge_A_chair_rear',-.98,6.43,.40,1.7,True),('lounge_A_oval_seat',-.34,6.25,.53,0,False),('lounge_A_ottoman_mid',.04,5.76,.39,0,False),('lounge_A_chair_right',.60,5.88,.41,.1,True),('lounge_B_chair_back',1.00,2.73,.47,1.4,True),('lounge_B_chair_mid',1.56,2.10,.47,.9,True),('lounge_B_chair_front',1.70,1.27,.47,.1,True),('lounge_B_ottoman_left',-.14,1.35,.46,0,False),('lounge_B_chair_left',-.48,.55,.46,3.5,True),('lounge_B_ottoman_rear',.43,3.02,.48,0,False)]:chair(*a)
# Resolve coplanar overlaps among distinct upholstered seat solids. This small
# layout regularization preserves group centers and records each displacement.
for prefix in ['lounge_A_', 'lounge_B_']:
 ids=[k for k,g in GROUPS.items() if k.startswith(prefix) and g['category'] in ['chair','ottoman']]
 original={k:bpy.data.objects[k+'.seat'].location.copy() for k in ids}
 centers={k:Vector((v.x,v.y)) for k,v in original.items()}
 radii={k:bpy.data.objects[k+'.seat'].dimensions.x*.52 for k in ids}
 anchor=Vector((-.56,5.24)) if prefix=='lounge_A_' else Vector((.16,2.33));table_radius=.63 if prefix=='lounge_A_' else .69
 for _ in range(500):
  moved=False
  for k in ids:
   delta=centers[k]-anchor;target=radii[k]+table_radius+.025
   if delta.length<target:
    centers[k]=anchor+delta.normalized()*target;moved=True
  for ii,a in enumerate(ids):
   for b in ids[ii+1:]:
    delta=centers[b]-centers[a];d=delta.length;target=radii[a]+radii[b]+.015
    if d<target:
     shift=delta.normalized()*(target-d)*.501;centers[a]-=shift;centers[b]+=shift;moved=True
  if not moved:break
 for k in ids:
  delta=Vector((centers[k].x-original[k].x,centers[k].y-original[k].y,0))
  for name in GROUPS[k]['parts']:bpy.data.objects[name].location+=delta
  GROUPS[k]['attributes']['nonintersection_layout_adjustment_m']=list(delta)
  GROUPS[k]['attributes']['layout_constraint']='Seat-seat and seat-table disks separated; measured table center fixed. Foreground radii reduced 12% based on RGB bulk discrepancy.'

def table(id,x,y,r=.64):
 group(id,'table',[0,65,85,130],top_height=.48,observed='black round top and open ribbed base',inferred='base joins')
 cyl('top',(x,y,.47),r,.05,'charcoal',64)
 for i in range(28):
  a=i*math.tau/28;tube('rib',[(x+.38*math.cos(a),y+.38*math.sin(a),.04),(x+.25*math.cos(a+.18),y+.25*math.sin(a+.18),.25),(x+.43*math.cos(a+.3),y+.43*math.sin(a+.3),.445)],.012,'charcoal')
 group(id+'_bowl','decor',[0,130],inferred='unseen bowl thickness');lathe('bowl',x,y,.50,[(0,0),(.13,0),(.16,.07),(.155,.16),(.14,.165),(.125,.08),(0,.055)],'bronze',48)
table('lounge_A_table',-.56,5.24,.63);table('lounge_B_table',.16,2.33,.69)
# Rectangular dividers and branch/leaf meshes.
def shrub(id,x,y,z,rx,ry,rz,gold=False,seed=0):
 group(id,'plant',[0,85,130],inferred='individual foliage topology',species='unidentified ornamental shrub');rng=random.Random(seed);verts=[];faces=[]
 for k in range(30 if gold else 45):
  bx=x+rng.uniform(-rx,rx)*.6;by=y+rng.uniform(-ry,ry)*.6;tip=Vector((x+rng.uniform(-rx,rx),y+rng.uniform(-ry,ry),z+rz*rng.uniform(.55,1.)));base=Vector((bx,by,z));mid=(base+tip)*.5+Vector((rng.uniform(-.12,.12),rng.uniform(-.12,.12),.1));tube('stem',[base,mid,tip],.006 if gold else .005,'twigs' if gold else 'leaf_green')
  for j in range(10):
   t=(j+1)/11;ctr=base.lerp(tip,t);aa=rng.uniform(0,math.tau);length=rng.uniform(.07,.16) if gold else rng.uniform(.12,.25);w=length*.25;d=Vector((math.cos(aa),math.sin(aa),rng.uniform(.1,.6)));side=Vector((-d.y,d.x,0));vi=len(verts);verts.extend([ctr,ctr+d*length*.5+side*w,ctr+d*length,ctr+d*length*.5-side*w]);faces.append((vi,vi+1,vi+2,vi+3))
 mesh('leaves',verts,faces,'golden_leaves' if gold else 'leaf_green')
for name,x in [('left',-1.14),('right',.90)]:
 group('divider_planter_'+name,'planter',[0,85,130],prov='Frames 0/130 manually triangulated box corners, near ViPE depth; back and wall thickness inferred.',observed='grey rectangular box and golden shrub')
 box('container',(x,7.75,.44),(1.57,.54,.83),'planter_grey',.02);box('soil',(x,7.75,.862),(1.46,.43,.015),'soil')
 for j in range(4):shrub('divider_'+name+'_shrub_'+str(j),x-.59+j*.39,7.75,.86,.35,.32,.85,True,40+j+(0 if name=='left' else 8))
def potplant(id,x,y,r=.43,h=.58,tree=False):
 group(id+'_pot','planter',[0,65,110,130],inferred='hollow pot underside');lathe('pot',x,y,0,[(0,0),(r*.55,.01),(r*.87,h*.22),(r,h*.75),(r*.94,h),(r*.84,h),(r*.85,h*.85)],'ceramic_grey');cyl('soil',(x,y,h*.87),r*.85,.018,'soil')
 if tree:
  group(id+'_tree','plant',[0,110,130],inferred='unobserved branches and individual leaf topology');tube('trunk',[(x,y,h*.85),(x+.04,y,h+1.1)],.037,'twigs')
  shrub(id+'_canopy',x,y,h+.85,.56,.52,.48,False,82+int(y))
 else:shrub(id+'_foliage',x,y,h*.85,r*.95,r*.9,.63,False,92+int(y))
potplant('window_shrub',-3.12,5.42,.64,.43);potplant('mirror_wall_shrub',3.03,4.10,.35,.62);potplant('reception_tree_left',-2.42,14.43,.27,.56,True);potplant('reception_tree_right',2.21,14.50,.28,.57,True);potplant('rear_corner_plant',4.91,14.70,.45,.41)
# Reception's clearly visible folded, tapered charcoal stone form.
group('reception_desk','reception_desk',[0,110,130],prov='Manual RGB triangulation frames0/130 top corners near x[-1.57,1.21],y14; native scale.',inferred='backside storage and solidity')
mesh('faceted_counter',[(-1.6,13.82,.97),(1.3,13.95,.97),(1.4,14.6,.97),(-1.6,14.6,.97),(-1.36,14.06,.08),(1.12,14.18,.08),(1.25,14.60,.08),(-1.36,14.60,.08),(.12,13.98,.47)],[(0,1,2,3),(0,8,4),(0,1,8),(1,5,8),(4,8,5),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'charcoal')
# R2: closed faceted desk with consistent outward winding, dimensions unchanged.
desk=bpy.data.objects['reception_desk.faceted_counter'];bm=bmesh.new();bm.from_mesh(desk.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.normal_update()
assert all(e.is_manifold for e in bm.edges), 'Desk must be closed manifold'
GROUPS['reception_desk']['attributes']['signed_volume_m3']=bm.calc_volume(signed=True);GROUPS['reception_desk']['attributes']['normals']='Consistent outward; manifold checked'
bm.to_mesh(desk.data);bm.free();desk.data.update()

group('reception_emblem','wall_decor',[0,130],inferred='abstract plaque and thin outline from RGB, not text');mesh('shield',[(-.35,15.54,2.56),(.35,15.54,2.56),(.33,15.54,1.78),(.15,15.54,1.50),(0,15.54,1.44),(-.20,15.54,1.55),(-.35,15.54,1.81)],[(0,1,2,3,4,5,6)],'emblem');tube('outline',[(-1.34,15.5,3.36),(-1.34,15.5,2.77),(-1.21,15.5,2.61),(-.4,15.5,2.61),(.4,15.5,2.61),(1.24,15.5,2.62),(1.40,15.5,2.77),(1.4,15.5,3.36)],.014,'charcoal')
# Circular mirrors on the projecting wall: circles lie in YZ, face the lobby.
mirror_fit=json.load(open(O/'mirror_refit.json'))
for item in mirror_fit['mirrors']:
 x,y,z=item['center'];r=item['radius'];group(item['object_id'],'mirror',[0,65,85],prov=mirror_fit['method'],inferred='thin backing',observed='round reflective wall disc',frame65_circle=item['rgb_frame65_circle_640x480']);ob=cyl('reflective_disc',(x,y,z),r,.025,'mirror',64);ob.rotation_euler[1]=math.pi/2
# Freestanding floor lamps.
for i,(x,y) in enumerate([(4.05,14.80),(4.17,8.38),(2.88,-2.10)]):
 group('floor_lamp_%d'%i,'floor_lamp',[0,65,85,130],inferred='hidden cable and tripod join');cyl('shade',(x,y,1.71),.22,.45,'ceiling_plaster')
 for a in [0,2.094,4.189]:tube('leg',[(x+.15*math.cos(a),y+.15*math.sin(a),.03),(x+.035*math.cos(a),y+.035*math.sin(a),1.51)],.012,'silver')
# Pendant positions obtained by intersecting manually observed frame-0 centers with nominal z=4.40.
cs=json.load(open(O/'cameras.json'));C=Matrix(cs['cameras'][0]['c2w_model']);K=cs['cameras'][0]['K'];lights=[(270,15,100),(360,95,54),(615,98,80),(904,67,142),(593,128,49),(366,143,40),(431,154,32),(493,164,45),(571,157,43),(635,169,37),(475,188,30),(541,193,28),(425,204,27),(490,211,26),(585,207,27)]
for ii,(u,v,rpx) in enumerate(lights):
 ray=C.to_3x3()@Vector(((u*1.28-K[0][2])/K[0][0],(v*1.28-K[1][2])/K[1][1],1));z=4.36+(ii%3)*.055;distance=(z-C.translation.z)/ray.z;pos=C.translation+ray*distance;x,y=pos.x,pos.y;r=max(.32,min(.95,rpx*1.28*distance/K[0][0]));group('pendant_%02d'%ii,'ceiling_light',[0,85,110,130],prov='RGB frame0 center rays intersect z=4.36..4.47 ceiling-relative support plane; depth conflicts on thin woven shades.',inferred='woven topology, cord, lighting watts',radius=r)
 tube('cord',[(x,y,z+.05),(x,y,4.95)],.007,'charcoal');profile=[(.11*r,0),(.30*r,.015),(.60*r,.06),(.84*r,.13),(r,.20),(r,.235)]
 # Open basket dish, radial reeds and concentric rims.
 for j in range(64):
  a=j*math.tau/64;pts=[(x+rr*math.cos(a),y+rr*math.sin(a),z+hh) for rr,hh in profile];tube('radial_reed',pts,.009,'rattan')
 for k in range(14):
  rr=r*(.22+.78*k/13);hh=.235*(rr/r)**2;pts=[(x+rr*math.cos(j*math.tau/96),y+rr*math.sin(j*math.tau/96),z+hh+.005*math.sin(j*math.pi)) for j in range(97)];tube('woven_ring',pts,.009,'rattan')
 cyl('diffuser',(x,y,z-.01),r*.24,.018,'lamp_glow');ld=bpy.data.lights.new('Pendant warm','AREA');ld.energy=12;ld.color=(1,.77,.43);ld.shape='DISK';ld.size=r*.50;lo=bpy.data.objects.new('pendant_light',ld);bpy.context.collection.objects.link(lo);lo.location=(x,y,z-.03)
# Physically motivated broad illumination from overexposed window wall.
for y in [0,6,12]:
 ld=bpy.data.lights.new('Window softbox','AREA');ld.energy=450;ld.shape='RECTANGLE';ld.size=4.2;ld.size_y=4.4;ob=bpy.data.objects.new('Daylight window',ld);bpy.context.collection.objects.link(ob);ob.location=(-4.22,y,2.65);ob.rotation_euler=(0,-math.pi/2,0)
ld=bpy.data.lights.new('Sun','SUN');ld.energy=1.05;ld.angle=.025;ob=bpy.data.objects.new('Sun',ld);bpy.context.collection.objects.link(ob);ob.rotation_euler=(.45,-.9,-.35)
# All supplied cameras retain exact transformed OpenCV c2w; Blender convention adapter only.
for c in cs['cameras']:
 ca=bpy.data.cameras.new('input_%03d'%c['frame_id']);ob=bpy.data.objects.new(ca.name,ca);bpy.context.collection.objects.link(ob);ob.matrix_world=Matrix(c['c2w_model'])@Matrix.Diagonal((1,-1,-1,1));ca.type='PERSP';ca.sensor_fit='HORIZONTAL';ca.sensor_width=36;ca.lens=c['K'][0][0]*36/c['width'];ca.shift_x=(c['width']/2-c['K'][0][2])/c['width'];ca.shift_y=(c['K'][1][2]-c['height']/2)/c['width'];ca.clip_start=.03;ca.clip_end=100
scene.camera=bpy.data.objects['input_000'];scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=50;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.render.pixel_aspect_x=cs['cameras'][0]['K'][1][1]/cs['cameras'][0]['K'][0][0];scene.render.pixel_aspect_y=1
# Exports and object-level inferred collider envelopes.
bpy.context.view_layer.update();objects=[];colliders=[]
for id,g in GROUPS.items():
 pts=[]
 for name in g['parts']:
  ob=bpy.data.objects[name];pts.extend([ob.matrix_world@Vector(v) for v in ob.bound_box])
 lo=[min(p[j] for p in pts) for j in range(3)];hi=[max(p[j] for p in pts) for j in range(3)];g['bounds']={'min':lo,'max':hi};g['center']=[(a+b)/2 for a,b in zip(lo,hi)];g['spatial_relations']=[{'relation':'supported_by','object_id':'floor'}] if g['category'] in ['chair','ottoman','table','planter','reception_desk','floor_lamp','column'] else [];objects.append(g)
 if g['category'] not in ['decor','wall_decor','mirror','plant','ceiling_detail']:
  role='floor' if g['category'] in ['floor','rug'] else 'overhead' if g['category'] in ['ceiling','ceiling_light'] else 'obstacle';parts=[n for n in g['parts'] if g['category']=='floor' or (g['category']=='wall' and ('.panelblock' in n or '.lintel' in n))]
  if parts:
   for n in parts:
    ob=bpy.data.objects[n];bp=[ob.matrix_world@Vector(v) for v in ob.bound_box];bb={'min':[min(v[j] for v in bp) for j in range(3)],'max':[max(v[j] for v in bp) for j in range(3)]};colliders.append({'object_id':id,'collider_id':n,'role':role,'bounds':bb,'shape':'axis_aligned_box','provenance':'Per-solid bound; architectural openings and L-shaped floor retained.'})
  elif id=='window_wall':
   # Permanent glazing excludes the true door aperture, independent of leaf state.
   lo,hi=g['bounds']['min'],g['bounds']['max'];pieces=[('before_portal',[lo[0],lo[1],lo[2]],[hi[0],11.6125,hi[2]]),('after_portal',[lo[0],13.2475,lo[2]],[hi[0],hi[1],hi[2]]),('portal_header',[lo[0],11.6125,2.495],[hi[0],13.2475,hi[2]])]
   for cid,pmin,pmax in pieces:colliders.append({'object_id':id,'collider_id':id+'.'+cid,'role':'obstacle','bounds':{'min':pmin,'max':pmax},'shape':'axis_aligned_box','state':'fixed','provenance':'Fixed window assembly segmented around observed door aperture.'})
  elif id=='glass_entry_double_door':
   for name in g['parts']:
    if not any(k in name for k in ['closed_leaf','door_stile','door_rail']):continue
    ob=bpy.data.objects[name];bp=[ob.matrix_world@Vector(v) for v in ob.bound_box];bb={'min':[min(v[j] for v in bp) for j in range(3)],'max':[max(v[j] for v in bp) for j in range(3)]};colliders.append({'object_id':id,'collider_id':name,'role':'obstacle','bounds':bb,'shape':'axis_aligned_box','state':'closed_leaf' if 'closed_leaf' in name else 'fixed_frame','supports_opening':False,'provenance':'Observed static closed door; no open-door traversability claimed.'})
  else:colliders.append({'object_id':id,'role':role,'bounds':g['bounds'],'shape':'axis_aligned_box','provenance':'Conservative parametric envelope; physical thickness and friction inferred.'})
json.dump({'objects':objects,'units':'native ViPE near-metric metres'},open(O/'objects.json','w'),indent=2);json.dump({'colliders':colliders,'coordinate_frame':'same as scene.blend'},open(O/'colliders.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'scene.blend'));bpy.ops.export_scene.gltf(filepath=str(O/'scene.glb'),export_format='GLB',export_cameras=True,export_lights=False,export_apply=True)
# Preserve both supplied fx and fy exactly in standard glTF perspective fields.
# glTF aspect includes physical pixel aspect; no camera/extrinsic/scene transforms.
raw=(O/'scene.glb').read_bytes();chunks=[];off=12
while off<len(raw):
 length,kind=struct.unpack_from('<II',raw,off);chunks.append((kind,raw[off+8:off+8+length]));off+=8+length
payload=json.loads(chunks[0][1].decode('utf8'))
for ca in payload.get('cameras',[]):
 if ca.get('name','').startswith('input_'):
  fi=int(ca['name'].split('_')[-1]);cc=cs['cameras'][fi];fx,fy=cc['K'][0][0],cc['K'][1][1];w,h=cc['width'],cc['height'];ca['perspective']['yfov']=2*math.atan(h/(2*fy));ca['perspective']['aspectRatio']=w*fy/(h*fx)
encoded=json.dumps(payload,separators=(',',':')).encode('utf8');encoded+=b' '*((-len(encoded))%4);chunks[0]=(chunks[0][0],encoded);body=b''.join(struct.pack('<II',len(data),kind)+data for kind,data in chunks);(O/'scene.glb').write_bytes(struct.pack('<4sII',b'glTF',2,12+len(body))+body)

# Fixed input-frame internal checks, counted by completed renders.
checks=[0,65,85,110,130];render_dir=O/'checks_v5';render_dir.mkdir(exist_ok=True)
for i in checks:
 scene.camera=bpy.data.objects['input_%03d'%i];scene.render.filepath=str(render_dir/('frame_%03d.png'%i));scene.render.pixel_aspect_x=cs['cameras'][i]['K'][1][1]/cs['cameras'][i]['K'][0][0];scene.render.pixel_aspect_y=1;bpy.ops.render.render(write_still=True)
json.dump({'revision':5,'rendered_input_views':checks,'render_count':len(checks),'elapsed_seconds':time.time()-START,'blender_version':bpy.app.version_string,'threads':4,'engine':'Cycles CPU'},open(O/'build_report.json','w'),indent=2)
