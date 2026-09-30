"""Clean M1 semantic scene; authored only from allowed RGB packet. Run in Blender."""
import bpy, math, json, random, time, hashlib, os, sys
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parent
INPUT=ROOT.parent.parent/'inputs'/'M1'
VERSION=int(os.environ.get('M1_VERSION','2'))
DO_RENDER=os.environ.get('M1_RENDER','1')=='1'
START=time.time()
random.seed(271828)
for p in ['analysis','checks','independent_review']: (ROOT/p).mkdir(exist_ok=True)
packet=json.loads((INPUT/'packet.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=12
scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(0.65,0.69,0.75,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.18
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.15
M={}; records={}; current=None

def mat(name,color,rough=.5,metal=0,noise=0,scale=12):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 nt=m.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if noise:
  tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=noise;bump.inputs['Distance'].default_value=.025
  nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
 M[name]=m;return m
mat('ivory_stone',(0.43,.42,.38),.22,0,.16,80)
mat('wall_oak',(0.31,.285,.235),.48,0,.32,65)
mat('ceiling',(0.49,.47,.425),.72,0,.1,11)
mat('reveal',(0.047,.044,.037),.55)
mat('slats',(0.18,.16,.13),.55)
mat('black_polished',(0.024,.022,.018),.055,.46,0,22)
mat('sage_fabric',(.32,.39,.225),.88,0,.23,145)
mat('black_metal',(.028,.026,.023),.3,.65)
mat('tabletop',(.055,.052,.044),.38,.05)
mat('mirror',(.92,.96,.95),.008,1)
mat('brushed_steel',(.42,.46,.46),.24,.85)
mat('brass',(.38,.285,.12),.23,.78)
mat('concrete',(.29,.30,.29),.8,0,.35,95)
mat('blue_ceramic',(.34,.40,.44),.21,.08,.22,14)
mat('white_ceramic',(.6,.63,.6),.22)
mat('soil',(.025,.018,.01),1)
mat('branch',(.155,.11,.045),.9)
mat('yellow_leaf',(.48,.365,.055),.7)
mat('green_leaf',(.095,.18,.035),.68)
mat('leaf_light',(.22,.31,.075),.7)
mat('orange',(.75,.25,.015),.6)
mat('cream_lamp',(.62,.53,.37),.36,.3,.28,95)
mat('white_shade',(.7,.7,.63),.6)
for name,col,power in [('window_white',(1,1,1),3),('lamp_glow',(1,.67,.31),3.2)]:
 m=mat(name,col,.35);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=power
# Vertically stretched oak grain is a procedural material assumption.
nt=M['wall_oak'].node_tree;noise=next(n for n in nt.nodes if n.type=='TEX_NOISE');coord=nt.nodes.new('ShaderNodeTexCoord');mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=(1,1,.018);nt.links.new(coord.outputs['Generated'],mul.inputs[0]);nt.links.new(mul.outputs[0],noise.inputs['Vector'])

def begin(id,category,evidence,desc,provenance='observed form; dimensions inferred from RGB',relations=None,collider='box'):
 global current
 current=id; records[id]={'id':id,'category':category,'component_names':[],'description':desc,'evidence_sample_ids':evidence,'provenance':provenance,'uncertainty':'Scale is unobservable from calibrated monocular RGB; sizes depend on assumed typical furniture scale. Hidden backs, thickness, joints and material parameters inferred.','spatial_relations':relations or [],'collider_type':collider}

def reg(o,name,material):
 o.name=current+'__'+name;o['semantic_id']=current;o['component']=name
 if material:o.data.materials.append(M[material])
 records[current]['component_names'].append(o.name)
 return o

def cube(name,loc,dims,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 reg(o,name,material)
 if bevel:mod=o.modifiers.new('softened edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,radius,depth,material,verts=48,bevel=0):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc);o=reg(bpy.context.object,name,material)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 if bevel:mod=o.modifiers.new('edge round','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o

def mesh(name,vs,fs,material,smooth=False):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);reg(o,name,material)
 if smooth:
  for p in d.polygons:p.use_smooth=True
 return o

def lathe(name,center,profile,material,n=48):
 vs=[];fs=[]
 for r,z in profile:
  for j in range(n):a=2*math.pi*j/n;vs.append((center[0]+r*math.cos(a),center[1]+r*math.sin(a),center[2]+z))
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 return mesh(name,vs,fs,material,True)

def tube(name,points,r,material):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=1
 sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*v,1)
 ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);return reg(ob,name,material)

def leaves(name,center,spread,count,material,kind='bush'):
 vs=[];fs=[]
 for _ in range(count):
  a=random.uniform(0,2*math.pi);h=random.random();rad=spread*(random.random()**.5)
  if kind=='tree':z=center[2]+random.uniform(-spread*.65,spread*.65);c=Vector((center[0]+rad*math.cos(a),center[1]+rad*math.sin(a),z));length=random.uniform(.045,.1);width=length*.42
  elif kind=='grass':c=Vector(center)+Vector((rad*.35*math.cos(a),rad*.35*math.sin(a),random.uniform(0,.25)));length=random.uniform(.45,.86);width=.012
  else:c=Vector((center[0]+rad*math.cos(a),center[1]+rad*math.sin(a),center[2]+random.uniform(-spread*.3,spread*.6)));length=random.uniform(.022,.065);width=length*.42
  if kind=='grass':end=c+Vector((length*math.cos(a),length*math.sin(a),.15+length*.45));side=Vector((-math.sin(a),math.cos(a),0))*width;ps=[c-side,c+side,end+Vector((0,0,-.12))]
  else:
   t=Vector((math.cos(a),math.sin(a),random.uniform(-.7,.7))).normalized()*length;s=Vector((-math.sin(a),math.cos(a),0))*width;ps=[c-t,c+s,c+t,c-s]
  k=len(vs);vs.extend([tuple(p) for p in ps]);fs.append(tuple(range(k,k+len(ps))))
 return mesh(name,vs,fs,material)
# Architecture dimensions are inferred, coordinate x increases away from glazing; +y faces reception; z is up.
W,L,H=8.8,18.,5.2
begin('floor_stone','floor',[0,45,90,104,135,179],'Continuous light polished stone floor')
cube('slab',(W/2,L/2,-.10),(W,L,.2),'ivory_stone')
begin('floor_black_inset','floor',[0,45,90,104,135,179],'Dark glossy rectangular floor inset, same level as surrounding stone')
cube('slab',(3.65,9.15,.006),(4.5,15.4,.012),'black_polished')
begin('ceiling','ceiling',[0,45,80,104,135,179],'Pale ceiling over full lobby')
cube('slab',(W/2,L/2,H+.1),(W,L,.2),'ceiling')
# North and south panelled end walls; actual wall thickness not observed.
for side,y,ev in [('north',L,[0,45,135,179]),('south',0,[80,90])]:
 begin('wall_'+side,'wall',ev,'Vertical oak panels and dark horizontal reveals')
 cube('substrate',(W/2,y,H/2),(W,.18,H),'reveal')
 for ix in range(10):
  for iz,(z0,z1) in enumerate([(0,2.05),(2.05,4.1),(4.1,H)]):cube(f'panel_{ix}_{iz}',((ix+.5)*W/10,y+(-.101 if side=='north' else .101),(z0+z1)/2),(W/10-.022,.045,z1-z0-.022),'wall_oak')
# Exact opening splits: panel geometry and wall colliders retain doorways.
for id,x,ya,yb,ev,doorcenters in [('wall_east_main',7.35,0,13.8,[45,62,80,90,135],[4.8,11.3]),('wall_east_recess',8.8,13.8,18,[0,45,80,179],[14.6,16.35])]:
 begin(id,'wall',ev,'Panelled east wall split exactly at opening jambs')
 n=round((yb-ya)/.88)
 for i in range(n):
  low=ya+i*(yb-ya)/n+.01;high=ya+(i+1)*(yb-ya)/n-.01
  for iz,(za,zb) in enumerate([(0,2.05),(2.05,4.1),(4.1,H)]):
   segments=[(low,high)]
   if iz==0:
    for d in doorcenters:
     new=[]
     for aa,bb in segments:
      if bb<=d-.50 or aa>=d+.50:new.append((aa,bb))
      else:
       if aa<d-.50:new.append((aa,d-.50))
       if bb>d+.50:new.append((d+.50,bb))
     segments=new
   for k,(aa,bb) in enumerate(segments):
    if bb-aa>.003:cube(f'panel_{i}_{iz}_{k}',(x,(aa+bb)/2,(za+zb)/2),(.16,bb-aa,zb-za-.02),'wall_oak')
 for j,d in enumerate(doorcenters):
  if id=='wall_east_main' and j==0:
   begin('passage_south','open_passage',ev,'Observed dark open passage beside mirror wall; shallow return geometry is assumed',collider='compound')
   for dy in [-.53,.53]:cube('return_'+str(dy),(x+.55,d+dy,1.015),(1.02,.06,2.03),'reveal')
   cube('lintel',(x+.55,d,2.08),(1.02,1.12,.10),'reveal')
  else:
   begin(f'elevator_{id}_{j}','door',ev,'Closed brushed silver double panel door with exact clear wall opening',relations=[{'relation':'set_in','target':id}])
   for dy in [-.237,.237]:cube('leaf_'+str(dy),(x+.03,d+dy,1.02),(.045,.47,2.04),'brushed_steel')
   cube('center_seam',(x-.004,d,1.02),(.045,.01,2.04),'reveal')
 begin(id+'_reveals','trim',ev,'Horizontal black panel joints above doors',collider='none')
 for z in [2.05,4.1]:cube('rail_'+str(z),(x-.02,(ya+yb)/2,z),(.17,yb-ya,.014),'reveal')
begin('wall_recess_return','wall',[45,80,179],'Short return between main wall and recessed elevator bank')
cube('return',(8.08,13.8,H/2),(1.46,.16,H),'wall_oak')
# Curtain wall and entrance pairs.
begin('glazing','window_wall',[0,45,90,104,118,135,179],'Bright exterior glazing with repeated metal mullions',collider='box')
cube('bright_glass',(-.085,L/2,H/2),(.025,L,H),'window_white')
for j in range(21):cube(f'mullion_{j}',(0,L*j/20,H/2),(.085,.04,H),'brushed_steel')
for z in [0,3.05,H]:cube('transom_'+str(z),(0,L/2,z),(.11,L,.075),'black_metal')
for k,y in enumerate([2.1,15.7]):
 begin(f'entrance_{k}','door',[0,90,104,118,135],'Gold framed glazed double entrance doors')
 for dy in [-.425,.425]:
  for sy in [-.39,.39]:cube(f'jamb_{dy}_{sy}',(.05,y+dy+sy,1.49),(.10,.08,2.98),'brass')
  for z in [.10,2.93]:cube(f'cross_{dy}_{z}',(.05,y+dy,z),(.10,.78,.16),'brass')
  cube('handle_'+str(dy),(.16,y+(.07 if dy>0 else -.07),1.27),(.04,.025,.8),'black_metal',.006)
for k,y in enumerate([1.9,10.6]):
 begin(f'column_{k}','column',[0,45,90,104,118,135,179],'Full height round stone column beside glazing',collider='cylinder')
 cyl('shaft',(.60,y,H/2),.32,H,'ivory_stone',64)
for side,xa,xb in [('glass',0,1.6),('wall',6.0,8.8)]:
 begin('ceiling_slats_'+side,'ceiling_detail',[0,45,80,104,135,179],'Closely spaced dark ceiling battens',collider='none')
 for j in range(100):cube(f'batten_{j}',((xa+xb)/2,.09+j*.18,H-.10),(xb-xa,.055,.13),'slats')
# modular lounge chairs: rounded cylinder cushion, separate dark foot ring, curved upholstered back.
def seat(id,x,y,r=.40,back=False,angle=0,ev=[0,45,90,135,179]):
 r*=.80
 if id.startswith('seat_S'):y+=2.6
 if id=='seat_N1':x+=.20
 begin(id,'chair' if back else 'ottoman',ev,'Round upholstered modular seat'+(' with curved backrest' if back else ''),relations=[{'relation':'supported_by','target':'floor_black_inset'}],collider='cylinder')
 cyl('seat_cushion',(x,y,.35),r,.45,'sage_fabric',64,.04)
 cyl('underside',(x,y,.115),r*.79,.09,'black_metal',32)
 for a in [45,135,225,315]:
  aa=math.radians(a);cyl('foot_'+str(a),(x+r*.7*math.cos(aa),y+r*.7*math.sin(aa),.075),.028,.15,'brushed_steel',12)
 if back:
  vs=[];fs=[];n=32
  for z in [.48,.91]:
   for rr in [r-.105,r+.006]:
    for j in range(n+1):
     a=angle+math.radians(-68+136*j/n);vs.append((x+rr*math.sin(a),y+rr*math.cos(a),z))
  stride=n+1
  for j in range(n):
   for a,b in [(0,1),(1,3),(3,2),(2,0)]:fs.append((a*stride+j,a*stride+j+1,b*stride+j+1,b*stride+j))
  for j in [0,n]:fs.append(tuple(k*stride+j for k in [0,1,3,2]))
  ob=mesh('curved_back',vs,fs,'sage_fabric',True);bev=ob.modifiers.new('upholstered roundover','BEVEL');bev.width=.035;bev.segments=3;ob.modifiers.new('back normals','WEIGHTED_NORMAL')
# North seating seen throughout the primary path.
for name,x,y,r,b,a in [('N1',2.15,9.20,.43,False,0),('N2',2.13,10.02,.40,True,1.1),('N3',2.77,10.52,.40,True,0),('N4',3.56,10.56,.56,False,0),('N5',4.40,10.25,.42,False,0),('N6',5.13,10.12,.42,True,-.4)]:seat('seat_'+name,x,y,r,b,a)
# South grouping around a matching table; backs oriented toward outer wall.
for name,x,y,r,b,a in [('S1',4.8,4.95,.43,False,0),('S2',5.55,4.64,.42,True,-.2),('S3',5.82,3.90,.43,True,-1.2),('S4',4.92,2.92,.50,False,0),('S5',3.85,2.74,.42,True,2.7)]:seat('seat_'+name,x,y,r,b,a,[62,80,90,135,179])

def table(id,x,y,rx,ry,bowl=False,ev=[0,45,90,135,179]):
 begin(id,'coffee_table',ev,'Dark oval table with a radial fluted pedestal',relations=[{'relation':'supported_by','target':'floor_black_inset'}])
 top=cyl('oval_top',(x,y,.485),1,.055,'tabletop',64,.01);top.scale=(rx,ry,1)
 cyl('core',(x,y,.24175),.25,.4595,'black_metal',40)
 for j in range(24):
  a=j*2*math.pi/24;vs=[]
  for z,r in [(0.04,.31),(.16,.28),(.35,.23),(.46,.28)]:
   for aa in [a-.026,a+.026]:vs.append((x+r*math.cos(aa),y+r*math.sin(aa),z))
  fs=[(0,1,3,2),(2,3,5,4),(4,5,7,6)];mesh('flute_'+str(j),vs,fs,'black_metal',True)
 if bowl:
  begin(id+'_bowl','decor',ev,'Low metallic bowl on table',relations=[{'relation':'on','target':id}],collider='none')
  lathe('bowl',(x,y,.52),[(.05,0),(.14,.02),(.18,.09),(.175,.135),(.153,.13),(.13,.045),(.03,.025)],'black_metal')
  lathe('rim',(x,y,.52),[(.173,.125),(.179,.13),(.173,.137),(.16,.133)],'brass')
table('table_north',3.40,9.1,.64,.52,True)
table('table_south',4.35,6.45,.72,.53,False,[62,80,90,135,179])
# Planters, individual woody branches and leaf clusters.
def rectangle_planter(id,x,y):
 begin(id,'planter',[0,45,80,90,104,118,135,179],'Rectangular grey raised planter with spreading yellow flowering branches')
 cube('body',(x,y,.44),(1.80,.57,.86),'concrete',.018)
 cube('soil',(x,y,.876),(1.68,.46,.017),'soil')
 # Combined mesh for many stems; leaves use explicit independent polygons.
 branches=[]
 for k in range(64):
  xx=x+random.uniform(-.73,.73);yy=y+random.uniform(-.17,.17);height=random.uniform(.25,.56)
  end=(xx+random.uniform(-.45,.45),yy+random.uniform(-.4,.4),.88+height)
  tube('stem_'+str(k),[(xx,yy,.87),((xx+end[0])/2,(yy+end[1])/2,.88+height*.55),end],.004,'branch')
  leaves('yellow_sprig_'+str(k),end,.20,75,'yellow_leaf')
  mid=((xx+end[0])/2,(yy+end[1])/2,.88+height*.65)
  leaves('yellow_mid_'+str(k),mid,.18,55,'yellow_leaf')
rectangle_planter('planter_north_left',2.52,11.70)
rectangle_planter('planter_north_right',4.78,11.70)
# South edge of same seating zone has two planters visible from reverse direction.
# Images show two back-to-back screens framing the northern lounge; no extra planter pair assumed.

def pot(id,x,y,kind='grass',size=.52,ev=[0,45,62,90,135,179]):
 begin(id,'potted_plant',ev,'Ceramic '+('low bowl of arching foliage' if kind=='grass' else 'urn with clipped small tree'),collider='cylinder')
 if kind=='grass':
  lathe('vessel',(x,y,0),[(0,0),(.27*size/.52,.02),(size*.9,.18),(size,.36),(size*.98,.39),(size*.91,.38),(size*.82,.2)],'white_ceramic')
  cyl('soil',(x,y,.35),size*.90,.02,'soil')
  leaves('foliage',(x,y,.37),size*.9,650,'green_leaf','grass');leaves('bright_blades',(x,y,.38),size*.8,200,'leaf_light','grass')
 else:
  lathe('vessel',(x,y,0),[(.16,0),(.25,.08),(.31,.40),(.28,.61),(.23,.65),(.22,.62),(.21,.53)],'blue_ceramic')
  cyl('soil',(x,y,.61),.22,.02,'soil')
  if kind=='tree':
   for j in [-1,0,1]:tube('trunk_'+str(j),[(x+j*.06,y,.61),(x+j*.08,y,1.4)],.014,'branch')
   leaves('crown',(x,y,1.61),.45,1200,'green_leaf','tree');leaves('crown_light',(x,y,1.63),.45,250,'leaf_light','tree')
  else:leaves('foliage',(x,y,.68),.35,600,'leaf_light','grass')
pot('plant_glass_north',.65,9.50,'grass',.70)
pot('plant_glass_south',.7,3.8,'grass',.64,[90,104,118,135])
pot('plant_mirror_north',6.77,9.0,'urn',.5)
pot('plant_reception_left',1.75,17.20,'tree',.5,[0,45,104,118,135,179])
pot('plant_reception_right',5.55,17.20,'tree',.5,[0,45,135,179])
pot('plant_northeast_low',7.65,17.35,'grass',.45,[0,45,179])
pot('plant_south_low',1.25,1.0,'grass',.52,[90])
# Tall bird of paradise plants flanking southern seating.
for k,x in enumerate([2.40,5.80]):
 begin('plant_bird_'+str(k),'potted_plant',[62,80,90],'Tall narrow planter with broad leaves and orange flowers')
 cube('vessel',(x,1.20,.51),(.48,.48,1.02),'concrete',.01)
 for j in range(11):
  a=random.random()*math.tau;hh=random.uniform(1.5,2.3);end=(x+random.uniform(-.35,.35),1.20+random.uniform(-.25,.25),hh)
  tube('stem_'+str(j),[(x,1.2,1),end],.012,'green_leaf')
  c=Vector(end);direction=Vector((math.cos(a)*.25,math.sin(a)*.25,.45));side=Vector((-math.sin(a)*.1,math.cos(a)*.1,0));mesh('blade_'+str(j),[tuple(c),tuple(c+direction*.55+side),tuple(c+direction),tuple(c+direction*.55-side)],[(0,1,2,3)],'leaf_light')
 for j in range(2):
  z=2.30+j*.13;tube('flower_stem_'+str(j),[(x,1.2,1),(x+.06*j,1.2,z)],.01,'green_leaf');mesh('flower_'+str(j),[(x,1.2,z),(x+.16,1.2,z+.08),(x+.03,1.2,z+.24),(x-.03,1.2,z)],[(0,1,2,3)],'orange')
# Reception with irregular faceted stone shell.
begin('reception_desk','reception',[0,45,104,118,135,179],'Angular faceted dark reception counter; back geometry inferred')
vs=[(2.0,16.35,0),(5.3,16.35,0),(5.55,17.25,0),(1.85,17.25,0),(1.7,16.15,.95),(5.6,16.15,.95),(5.3,17.3,.95),(1.85,17.3,.95),(3.45,16.02,.55)]
mesh('faceted_shell',vs,[(0,1,8),(1,5,8),(5,4,8),(4,0,8),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'tabletop')
cube('countertop',(3.65,16.74,.985),(3.95,1.15,.07),'tabletop',.014)
begin('reception_desk_succulents','decor',[0,45,104,135,179],'Three tiny potted succulents on reception counter',collider='none')
for j in range(3):
 cyl('pot_'+str(j),(4.25+j*.13,16.68,1.08),.055,.14,'white_ceramic',20);leaves('plant_'+str(j),(4.25+j*.13,16.68,1.22),.035,20,'leaf_light','grass')
# Abstract horn and shield wall ornament.
begin('reception_wall_art','wall_art',[0,45,118,135,179],'U shaped dark line and white shield wall ornament',collider='none')
tube('horn_outline',[(2.15,17.84,3.36),(2.15,17.84,2.64),(2.32,17.84,2.5),(4.9,17.84,2.5),(5.06,17.84,2.64),(5.06,17.84,3.36)],.018,'black_metal')
mesh('shield',[(3.26,17.80,2.68),(3.94,17.80,2.68),(3.94,17.80,1.93),(3.77,17.80,1.69),(3.59,17.80,1.60),(3.40,17.80,1.70),(3.26,17.80,1.94)],[(0,1,2,3,4,5,6)],'white_ceramic')
# Ten circular mirrors: reflection is the physical room, never another room.
mirrors=[(5.60,2.19,.81),(4.10,1.72,.68),(4.00,3.03,.39),(5.38,3.25,.31),(6.74,2.88,.34),(6.97,2.14,.23),(6.70,1.50,.33),(5.09,1.13,.22),(3.31,2.59,.49),(3.25,1.65,.24)]
for k,(y,z,r) in enumerate(mirrors):
 y+=3.3
 begin('mirror_'+str(k),'mirror',[45,62,80,90,135],'Circular flush mirror with slim metal rim',relations=[{'relation':'mounted_on','target':'wall_east_main'}],collider='none')
 ob=cyl('reflective_disc',(7.238,y,z),r,.018,'mirror',80);ob.rotation_euler[1]=math.pi/2
 # Rim torus lies in yz plane.
 bpy.ops.mesh.primitive_torus_add(major_segments=80,minor_segments=8,location=(7.219,y,z),major_radius=r,minor_radius=.009,rotation=(0,math.pi/2,0));reg(bpy.context.object,'rim','brushed_steel')
# Floor lamps with cylindrical shades and tripod legs.
for k,(x,y) in enumerate([(7.04,16.50),(7.95,14.3),(6.30,.65)]):
 begin('floor_lamp_'+str(k),'floor_lamp',[0,45,80,90,179],'White drum shade on three thin light legs',collider='cylinder')
 for j in range(3):
  a=j*math.tau/3;tube('leg_'+str(j),[(x+.18*math.cos(a),y+.18*math.sin(a),.02),(x+.09*math.cos(a),y+.09*math.sin(a),1.34)],.013,'white_ceramic')
 lathe('shade',(x,y,1.35),[(.27,0),(.27,.50),(.255,.50),(.255,0)],'white_shade')
 cyl('diffuser',(x,y,1.36),.253,.01,'white_shade')
# Pendant bowls distributed in three informal longitudinal rows.
pendants=[(1.55,2.5,.66,4.66),(3.9,2.4,.65,4.53),(6.0,2.7,.73,4.67),(2.0,4.9,.62,4.56),(4.75,5.3,.7,4.45),(6.05,6.5,.60,4.59),(1.8,7.1,.58,4.50),(3.6,7.4,.64,4.63),(5.25,8.1,.59,4.4),(2.0,9.1,.57,4.53),(4.05,9.7,.67,4.58),(5.8,10.7,.61,4.47),(2.1,11.5,.63,4.65),(3.6,12.0,.55,4.40),(5.5,13.1,.57,4.60),(2.2,14.2,.59,4.58),(4.1,14.8,.55,4.50),(5.95,15.5,.65,4.61),(3.0,16.3,.53,4.4),(4.9,16.7,.50,4.53)]
for k,(x,y,r,z) in enumerate(pendants):
 begin('pendant_'+str(k),'pendant_light',[0,45,80,90,104,135,179],'Shallow ribbed suspended luminous bowl; weave approximated procedurally',collider='none')
 profile=[(.19*r,-.24*r),(.34*r,-.22*r),(.57*r,-.14*r),(.81*r,0),(r,.14*r),(r,.17*r),(.80*r,.02*r),(.53*r,-.10*r),(.28*r,-.18*r)]
 lathe('bowl',(x,y,z),profile,'cream_lamp',80)
 # Alternating geometric under-dish tiles: scene-native approximation of visible weave.
 vs=[];fs=[]
 for ring in range(4,19):
  rr=r*ring/19;count=max(24,int(110*rr/r))
  for jj in range(count):
   aa=(jj+(ring%2)*.5)*math.tau/count;dr=r*.025;da=math.pi/count*.78
   zz=z+(.42*(rr/r)**2-.25)*r-.018
   k0=len(vs)
   for rad,ang in [(rr-dr,aa-da),(rr+dr,aa-da),(rr+dr,aa+da),(rr-dr,aa+da)]:vs.append((x+rad*math.cos(ang),y+rad*math.sin(ang),zz))
   fs.append((k0,k0+1,k0+2,k0+3))
 mesh('woven_underside',vs,fs,'brass')
 # Concentric rings reinforce the shallow silhouette.

 for j in range(3,12):
  rr=r*j/12;zz=z+(.42*(rr/r)**2-.25)*r
  bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=6,major_radius=rr,minor_radius=.009,location=(x,y,zz));reg(bpy.context.object,'weave_ring_'+str(j),'cream_lamp')
 cyl('diffuser',(x,y,z-.22*r),.27*r,.014,'lamp_glow',48)
 for j in range(3):
  a=j*math.tau/3;tube('suspension_'+str(j),[(x+.24*r*math.cos(a),y+.24*r*math.sin(a),z),(x+.24*r*math.cos(a),y+.24*r*math.sin(a),H)],.002,'brushed_steel')
# Lighting neutral white exterior, warm emission fixtures.
def area(name,loc,target,power,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size[0];d.size_y=size[1];o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for y in [3,9,15]:area('daylight_'+str(y),(.15,y,3.3),(4.5,y,1.8),500,(4,4))
area('ceiling_fill',(4.1,9,5.05),(4.1,9,0),240,(4,12))
# Camera JSON is authored by prepare_cameras.py; axes RDF -> Blender right, up, backwards.
camera_data=json.loads((ROOT/'cameras.json').read_text())
camd=bpy.data.cameras.new('RGB_camera');cam=bpy.data.objects.new('RGB_camera',camd);scene.collection.objects.link(cam);scene.camera=cam
camd.type='PERSP';camd.sensor_width=36;camd.sensor_fit='HORIZONTAL';camd.lens=762.8*36/1280;camd.clip_start=.05;camd.clip_end=150

def setcam(i):
 f=camera_data['frames'][i];cam.matrix_world=Matrix(f['camera_to_world'])@Matrix.Diagonal((1,-1,-1,1))
setcam(179)
# Bounds from actual geometry after modifiers; every mesh must map to a semantic record.
bpy.context.view_layer.update()
for rec in records.values():
 pts=[]
 for name in rec['component_names']:
  o=bpy.data.objects[name]
  for v in o.bound_box:pts.append(o.matrix_world@Vector(v))
 lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
 rec['bounds']={'min':lo,'max':hi};rec['dimensions']=[hi[i]-lo[i] for i in range(3)]
 rec['physical_parameters']={'mass_kg':None,'friction':.5,'restitution':0,'provenance':'Coefficients are assumptions; no physical measurements supplied.'}
(ROOT/'objects.json').write_text(json.dumps({'objects':list(records.values()),'coordinate_frame':'model','units':'assumed meters'},indent=2))
colliders=[]
for rec in records.values():
 if rec['collider_type']=='none':continue
 if rec['category']=='wall' or rec['id']=='passage_south':
  parts=[]
  for name in rec['component_names']:
   ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
   parts.append({'component_name':name,'type':'box','bounds':{'min':[min(v[k] for v in pts) for k in range(3)],'max':[max(v[k] for v in pts) for k in range(3)]}})
  colliders.append({'object_id':rec['id'],'type':'compound','parts':parts,'door_state':'open passage retained; closed door leaves have separate records'})
 else:colliders.append({'object_id':rec['id'],'type':rec['collider_type'],'bounds':rec['bounds'],'approximation':'Conservative furniture bounds; not contact-accurate physics geometry'})
(ROOT/'colliders.json').write_text(json.dumps({'colliders':colliders,'units':'assumed meters','status':'compound walls preserve openings; furniture approximate'},indent=2))
(ROOT/'layout.json').write_text(json.dumps({'coordinate_frame':'arbitrary inferred metric-like scene','axes':{'x':'from glazing toward panelled wall','y':'toward reception','z':'up'},'room':{'width':W,'length':L,'height':H,'east_main_wall_x':7.35,'east_recess_start_y':13.8},'scale_provenance':'Assumed chair diameter about 0.8 m and door height about 2.1 m. Monocular images do not determine metric scale.','objects':{k:{'bounds':v['bounds'],'category':v['category']} for k,v in records.items()}},indent=2))
(ROOT/'analysis/object_inventory.json').write_text(json.dumps({'inventory':[{k:v[k] for k in ['id','category','description','evidence_sample_ids','provenance','uncertainty','spatial_relations']} for v in records.values()]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'scene.glb'),export_format='GLB',export_yup=True,export_cameras=False,export_lights=False)
# Track attempts before invoking renderer; a failed render still consumes budget.
logpath=ROOT/'iteration_log.json'
log=json.loads(logpath.read_text()) if logpath.exists() else {'versions':[],'render_attempts':[],'limits':{'scene_versions':5,'checking_renders':60}}
log['versions'].append({'version':VERSION,'build_elapsed_seconds':time.time()-START,'description':'Initial semantic scene inferred from RGB' if VERSION==1 else 'v2 independent review repairs: openings, compound colliders, support, layout and appearance','complete':True})
if DO_RENDER:
 for i in [0,45,90,135,179]:
  setcam(i);scene.render.filepath=str(ROOT/f'checks/v{VERSION}_{i:04d}.png')
  entry={'version':VERSION,'sample_index':i,'filepath':scene.render.filepath,'engine':'CPU Cycles','samples':12,'resolution':[640,480],'threads':4,'status':'attempted'};log['render_attempts'].append(entry);logpath.write_text(json.dumps(log,indent=2))
  ts=time.time()
  try:bpy.ops.render.render(write_still=True);entry['status']='completed'
  except Exception as e:entry['status']='failed';entry['error']=str(e)
  entry['elapsed_seconds']=time.time()-ts;logpath.write_text(json.dumps(log,indent=2))
logpath.write_text(json.dumps(log,indent=2))
manifest={'method_id':'M1','model_id':'gpt-6-astra','status':'ready_for_independent_review','quality_status':'limited','model_from_input':None,'geometry_scale':{'type':'inferred','units':'assumed meters','metric_observable':False,'anchor':'Typical 0.8 m lounge seat diameter and 2.1 m internal door height','confidence':'low'},'coordinate_frame':'arbitrary RGB-inferred model frame','revisions':VERSION,'checking_render_count':len(log['render_attempts']),'unresolved_issues':['Monocular global scale is unconstrained; dimensions are inferred.','Only a sparse set of cameras is manually constrained; intermediate poses are illustrative and invalid for evaluation.','Topology and object inventory are inferred; hidden surfaces and exact repeated fixture count uncertain.','Procedural materials, lighting, plant forms and fixture weave approximate appearance.','Detailed collision geometry and physical properties are not measured.'],'input_packet_sha256':hashlib.sha256((INPUT/'packet.json').read_bytes()).hexdigest(),'ground_truth_used':False,'prior_scene_used':False,'external_sfm_slam_depth_models_used':False,'independent_review':'pending','authoring_seconds':time.time()-START}
(ROOT/'modelling_manifest.json').write_text(json.dumps(manifest,indent=2))
print('M1_BUILD_COMPLETE',len(records),'objects',len(log['render_attempts']),'render attempts',time.time()-START)
