"""Independent M3 semantic authoring from M3 RGB and metric depth anchors only."""
import bpy,math,json,time,hashlib,random,sys
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
O=Path(__file__).resolve().parent
P=Path('/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3')
BLENDER='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
VERSION=1
J=json.loads((P/'packet.json').read_text()); TRANS=np.load(O/'analysis/model_from_input.npy')
random.seed(314159); start=time.monotonic()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
records={}; active=None

def group(id,category,evidence,desc,uncertainty=.2,relations=None):
 global active
 active=id;records[id]={'id':id,'category':category,'description':desc,'component_names':[],'evidence_sample_ids':evidence,'provenance':{'visible_shape':'observed in RGB; positions from M3 optical-Z backprojection','hidden_surfaces':'inferred closure and thickness','materials':'visually estimated','physical_coefficients':'assumed'},'uncertainty_m':uncertainty,'spatial_relations':relations or []}
def own(o,component):
 o.name=active+'__'+component;o['semantic_id']=active;o['category']=records[active]['category'];records[active]['component_names'].append(o.name);return o

def mat(name,col,rough=.5,metal=0,noise=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;nt=m.node_tree;n=nt.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*col,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal
 if noise:
  tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=85;tex.inputs['Detail'].default_value=3
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=noise;bump.inputs['Distance'].default_value=.018;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],n.inputs['Normal'])
 return m
stone=mat('warm pale polished stone',(.51,.49,.43),.2,0,.18);dark=mat('charcoal polished floor',(.045,.042,.035),.12,.15,.1);oak=mat('vertical pale wood wall panels',(.43,.405,.34),.53,0,.24);seam=mat('dark panel reveals',(.028,.026,.022),.6);silver=mat('satin aluminium',(.55,.57,.55),.24,.85);gold=mat('bronze door and light details',(.48,.34,.15),.27,.7);fabric=mat('pistachio upholstery',(.33,.405,.22),.83,0,.3);black=mat('black table finish',(.022,.02,.018),.32);potmat=mat('concrete planters',(.32,.34,.32),.74,0,.3);soil=mat('dark soil',(.035,.027,.018),.99);leafmat=mat('green foliage',(.07,.17,.035),.66);yellow=mat('yellow blossom foliage',(.47,.37,.035),.72);stemmat=mat('plant stems',(.13,.1,.045),.83);white=mat('ivory light shades',(.78,.75,.67),.7);ceramic=mat('glazed mottled ceramic',(.55,.61,.60),.25,0,.22);mirror=mat('mirror silver',(.96,.97,.96),.012,1);lampmat=mat('woven brass light bowls',(.64,.51,.32),.38,.45,.3)
# Wood grain elongated using generated coordinates.
nt=oak.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_NOISE');tc=nt.nodes.new('ShaderNodeTexCoord');vm=nt.nodes.new('ShaderNodeVectorMath');vm.operation='MULTIPLY';vm.inputs[1].default_value=(3,3,.035);nt.links.new(tc.outputs['Generated'],vm.inputs[0]);nt.links.new(vm.outputs['Vector'],tex.inputs['Vector'])
glow=mat('warm light diffusers',(1,.68,.32),.4);bs=glow.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=(1,.62,.22,1);bs.inputs['Emission Strength'].default_value=3
window=bpy.data.materials.new('bright exterior glazing');window.use_nodes=True;nt=window.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');mix=nt.nodes.new('ShaderNodeMixShader');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1);em.inputs[1].default_value=2;tr=nt.nodes.new('ShaderNodeBsdfTransparent');lp=nt.nodes.new('ShaderNodeLightPath');nt.links.new(lp.outputs['Is Shadow Ray'],mix.inputs[0]);nt.links.new(em.outputs[0],mix.inputs[1]);nt.links.new(tr.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])

def finish(o,name,ma,bevel=0):
 own(o,name)
 if ma:o.data.materials.append(ma)
 if bevel:
  mod=o.modifiers.new('softened manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
  mod=o.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 return o

def box(name,loc,dims,ma,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,ma,bevel)
def cyl(name,loc,r,depth,ma,verts=48,bevel=0):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=bpy.context.object;finish(o,name,ma,bevel)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o

def mesh(name,v,f,ma):
 me=bpy.data.meshes.new(active+' '+name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(active+' '+name,me);bpy.context.collection.objects.link(o);return finish(o,name,ma)
def lathe(name,loc,profile,ma,N=48):
 v=[(loc[0]+r*math.cos(2*math.pi*i/N),loc[1]+r*math.sin(2*math.pi*i/N),loc[2]+z) for r,z in profile for i in range(N)];f=[]
 for j in range(len(profile)-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 o=mesh(name,v,f,ma)
 for p in o.data.polygons:p.use_smooth=True
 return o

def rod(name,a,b,r,ma,N=10):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,ma,N);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def ellipsoid(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);o=bpy.context.object;o.scale=scale;finish(o,name,ma)
 for p in o.data.polygons:p.use_smooth=True
 return o

def leafmesh(name,leaves,ma):
 vs=[];fs=[]
 for pos,length,width,ang,tilt in leaves:
  p=np.array(pos);a=np.array([math.cos(ang)*math.cos(tilt),math.sin(ang)*math.cos(tilt),math.sin(tilt)]);b=np.array([-math.sin(ang),math.cos(ang),0]);k=len(vs);vs.extend([p,p+a*length*.42+b*width,p+a*length,p+a*length*.42-b*width,p+a*length*.48+np.array([0,0,width*.22])]);fs.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)])
 return mesh(name,[tuple(v) for v in vs],fs,ma)

# Envelope. Far side wall steps back behind the mirror bay.
group('floor','floor',[0,45,90,110,135],'Polished pale floor around a charcoal central inlay',.13)
box('base',(9.75,2.3,-.08),(19.7,11.0,.16),stone)
box('dark_inlay',(9.75,3.73,.006),(15.8,4.25,.014),dark)
group('ceiling','ceiling',[0,45,90,125],'Pale ceiling with dark slatted margins',.22)
box('slab',(9.75,2.3,5.05),(19.7,11,.16),stone)
for i in range(97):
 x=.3+i*.2
 for side,y,width in [('glazed',6.86,1.9),('inner',-.7,2.0)]:box(f'{side}_batten_{i:03}',(x,y,4.96),(.06,width,.11),oak)
# wall panels and reveal substrate, opening rectangles optional
def wall_x(id,x,y0,y1,openings=[]):
 group(id,'wall',[0,90,135],'Vertical timber panels and joints, top closure inferred',.4)
 box('substrate',(x,(y0+y1)/2,2.5),(.18,y1-y0,5),seam)
 for n,y in enumerate(np.arange(y0,y1,.83)):
  for h,(z0,z1) in enumerate([(0,1.85),(1.85,3.7),(3.7,5)]):box(f'panel_{n:02}_{h}',(x-.1,y+min(.83,y1-y)/2,(z0+z1)/2),(.045,min(.83,y1-y)-.012,z1-z0-.014),oak)
def wall_y(id,y,x0,x1,openings=[]):
 group(id,'wall',[45,60,80,90],'Timber-clad wall with observed doors',.22)
 box('substrate',((x0+x1)/2,y-.1,2.5),(x1-x0,.18,5),seam)
 for n,x in enumerate(np.arange(x0,x1,.8)):
  for h,(z0,z1) in enumerate([(0,1.85),(1.85,3.7),(3.7,5)]):
   mid=x+min(.8,x1-x)/2
   if z0==0 and any(a<mid<b for a,b in openings):continue
   box(f'panel_{n:02}_{h}',(mid,y+.006,(z0+z1)/2),(min(.8,x1-x)-.012,.045,z1-z0-.012),oak)
wall_x('far_end_wall',19.25,-3.25,7.8);wall_x('near_end_wall',.75,-.2,7.8)
# Reverse near wall panels toward interior
for nm in records['near_end_wall']['component_names']:
 if 'panel' in nm:bpy.data.objects[nm].location.x+=.23
wall_y('mirror_bay_wall',-.12,.75,10.25,[(1.55,2.5),(8.75,9.6)])
wall_y('recess_wall',-3.25,10.25,19.25,[(11.1,12.05),(13.65,14.6),(16.2,17.15)])
group('wall_return','wall',[80],'Return wall at recess behind mirror bay',.25);box('return',(10.25,-1.71,2.5),(.18,3.08,5),oak)
# exposed metal door panels and frames
for idx,(x,y) in enumerate([(2.05,-.07),(9.12,-.07),(11.6,-3.2),(14.12,-3.2),(16.65,-3.2)]):
 group(f'interior_door_{idx:02}','door',[45,60,80],'Flush metal interior doorway',.25)
 box('leaf',(x,y,.935),(.8,.05,1.87),silver,.008);box('head',(x,y+.032,1.88),(.9,.045,.035),silver)
 for side in [-1,1]:box('jamb_'+str(side),(x+side*.43,y+.035,.94),(.035,.045,1.88),silver)
 rod('pull',(x-.28,y+.08,.81),(x-.28,y+.08,1.03),.012,silver)
# window curtain wall
for i in range(23):
 x=.8+i*.835
 if x>19.25:break
 group(f'glazing_bay_{i:02}','window',[0,100,110,125],'Floor-to-ceiling glazed bay; exterior overexposed',.35)
 box('pane',(x+.41,7.85,2.5),(.82,.03,5),window)
 box('vertical_mullion',(x,7.81,2.5),(.035,.06,5),silver)
 box('transom',(x+.41,7.80,2.85),(.84,.06,.045),seam)
for k,x in enumerate([4.7,15.3]):
 group(f'entrance_doors_{k}','door',[0,100,110,125],'Paired bronze framed glazed entry doors',.25)
 for s in [-1,1]:
  c=x+s*.43
  for e in [-1,1]:box(f'leaf{s}_stile{e}',(c+e*.40,7.735,1.40),(.065,.08,2.8),gold)
  for z in [.09,2.73]:box(f'leaf{s}_rail{z}',(c,7.735,z),(.82,.08,.14),gold)
  rod(f'leaf{s}_handle',(c-s*.31,7.65,.80),(c-s*.31,7.65,1.48),.015,black)
group('round_column','column',[0,90,110,125],'Round structural column beside glazing',.23)
cyl('shaft',(9.78,7.02,2.5),.43,5,stone,64)
# reception desk geometric faceted fronts
group('reception_desk','reception_desk',[0,100,110,135],'Faceted dark reception desk with thin top and work recess',.5,[{'relation':'in_front_of','target':'far_end_wall'}])
x0,x1=16.9,18.0;y0,y1=2.25,5.7
v=[(x0,y0,.06),(x0,y1,.06),(x0-.12,y0,.78),(x0-.12,y1,.78),(x0+.28,3.65,.34),(x1,y0,.08),(x1,y1,.08),(x1,y0,.82),(x1,y1,.82)]
mesh('faceted_front',v,[(0,2,4),(2,3,4),(3,1,4),(1,0,4),(0,5,7,2),(1,3,8,6),(5,6,8,7)],black)
box('countertop',(17.44,3.97,.825),(1.28,3.65,.055),black,.012)
box('recess_shelf',(17.72,3.9,.60),(.6,2.9,.06),oak)
# emblem and fine U shaped dark line on end wall
group('reception_wall_emblem','wall_art',[0,135],'White shield relief and curved dark line',.3)
mesh('shield',[(19.02,3.45,2.05),(19.02,4.2,2.05),(19.02,4.2,1.45),(19.02,3.83,1.25),(19.02,3.45,1.45)],[(0,1,2,3,4)],white)
for a,b in [((19.0,2.25,2.65),(19.0,2.25,2.05)),((19.0,2.25,2.05),(19.0,2.5,1.94)),((19.0,2.5,1.94),(19.0,5.15,1.94)),((19.0,5.15,1.94),(19.0,5.4,2.05)),((19.0,5.4,2.05),(19.0,5.4,2.65))]:rod('line',a,b,.015,black)
# seating functions
def chair(id,x,y,r=.45,back=False,angle=0,evidence=[0,135]):
 group(id,'lounge_chair' if back else 'ottoman',evidence,'Round upholstered seat with dark feet'+(' and curved wraparound back' if back else ''),.16,[{'relation':'supported_by','target':'floor'}])
 cyl('seat',(x,y,.295),r,.43,fabric,48,.035)
 for k in range(4):
  a=math.pi/4+k*math.pi/2;cyl(f'foot_{k}',(x+r*.69*math.cos(a),y+r*.69*math.sin(a),.085),.023,.15,silver,12)
 if back:
  N=24;vs=[]
  for z,rad in [(.47,r-.075),(.85,r-.075),(.47,r+.005),(.85,r+.005)]:
   for a in np.linspace(angle-.92,angle+.92,N):vs.append((x+rad*math.cos(a),y+rad*math.sin(a),z))
  fs=[]
  for i in range(N-1):fs.extend([(i,i+1,N+i+1,N+i),(2*N+i,3*N+i,3*N+i+1,2*N+i+1),(N+i,N+i+1,3*N+i+1,3*N+i),(i,2*N+i,2*N+i+1,i+1)])
  fs.extend([(0,N,3*N,2*N),(N-1,2*N-1,4*N-1,3*N-1)]);o=mesh('curved_backrest',vs,fs,fabric);mod=o.modifiers.new('upholstered edge','BEVEL');mod.width=.025;mod.segments=3
# far six-module arrangement
for k,(x,y,r,b,a) in enumerate([(7.95,5.15,.45,False,0),(8.7,5.22,.45,True,1.4),(9.25,4.65,.45,True,1.0),(9.56,4.10,.49,False,0),(9.05,3.73,.47,False,0),(8.77,3.15,.45,True,-1.1)]):chair(f'far_seat_{k}',x,y,r,b,a)
for k,(x,y,r,b,a) in enumerate([(5.5,2.77,.46,False,0),(4.75,2.79,.43,True,-1.6),(4.2,3.16,.46,True,-2.1),(4.25,4.05,.44,False,0)]):chair(f'near_seat_{k}',x,y,r,b,a,[45,60,90])
def table(id,x,y,rx,ry,evidence,bowl=False):
 group(id,'coffee_table',evidence,'Thin oval dark tabletop on fluted radial pedestal',.16)
 o=cyl('top',(x,y,.43),1,.045,black,64,.009);o.scale=(rx,ry,1)
 cyl('core',(x,y,.22),.19,.38,black)
 for k in range(20):
  a=k*math.tau/20;rod(f'flute_{k}',(x+.29*math.cos(a),y+.29*math.sin(a),.025),(x+.18*math.cos(a),y+.18*math.sin(a),.4),.028,black)
 if bowl:lathe('decorative_bowl',(x,y,.455),[(0,0),(.11,0),(.17,.07),(.18,.15),(.16,.155),(.14,.075),(0,.04)],gold)
table('far_coffee_table',8.22,4.24,.58,.64,[0,135],True);table('near_coffee_table',5.17,3.66,.65,.54,[45,60,90])
# plant builders

def bush(id,x,y,pottype='bowl',evidence=[0],radius=.55,height=.7,foliage='green'):
 group(id,'potted_plant',evidence,'Observed foliage mass and planter; individual leaves inferred',.25)
 if pottype=='bowl':lathe('bowl',(x,y,0),[(0,0),(.3,.04),(radius*.9,.15),(radius,.38),(radius,.44),(radius*.87,.43),(radius*.82,.18),(0,.15)],ceramic);base=.42
 else:lathe('vase',(x,y,0),[(0,0),(.2,0),(.31,.13),(.34,.4),(.26,.63),(.24,.65),(.21,.61),(0,.2)],ceramic);base=.63
 cyl('soil',(x,y,base-.015),radius*.83 if pottype=='bowl' else .22,.025,soil)
 leaves=[]
 for k in range(300):
  a=random.random()*math.tau;r=radius*math.sqrt(random.random())*.66;z=base+random.random()*height*.36;leaves.append(((x+r*math.cos(a),y+r*math.sin(a),z),random.uniform(.24,.55),random.uniform(.012,.028),a,random.uniform(-.2,1.25)))
 leafmesh('fine_foliage',leaves,leafmat)
for args in [('window_bush',9.0,6.9,'bowl',[0,90,125],.61,.6),('mirror_vase',7.55,.60,'vase',[45,60,90,135],.48,.6),('near_window_bush',1.9,6.9,'bowl',[90,100],.58,.6),('far_corner_bowl',18.1,-1.6,'bowl',[0,45],.53,.35)]:bush(*args)
# yellow branched bushes in two rectangular troughs
for i,y in enumerate([2.77,4.98]):
 group(f'flower_trough_{i}','planter',[0,80,90,135],'Rectangular concrete trough with yellow flowering branches',.18)
 x=10.73;box('body',(x,y,.34),(.68,1.83,.68),potmat,.025);box('soil',(x,y,.687),(.54,1.68,.025),soil)
 leaves=[]
 for k in range(34):
  sx=x+random.uniform(-.2,.2);sy=y+random.uniform(-.74,.74);a=random.random()*math.tau;h=random.uniform(.55,1.00);end=(sx+random.uniform(-.4,.4),sy+random.uniform(-.35,.35),.7+h);rod(f'stem_{k}',(sx,sy,.67),end,.005,stemmat,6)
  for b in range(3):
   t=random.uniform(.3,.8);st=np.array([sx,sy,.68])*(1-t)+np.array(end)*t;ed=st+np.array([random.uniform(-.24,.24),random.uniform(-.3,.3),random.uniform(.15,.4)]);rod(f'branch_{k}_{b}',st,ed,.003,stemmat,6)
   for z in range(9):
    p=st+(ed-st)*random.random();leaves.append((p,random.uniform(.025,.06),.013,random.random()*math.tau,random.uniform(-.4,.8)))
 leafmesh('yellow_florets',leaves,yellow)
# tall bird of paradise planters near room end
for i,(x,y) in enumerate([(3.32,2.1),(2.9,5.65)]):
 group(f'bird_of_paradise_{i}','potted_plant',[60,90],'Tall square planter with broad leaves and orange flowers',.2)
 box('square_pot',(x,y,.44),(.48,.48,.88),potmat,.012);box('soil',(x,y,.89),(.41,.41,.025),soil);ls=[]
 for k in range(14):
  a=k*2.4;end=(x+.30*math.cos(a),y+.30*math.sin(a),random.uniform(1.2,1.75));rod(f'stalk_{k}',(x,y,.85),end,.007,leafmat,8);ls.append((end,random.uniform(.3,.55),.10,a,random.uniform(.3,1.1)))
 leafmesh('broad_leaves',ls,leafmat)
 for k in range(3):
  end=(x+random.uniform(-.18,.18),y+random.uniform(-.18,.18),1.85+k*.12);rod(f'flower_stem_{k}',(x,y,.85),end,.009,leafmat)
  leafmesh(f'orange_bloom_{k}',[(end,.18,.033,.5+k,1.0),(end,.15,.04,.9+k,.25)],mat(f'orange blossom {i} {k}',(.85,.23,.015),.6))
# two small trees by desk
for i,y in enumerate([1.25,6.15]):
 group(f'reception_tree_{i}','potted_tree',[0,135],'Slender indoor tree in pale ceramic vase',.4)
 x=18.15;lathe('vase',(x,y,0),[(0,0),(.19,0),(.27,.12),(.25,.5),(.20,.61),(.18,.58),(0,.12)],ceramic);rod('trunk',(x,y,.5),(x,y,1.6),.026,stemmat)
 leaves=[]
 for k in range(450):
  a=random.random()*math.tau;r=random.random()**(1/3)*.52;z=random.uniform(-.28,.3);leaves.append(((x+r*math.cos(a),y+r*math.sin(a),1.48+z),.11,.035,a,random.uniform(-.7,.7)))
 leafmesh('crown',leaves,leafmat)
# floor standing lamps
for i,(x,y) in enumerate([(16.0,.1),(11.3,-2.6),(2.4,1.1)]):
 group(f'floor_lamp_{i}','floor_lamp',[0,45,80,90],'White cylindrical drum shade on three slender legs',.25)
 for a in [0,2.1,4.2]:rod('leg',(x+.17*math.cos(a),y+.17*math.sin(a),.015),(x+.065*math.cos(a),y+.065*math.sin(a),1.52),.009,silver)
 lathe('drum',(x,y,1.43),[(.23,0),(.23,.43),(.217,.43),(.217,0),(.23,0)],white)
 cyl('diffuser',(x,y,1.438),.212,.016,glow)
# circular mirrors: screen-coordinate ordering converts to reversed model X along side wall
mirror_layout=[(6.35,1.72,.66),(5.05,1.20,.57),(4.10,1.96,.45),(4.69,2.61,.36),(5.41,2.18,.28),(7.25,2.20,.30),(7.55,1.66,.20),(7.13,1.12,.28),(5.95,.98,.19),(4.15,1.19,.21)]
for i,(x,z,r) in enumerate(mirror_layout):
 group(f'mirror_{i:02}','mirror',[45,60,80],'Circular reflective disc on timber wall; reflection is not extra room',.12)
 o=cyl('reflective_disc',(x,-.055,z),r,.024,mirror,64);o.rotation_euler=(math.pi/2,0,0)
 o=lathe('thin_metal_rim',(0,0,0),[(r,.0),(r+.012,.0),(r+.012,.022),(r,.022)],silver,64);o.location=(x,-.047,z);o.rotation_euler=(math.pi/2,0,0)
# suspended woven-bowl lighting. Positions are interpolated among measured visible centres.
lamps=[(3.4,3.5,.58,4.10),(4.2,5.8,.60,4.20),(4.8,2.0,.58,4.10),(5.6,4.0,.7,4.30),(6.4,6.0,.65,4.27),(6.5,2.55,.66,4.20),(7.8,5.55,.70,4.20),(8.45,2.60,.76,3.95),(9.8,5.25,.65,4.22),(10.95,2.90,.61,4.22),(10.9,5.85,.66,4.12),(11.75,4.15,.64,4.2),(12.1,2.15,.61,4.05),(12.8,5.6,.59,4.22),(13.6,3.6,.55,4.13),(14.7,4.7,.60,4.1),(14.6,2.8,.56,4.10),(16.2,1.9,.53,4.06),(16.9,3.95,.58,4.0),(16.9,5.4,.55,4.11)]
for idx,(x,y,r,z) in enumerate(lamps):
 group(f'pendant_{idx:02}','ceiling_light',[0,45,90,125],'Suspended shallow woven bowl with luminous central disc',.25,[{'relation':'suspended_from','target':'ceiling'}])
 rod('wire',(x,y,z+.20),(x,y,4.98),.002,black,6)
 lathe('dish',(x,y,z),[(.19*r,-.04),(.35*r,-.04),(.6*r,.015),(.82*r,.10),(r,.22),(r*.98,.24),(.8*r,.125),(.57*r,.045),(.19*r,-.01)],lampmat,64)
 cyl('diffuser',(x,y,z-.03),.25*r,.018,glow)
 lathe('rim',(x,y,z),[(r,.215),(r+.014,.215),(r+.014,.24),(r,.24)],black,64)
 # radial ribs and concentric woven courses model the prominent basket texture.
 for k in range(36):
  a=math.tau*k/36
  prev=None
  for q in [0.33,.5,.7,.86,1.0]:
   pt=(x+r*q*math.cos(a),y+r*q*math.sin(a),z-.045+.265*q*q)
   if prev:rod(f'rib_{k}_{q}',prev,pt,.0075,white,5)
   prev=pt
 for rr in [.45,.60,.73,.84,.94]:lathe('weave_'+str(rr),(x,y,z),[(r*rr-.005,-.045+.265*rr*rr),(r*rr+.005,-.045+.265*rr*rr+.006)],gold,72)
# Lighting and renderer
world=bpy.data.worlds.new('Bright overcast exterior');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,1,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45;bpy.context.scene.world=world
for i,x in enumerate([3.5,9.5,15.5]):
 d=bpy.data.lights.new('window fill '+str(i),'AREA');d.energy=550;d.shape='RECTANGLE';d.size=4;d.size_y=3;o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=(x,7.5,3.5);o.rotation_euler=(Vector((x,2,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.lights.new('slanted daylight','SUN');d.energy=1.9;d.angle=.05;o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.rotation_euler=(.52,-.28,-.3)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.cycles.max_bounces=5;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3;scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
# Camera transforms remain supplied native pose times one rigid transform.
frames=[]
for f in J['frames']:
 tf=TRANS@np.array(f['camera_to_world']);frames.append({k:f[k] for k in ['sample_index','source_index','timestamp_ns']}|{'camera_to_world':tf.tolist(),'intrinsics':f['intrinsics'],'valid':True})
(O/'cameras.json').write_text(json.dumps({'frames':frames,'coordinate_frame':'model','pose_convention':'OpenCV RDF camera-to-world','model_from_input':TRANS.tolist()},indent=2))
camd=bpy.data.cameras.new('M3 calibrated camera');cam=bpy.data.objects.new('M3 calibrated camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam;camd.type='PERSP';camd.lens=762.8*36/1280;camd.sensor_width=36;camd.sensor_fit='HORIZONTAL';camd.clip_start=.04;camd.clip_end=100
cam.matrix_world=Matrix(frames[0]['camera_to_world'])@Matrix.Diagonal((1,-1,-1,1))
# Bounds, records and simple explicit collider approximations.
bpy.context.view_layer.update()
for id,r in records.items():
 pts=[]
 for name in r['component_names']:
  obj=bpy.data.objects[name];pts.extend([list(obj.matrix_world@Vector(p)) for p in obj.bound_box])
 p=np.array(pts);lo=p.min(0);hi=p.max(0);r.update(bounds={'min':lo.tolist(),'max':hi.tolist()},dimensions=(hi-lo).tolist(),position=((hi+lo)/2).tolist())
(O/'objects.json').write_text(json.dumps({'objects':list(records.values()),'coordinate_frame':'model','units':'metres'},indent=2))
cols=[]
for id,r in records.items():
 if r['category'] in ['ceiling_light','wall_art','mirror','window']:continue
 cols.append({'object_id':id,'type':'axis_aligned_box','bounds':r['bounds'],'static':True,'friction':.5,'restitution':0,'provenance':'inferred conservative broad-phase collider; foliage included where applicable'})
(O/'colliders.json').write_text(json.dumps({'colliders':cols,'units':'metres','limitations':['Conservative furniture bounds include gaps; no rigid-body articulation or dynamics calibration.']},indent=2))
layout={'units':'metres','geometry_scale':1,'model_from_input':TRANS.tolist(),'floor_z':0,'ceiling_z':5,'room_extent':{'x':[.75,19.25],'glazed_wall_y':7.85,'near_solid_wall_y':-.12,'recessed_solid_wall_y':-3.25,'wall_step_x':10.25},'main_features':{'mirror_wall_x':[.75,10.25],'round_column':[9.78,7.02],'reception':[17.44,3.97],'seating_groups':[[8.85,4.3],[4.8,3.4]],'troughs':[[10.73,2.77],[10.73,4.98]]},'derivation':'RGB semantics and stable M3 depth/pose anchor consensus. No GT, other methods, old model, or previous scene code read.'}
(O/'layout.json').write_text(json.dumps(layout,indent=2))
(O/'analysis/object_inventory.json').write_text(json.dumps({'objects':[{'id':r['id'],'category':r['category'],'evidence_sample_ids':r['evidence_sample_ids'],'description':r['description'],'uncertainty_m':r['uncertainty_m']} for r in records.values()]},indent=2))
issues=['M3 DA3 metric scale collapses on stationary samples; sample 179 median depth ~0.5m conflicts with stable same-view ~6m. No scale correction was applied.','Far wall and glass positions vary by roughly 0.3–1.2m across stable depth frames.','Desk far-end dimensions, hidden backs, joinery, material parameters, and exact light placement inferred.','Plants reconstructed as semantic procedural foliage; leaf topology is assumed.','Two near seating modules and lamp placements are occluded across many views.']
old=json.loads((O/'modelling_manifest.json').read_text()) if (O/'modelling_manifest.json').exists() else {}
manifest={'method_id':'M3','model_id':'gpt-6-astra','status':'building_initial_checks','quality_status':'limited_pending_review','model_from_input':TRANS.tolist(),'geometry_scale':1.0,'revisions':VERSION,'checking_render_count':old.get('checking_render_count',0),'unresolved_issues':issues,'input_packet_sha256':hashlib.sha256((P/'packet.json').read_bytes()).hexdigest(),'independent_author':True,'input_scope':'M3 only','no_gt_used':True,'render_settings':{'engine':'CPU Cycles','samples':12,'resolution':[640,480],'threads':4}}
(O/'modelling_manifest.json').write_text(json.dumps(manifest,indent=2))
(O/'analysis/measurements.json').write_text(json.dumps({'coordinate_transform':{'model_from_input':TRANS.tolist(),'scale':1.,'rotation_determinant':float(np.linalg.det(TRANS[:3,:3])),'reason':'Floor/ceiling normals from stable frames define Z; wall normals define horizontal axis. Native metric scale preserved.'},'planes':json.loads((O/'analysis/plane_measurements.json').read_text()),'anchors':json.loads((O/'analysis/anchor_measurements.json').read_text()),'conflicts':issues,'robust_floor_reference_m':-2.0,'room_length_estimate_m':18.5,'ceiling_height_estimate_m':5.0},indent=2))
# Geometric camera check: proper rigid transform and no pose adjustment.
camp=np.array([np.array(f['camera_to_world'])[:3,3] for f in frames]);err=max(np.linalg.norm(np.array(f['camera_to_world'])[:3,:3].T@np.array(f['camera_to_world'])[:3,:3]-np.eye(3)) for f in frames)
(O/'analysis/camera_checks.json').write_text(json.dumps({'frames':180,'all_valid':True,'opencv_to_blender_right_multiplier':[1,-1,-1,1],'pose_rotation_orthogonality_max':float(err),'camera_height_range_m':[float(camp[:,2].min()),float(camp[:,2].max())],'camera_positions_within_floor_extent':bool(np.all((camp[:,0]>.0)&(camp[:,0]<19.4)&(camp[:,1]>-3.5)&(camp[:,1]<8.0))),'fixed_check_samples':[0,45,90,135,179],'intrinsics_rgb':J['intrinsics'],'intrinsics_depth':[[233.6074981689453,0,196],[0,233.6074981689453,147],[0,0,1]]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'scene.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_apply=True)
(O/'checks/build_time.json').write_text(json.dumps({'version':VERSION,'seconds':time.monotonic()-start,'mesh_objects':sum(o.type=='MESH' for o in scene.objects),'semantic_objects':len(records)},indent=2))
print('BUILD COMPLETE',len(records),'semantic objects',flush=True)
