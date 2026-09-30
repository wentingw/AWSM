"""Independent M2 semantic model, authored from supplied RGB + metric depth and native poses.
Run Blender --background --factory-startup --threads 4 --python-exit-code 1 --python this.py.
Only this output directory and the assigned M2 packet are read. No reconstruction mesh imported.
"""
import bpy, math, json, random, time, hashlib, sys
from pathlib import Path
from mathutils import Matrix,Vector
from math import sin,cos,pi
O=Path(__file__).resolve().parent
P=O.parent.parent/'inputs/M2'
J=json.load(open(P/'packet.json'))
T=json.load(open(O/'analysis/transform.json'))
M=Matrix(T['model_from_input'])
VERSION=2
random.seed(6202)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.2,.2,.2);scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.8,.85,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.18
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.35
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.cycles.max_bounces=6;scene.cycles.transmission_bounces=3
records=[];current=None

def material(name,color,rough=.5,metal=0,noise=None,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes;links=m.node_tree.links;b=n.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 if emission:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emission
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=noise;tex.inputs['Detail'].default_value=2
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[0].color=(*(x*.68 for x in color),1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*(min(1,x*1.15) for x in color),1);links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],b.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.015;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],b.inputs['Normal'])
 return m
stone=material('warm pale terrazzo',(0.53,.51,.44),.22,noise=180)
wall=material('vertical pale oak panels',(.43,.41,.33),.55)
n=wall.node_tree.nodes;l=wall.node_tree.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5;tex.inputs['Detail'].default_value=3;coord=n.new('ShaderNodeTexCoord');vec=n.new('ShaderNodeVectorMath');vec.operation='MULTIPLY';vec.inputs[1].default_value=(22,22,.38);l.new(coord.outputs['Generated'],vec.inputs[0]);l.new(vec.outputs[0],tex.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.23,.21,.16,1);r.color_ramp.elements[1].color=(.56,.54,.46,1);l.new(tex.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],n['Principled BSDF'].inputs['Base Color']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.008;l.new(tex.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],n['Principled BSDF'].inputs['Normal'])
charcoal=material('charcoal joinery',(.035,.033,.027),.43)
black=material('black table satin',(.033,.031,.027),.32)
metal=material('dark bronze metal',(.12,.105,.075),.27,.7)
brass=material('brass door edging',(.43,.34,.15),.22,.8)
chrome=material('brushed stainless steel',(.52,.57,.58),.22,.9)
mirror=material('true circular reflective mirror',(.96,.98,1),.025,1)
green=material('sage woven upholstery',(.28,.36,.17),.82,noise=150)
cement=material('fine gray planter concrete',(.25,.26,.25),.68,noise=100)
ceramic=material('blue white mottled ceramic',(.45,.55,.57),.3,noise=8)
soil=material('dark soil',(.035,.026,.012),1,noise=40)
leaf=material('living leaf green',(.10,.20,.046),.7)
leaflight=material('grass highlights',(.22,.32,.087),.7)
yellow=material('ochre gold flowering branches',(.52,.36,.04),.7)
wood=material('branch bark',(.12,.085,.035),.85)
linen=material('ivory fabric shades',(.72,.74,.65),.7)
ceilingmat=material('pale plaster ceiling',(.60,.59,.54),.85,noise=20)
woven=material('woven brass bronze light',(.56,.43,.24),.38,.45,noise=65)
emit=material('warm lamp diffuser',(1,.66,.28),.3,emission=3)
glazing=material('overexposed frosted exterior glazing',(.98,1,1),.35,emission=1.4)
# Polished dark inset: shallow periodic material relief represents visible reflection distortion.
floorblack=material('polished black inset',(.015,.014,.011),.055,.25)
n=floorblack.node_tree.nodes;l=floorblack.node_tree.links;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=170;tex.inputs['Roughness'].default_value=.8;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.025;bump.inputs['Distance'].default_value=.003;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],n['Principled BSDF'].inputs['Normal'])

def begin(sid,category,evidence,description,confidence='medium',assumptions=None,relations=None):
 global current
 current={'id':sid,'category':category,'description':description,'component_names':[],'evidence_sample_ids':evidence,'provenance':{'visible_form':'observed in supplied RGB','placement':'measured from M2 depth with robust cross-view interpretation','hidden_geometry':'inferred'},'confidence':confidence,'assumptions':assumptions or ['Unseen backs, thickness and internal construction inferred.','Material response and physical coefficients are visual approximations.'],'spatial_relations':relations or []};records.append(current)
def tag(obj,name,mat):
 obj.name=current['id']+'__'+name;obj['semantic_id']=current['id'];obj['category']=current['category'];obj['provenance']='RGB observed form; depth measured position; hidden construction inferred'
 if mat:obj.data.materials.append(mat)
 current['component_names'].append(obj.name);return obj
def cube(name,loc,size,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);tag(o,name,mat)
 if bevel:m=o.modifiers.new('soft manufactured edges','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
def mesh(name,verts,faces,mat,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);tag(o,name,mat)
 if smooth:
  for p in me.polygons:p.use_smooth=True
 return o
def cylinder(name,loc,radius,depth,mat,scale=(1,1,1),vertices=48,bevel=0):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;o.scale=scale;tag(o,name,mat)
 if bevel:m=o.modifiers.new('rounded edge','BEVEL');m.width=bevel;m.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 for p in o.data.polygons:p.use_smooth=(len(p.vertices)==4)
 return o
def rod(name,a,b,r,mat,vertices=8):
 a=Vector(a);b=Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,mat,vertices=vertices);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def lathe(name,loc,profile,mat,n=64):
 verts=[];faces=[]
 for r,z in profile:
  for q in range(n):a=2*pi*q/n;verts.append((loc[0]+r*cos(a),loc[1]+r*sin(a),loc[2]+z))
 for j in range(len(profile)-1):
  for q in range(n):a=j*n+q;b=j*n+(q+1)%n;faces.append((a,b,b+n,a+n))
 return mesh(name,verts,faces,mat,True)
def arc_back(name,x,y,r,z0,z1,angle,span,mat):
 verts=[];faces=[];n=32
 for z in [z0,z1]:
  for rr in [r-.065,r+.065]:
   for k in range(n+1):a=angle-span/2+span*k/n;verts.append((x+rr*cos(a),y+rr*sin(a),z))
 N=n+1
 for k in range(n):
  faces.extend([(k,k+1,2*N+k+1,2*N+k),(N+k,3*N+k,3*N+k+1,N+k+1),(k,N+k,N+k+1,k+1),(2*N+k,2*N+k+1,3*N+k+1,3*N+k)])
 faces.extend([(0,2*N,3*N,N),(n,N+n,3*N+n,2*N+n)])
 o=mesh(name,verts,faces,mat,True);m=o.modifiers.new('upholstery seam rounding','BEVEL');m.width=.035;m.segments=3;return o

SEAT_LAYOUT=[('seat_far_01',-1.43,5.10,.35,None),('seat_far_02',-1.36,5.81,.34,pi*.76),('seat_far_03',-1.00,6.42,.34,pi*.62),('seat_far_04',-.30,6.45,.54,None),('seat_far_05',.27,6.06,.35,None),('seat_far_06',.95,6.08,.35,pi*.36),('seat_near_01',1.03,2.65,.40,None),('seat_near_02',1.04,1.88,.38,pi*.12),('seat_near_03',1.07,1.10,.39,pi*.08),('seat_near_04',1.14,.30,.38,None),('seat_end_01',-.55,-.1,.37,None),('seat_end_02',.20,-.30,.37,pi*1.5)]
def cushion(name,x,y,r,sid):
 poly=[(x+r*cos(2*pi*k/64),y+r*sin(2*pi*k/64)) for k in range(64)]
 for other,xx,yy,rr,_ in SEAT_LAYOUT:
  if other==sid:continue
  dx=xx-x;dy=yy-y;d=math.hypot(dx,dy)
  if d>=r+rr or d<.001:continue
  nx=dx/d;ny=dy/d;limit=(d*d+r*r-rr*rr)/(2*d)-.004
  result=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   fa=(a[0]-x)*nx+(a[1]-y)*ny-limit;fb=(b[0]-x)*nx+(b[1]-y)*ny-limit
   if fa<=0:result.append(a)
   if (fa<=0)!=(fb<=0):t=fa/(fa-fb);result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
  poly=result
 N=len(poly);verts=[(xx,yy,z) for z in [.155,.47] for xx,yy in poly];faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(k,(k+1)%N,(k+1)%N+N,k+N) for k in range(N)]
 o=mesh(name,verts,faces,green)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 m=o.modifiers.new('soft upholstery edge','BEVEL');m.width=.023;m.segments=3;o.modifiers.new('weighted cushion normals','WEIGHTED_NORMAL');return o
def chair(sid,x,y,r=.44,angle=None,evidence=[0,45,135],sy=1):
 begin(sid,'lounge_chair' if angle is not None else 'ottoman',evidence,'Circular sage upholstered seat with recessed feet'+(' and curved backrest' if angle is not None else ''),relations=[{'relation':'supported_by','target':'floor_inset'}])
 cylinder('underframe',(x,y,.15),r*.82,.08,black,scale=(1,sy,1))
 cushion('padded_seat',x,y,r,sid)
 for a in [pi/4,3*pi/4,5*pi/4,7*pi/4]:rod('foot_'+str(round(a,2)),(x+r*.7*cos(a),y+r*.7*sin(a),.015),(x+r*.7*cos(a),y+r*.7*sin(a),.18),.024,chrome)
 if angle is not None:arc_back('curved_padded_back',x,y,r*.85,.445,.755,angle,pi*.68,green)
def table(sid,x,y,sx=1,sy=1,evidence=[0,45,135],bowl=False):
 begin(sid,'coffee_table',evidence,'Low oval black table with radial sculpted base',relations=[{'relation':'supported_by','target':'floor_inset'}]);cylinder('oval_top',(x,y,.40),.64,.035,black,scale=(sx,sy,1),bevel=.015)
 cylinder('base_core',(x,y,.2025),.19,.375,black,vertices=32)
 for k in range(24):
  a=2*pi*k/24;verts=[]
  for z,r in [(.015,.34),(.11,.27),(.34,.19),(.38,.24)]:
   for aa in [a-.028,a+.028]:verts.append((x+r*cos(aa),y+r*sin(aa),z))
  faces=[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,6),(1,7,5,3),(0,6,7,1)];mesh('radial_leg_%02d'%k,verts,faces,black)
 if bowl:
  begin(sid+'_bowl','decorative_bowl',evidence,'Small open bronze bowl on coffee table',confidence='medium',relations=[{'relation':'on','target':sid}]);lathe('bowl',(x,y,.423),[(.12,0),(.17,.04),(.18,.13),(.165,.13),(.15,.045),(.10,.023),(0,.023)],metal)
def leaves_mesh(name,leaves,mat):
 verts=[];faces=[]
 for a,b,width in leaves:
  a=Vector(a);b=Vector(b);d=b-a;side=d.cross(Vector((0,0,1)))
  if side.length<.001:side=Vector((1,0,0))
  side.normalize();mid=a+d*.56;idx=len(verts);verts.extend([a,mid+side*width,b,mid-side*width,mid+Vector((0,0,width*.25))]);faces.extend([(idx,idx+1,idx+4),(idx+1,idx+2,idx+4),(idx+2,idx+3,idx+4),(idx+3,idx,idx+4)])
 return mesh(name,verts,faces,mat,True)
def grass(sid,x,y,size=.7,evidence=[0,45,135],pot='bowl'):
 begin(sid,'potted_grass',evidence,'Rounded ceramic planter with dense arching grass',relations=[{'relation':'supported_by','target':'floor_stone'}])
 if pot=='bowl':lathe('ceramic_bowl',(x,y,0),[(0,-.005),(.25*size,-.005),(.52*size,.12*size),(.68*size,.40*size),(.70*size,.48*size),(.64*size,.48*size),(.58*size,.18*size)],ceramic);z=.42*size;r=.57*size
 else:lathe('ceramic_vase',(x,y,0),[(0,-.005),(.22*size,-.005),(.38*size,.18*size),(.43*size,.48*size),(.35*size,.68*size),(.30*size,.72*size),(.27*size,.72*size)],ceramic);z=.67*size;r=.3*size
 cylinder('soil',(x,y,z-.03),r,.05,soil)
 verts=[];faces=[]
 for k in range(620):
  a=random.random()*2*pi;rr=r*random.random()**.5;L=size*random.uniform(.38,.85);start=Vector((x+rr*cos(a),y+rr*sin(a),z));side=Vector((-sin(a),cos(a),0));idx=len(verts)
  for q in range(7):
   t=q/6;pos=start+Vector((L*.78*t*cos(a),L*.78*t*sin(a),L*(1.6*t-1.2*t*t)));w=.006*size*(1-t)+.0003
   verts.extend([pos-side*w,pos+side*w])
  for q in range(6):faces.append((idx+2*q,idx+2*q+1,idx+2*q+3,idx+2*q+2))
 mesh('arching_blades',verts,faces,leaflight,True)

def yellow_planter(sid,x,y,evidence=[0,45,82,90,125,135]):
 begin(sid,'flower_planter',evidence,'Rectangular gray concrete planter with fine yellow flowering stems',relations=[{'relation':'behind','target':'seating_group_far'},{'relation':'supported_by','target':'floor_inset'}]);cube('box_base',(x,y,.31),(1.72,.52,.62),cement,.035);cube('soil_surface',(x,y,.625),(1.61,.42,.015),soil)
 leaves=[];v=[];f=[]
 for k in range(90):
  bx=x+random.uniform(-.73,.73);by=y+random.uniform(-.16,.16);h=random.uniform(.35,.83);dx=random.uniform(-.38,.38);dy=random.uniform(-.26,.26)
  # crossed tapered stem ribbons avoid thousands of individual objects
  a=Vector((bx,by,.63));b=Vector((bx+dx,by+dy,.63+h));idx=len(v);v.extend([a+Vector((-.006,0,0)),a+Vector((.006,0,0)),b+Vector((.002,0,0)),b-Vector((.002,0,0))]);f.append((idx,idx+1,idx+2,idx+3))
  for q in range(10):
   t=random.uniform(.2,1);base=a+(b-a)*t;aa=random.random()*2*pi;end=base+Vector((.13*cos(aa),.13*sin(aa),.09));leaves.append((base,end,.0045));leaves.append((base+Vector((0,0,.03)),end+Vector((0,0,.045)),.004))
 mesh('fine_stems',v,f,wood);leaves_mesh('yellow_sprigs',leaves,yellow)
def tree(sid,x,y,evidence=[0,45,125,135]):
 begin(sid,'potted_tree',evidence,'Small round canopy topiary in ceramic vase',relations=[{'relation':'beside','target':'reception_desk'}]);lathe('pot',(x,y,0),[(0,.015),(.19,.015),(.25,.25),(.23,.52),(.18,.56),(.16,.56)],ceramic);cylinder('soil',(x,y,.52),.17,.03,soil);rod('trunk',(x,y,.5),(x,y,1.6),.035,wood)
 leaves=[]
 for k in range(3400):
  a=random.random()*2*pi;t=random.uniform(-1,1);rr=.52*random.random()**(1/3);pos=Vector((x+rr*math.sqrt(1-t*t)*cos(a),y+rr*math.sqrt(1-t*t)*sin(a),1.72+rr*t*.70));end=pos+Vector((random.uniform(-.08,.08),random.uniform(-.08,.08),random.uniform(-.04,.07)));leaves.append((pos,end,.047))
 leaves_mesh('dense_leaf_crown',leaves,leaf)
def birdplant(sid,x,y):
 begin(sid,'tall_flowering_plant',[60,90,100,143],'Bird of paradise foliage in tall square concrete planter');cube('square_planter',(x,y,.48),(.46,.46,.96),cement,.012);cube('soil',(x,y,.965),(.4,.4,.01),soil);leaves=[]
 for k in range(12):
  a=random.random()*2*pi;h=random.uniform(.55,1.25);base=(x,y,.97);tip=(x+.4*cos(a),y+.4*sin(a),.97+h);rod('stem_%02d'%k,base,tip,.008,leaf,6);leaves.append(((x+.1*cos(a),y+.1*sin(a),1.1),(x+.55*cos(a),y+.55*sin(a),1.3+h),.085))
 leaves_mesh('broad_blades',leaves,leaf)
 for k in range(3):
  a=k*2.1;tip=(x+.15*cos(a),y+.15*sin(a),2.1+k*.1);rod('flower_stalk_%d'%k,(x,y,1),tip,.008,leaf,6);leaves_mesh('orange_flower_%d'%k,[(tip,(tip[0]+.2,tip[1],tip[2]+.2),.055)],yellow)
def lamp(sid,x,y,evidence):
 begin(sid,'floor_lamp',evidence,'Tripod floor lamp with cylindrical white fabric shade');
 for k in range(3):a=k*2*pi/3;rod('leg_%d'%k,(x+.15*cos(a),y+.15*sin(a),.02),(x+.045*cos(a),y+.045*sin(a),1.45),.013,chrome)
 lathe('fabric_shade',(x,y,1.35),[(.21,0),(.22,.5),(.20,.5),(.19,0),(.21,0)],linen);cylinder('diffuser',(x,y,1.39),.19,.015,emit)

def light_bowl(sid,x,y,z,r,evidence):
 begin(sid,'pendant_light',evidence,'Suspended shallow woven bowl pendant with central warm diffuser',assumptions=['Woven relief uses explicit staggered cells; exact interlacing inferred.','Suspension height and hidden electrics inferred; emitted intensity chosen for rendering.']);prof=[]
 for k in range(18):t=k/17;rr=r*(.22+.78*t);zz=.24*r*(t*t);prof.append((rr,zz))
 lathe('woven_dish',(x,y,z),prof,woven)
 verts=[];faces=[]
 for ring in range(13):
  rr=r*(.27+.71*ring/12);count=max(20,int(2*pi*rr/.037))
  for k in range(count):
   aa=2*pi*(k+.5*(ring%2))/count;da=pi*.74/count;dr=.020*r;idx=len(verts)
   for rrr,aaa,up in [(rr-dr,aa-da,0),(rr+dr,aa-da,0),(rr+dr,aa+da,0),(rr-dr,aa+da,0),(rr,aa,-.023*r)]:
    zz=.24*r*((rrr/r-.22)/.78)**2+up;verts.append((x+rrr*cos(aaa),y+rrr*sin(aaa),z+zz))
   faces.extend([(idx,idx+1,idx+4),(idx+1,idx+2,idx+4),(idx+2,idx+3,idx+4),(idx+3,idx,idx+4)])
 mesh('woven_relief',verts,faces,woven)
 cylinder('warm_diffuser',(x,y,z+.002),r*.23,.025,emit)
 for a in [0,2*pi/3,4*pi/3]:rod('suspension_'+str(a),(x+r*.45*cos(a),y+r*.45*sin(a),z+.1),(x+r*.45*cos(a),y+r*.45*sin(a),4.94),.003,metal,6)
 # Small ribs imply detailed woven bowl outline at each radial direction.
 for k in range(40):a=2*pi*k/40;rod('rim_weave_%02d'%k,(x+r*.89*cos(a),y+r*.89*sin(a),z+.16*r),(x+r*cos(a),y+r*sin(a),z+.24*r),.008,woven,6)

# Architectural shell, explicitly built components with no scan geometry.
begin('floor_stone','floor',[0,45,60,90,110,135,179],'Continuous pale polished stone floor',confidence='high',assumptions=['Floor thickness 0.16 m inferred.','Ground plane robust fit uses good-baseline input depths; no scale adjustment.'])
cube('main_slab',(.0,6.7,-.085),(8.12,18.6,.16),stone)
cube('recessed_right_slab',(5.1,11.8,-.085),(2.2,8.4,.16),stone)
begin('floor_inset','floor_inlay',[0,45,60,90,110,135,179],'Long polished charcoal inset through seating and reception axis',confidence='high');cube('dark_inlay',(-.18,6.8,.006),(4.20,16.6,.018),floorblack)
begin('ceiling','ceiling',[0,45,82,90,125,135],'Plaster ceiling with dark parallel slats along both sides');cube('ceiling_main',(.0,6.7,5.04),(8.16,18.6,.16),ceilingmat);cube('ceiling_recess',(5.1,11.8,5.04),(2.2,8.4,.16),ceilingmat)
for x in [-3.2,2.8]:
 for k,y in enumerate([-.9+i*.19 for i in range(90)]):cube(('left' if x<0 else 'right')+'_slat_%03d'%k,(x,y,4.92),(1.65,.07,.12),charcoal)
# Wall panels with narrow dark joints; door bays are separate surfaces.
def paneled_wall(sid,axis,fixed,start,end,height=4.98,bays=None,backing_sign=1,evidence=[0,45,60,82,90,135]):
 begin(sid,'wall',evidence,'Pale vertical wall panels divided by dark recessed joints');bays=bays or []
 cuts=sorted(set([start,end]+[v for a,b in bays for v in (a,b)]+[start+i*.8 for i in range(1,int((end-start)/.8)+1)]))
 for a,b in zip(cuts[:-1],cuts[1:]):
  mid=(a+b)/2;door=any(d0<=mid<=d1 for d0,d1 in bays)
  for z0,z1 in [(0,1.98),(1.98,3.48),(3.48,height)]:
   if door and z0==0:continue
   loc=(fixed,mid,(z0+z1)/2) if axis=='x' else (mid,fixed,(z0+z1)/2);size=(.15,b-a-.022,z1-z0-.022) if axis=='x' else (b-a-.022,.15,z1-z0-.022);cube('panel_%03d'%len(current['component_names']),loc,size,wall,.006)
 # thin dark backing preserves joints only, doorway still open in lower band.
 for z0,z1 in [(2.0,height)]:
  loc=(fixed+backing_sign*.12 if axis=='x' else (start+end)/2,(start+end)/2 if axis=='x' else fixed+backing_sign*.12,(z0+z1)/2);size=(.07,end-start,z1-z0) if axis=='x' else (end-start,.07,z1-z0);cube('joint_backing',loc,size,charcoal)
paneled_wall('wall_mirror','x',3.58,-2.5,7.45,bays=[(-.9,.05),(5.8,6.68)])
paneled_wall('wall_right_recess','x',6.23,7.45,16.0,bays=[(9.5,10.35),(12.5,13.35)])
paneled_wall('wall_recess_return','y',7.48,3.58,6.23,evidence=[75,82])
paneled_wall('wall_reception','y',16.02,-4.05,6.23,evidence=[0,45,110,125,135,179])
paneled_wall('wall_near_end','y',-2.52,-4.05,3.58,backing_sign=-1,evidence=[82,90,100])
for k,(x,y,w) in enumerate([(3.61,-.42,.95),(3.61,6.24,.88),(6.26,9.92,.85),(6.26,12.92,.85)]):
 if k==0:
  begin('door_side_0','open_passage',[66,75,90],'Observed open passage at near end of mirror wall',confidence='high',assumptions=['Only 0.8 m visible doorway return is inferred. Unseen connected room extent unknown.','Jamb and header component colliders leave passage free.'])
  for yy in [y-w/2-.018,y+w/2+.018]:cube('return_jamb_'+str(yy),(x+.35,yy,.985),(.8,.036,1.97),wall)
  cube('jamb_top',(x+.35,y,2.02),(.8,w+.072,.05),metal)
  cube('passage_threshold',(x+.35,y,-.085),(.8,w,.16),stone)
 else:
  begin('door_side_%d'%k,'interior_door',[45,60,75,82,90],'Flush brushed-metal interior door',confidence='medium');cube('door_leaf',(x,y,.985),(.055,w-.04,1.97),chrome,.008);cube('jamb_top',(x-.03,y,2.02),(.10,w+.04,.05),metal)
# Large glazed facade x=-4.05, paneled lower and upper bands.
begin('glass_facade','window_wall',[0,45,90,100,110,125,135],'Bright full-height glazing with slender mullions and two pairs of brass framed entrance doors',confidence='high',assumptions=['Exterior overexposure represented by luminous panes.','Glass optical properties and mullion cross sections inferred.'])
for k in range(24):
 y=-2.5+(18.5/24)*(k+.5);cube('pane_%02d'%k,(-4.07,y,2.47),(.035,18.5/24-.036,4.94),glazing);cube('vertical_mullion_%02d'%k,(-4.0,y-18.5/48,2.48),(.055,.035,4.96),charcoal)
cube('horizontal_crossbar',(-3.98,6.75,2.77),(.08,18.55,.065),charcoal)
cube('lower_sill',(-4.00,6.75,.027),(.12,18.5,.055),chrome)
for k,y in enumerate([-.65,12.02]):
 begin('entrance_door_%d'%k,'glass_double_door',[0,90,100,110,125],'Pair of brass framed tall glass entrance leaves',confidence='high')
 for n,yy in enumerate([y-.42,y+.42]):
  for dy in [-.4,.4]:cube('leaf_%d_stile_%s'%(n,dy),(-3.92,yy+dy,1.37),(.08,.055,2.74),brass,.008)
  for z in [.07,2.68]:cube('leaf_%d_rail_%s'%(n,z),(-3.92,yy,z),(.08,.8,.13),brass,.005)
  rod('handle_%d'%n,(-3.83,yy+(.31 if n==0 else -.31),.85),(-3.83,yy+(.31 if n==0 else -.31),1.5),.015,brass)
begin('column_facade','structural_column',[0,45,90,100,110,125,135],'Round structural column beside glazing',confidence='high');cylinder('shaft',(-3.1,6.68,2.48),.42,4.96,stone,vertices=64)
# Circular mirror constellation on primary right wall; reflective material only.
begin('mirror_cluster','wall_mirror',[45,60,75,82,135,143,179],'Ten circular mirrors of unequal diameters arranged as a horizontal cluster',confidence='high',assumptions=['Mirrors are reflective surfaces; reflected content is not additional room geometry.','Backing thickness 0.025 m inferred.'])
for k,(y,z,r) in enumerate([(2.95,1.75,.62),(1.75,1.30,.51),(.78,1.98,.43),(1.65,2.53,.32),(2.15,2.16,.25),(3.75,2.2,.29),(4.0,1.7,.19),(3.82,1.2,.30),(2.52,.99,.18),(.9,1.24,.19)]):
 o=cylinder('mirror_%02d'%k,(3.476,y,z),r,.027,mirror,vertices=64);o.rotation_euler[1]=pi/2
# Far conversational seating: rounded modular group, each functional seat independent.
for args in SEAT_LAYOUT:
 chair(*args,evidence=[0,45,60,90,135,179] if 'far' in args[0] else [45,60,75,90,135,150])
table('table_far',-.52,5.27,.86,.70,bowl=True)
table('table_near',.12,2.45,1.02,.76,evidence=[45,60,90,135,150])
table('table_end',-.45,-.8,.75,.7,evidence=[90,100])
yellow_planter('planter_yellow_left',-1.3,7.73);yellow_planter('planter_yellow_right',.87,7.73)
grass('grass_window_mid',-3.1,5.40,1.0);grass('grass_wall_mid',2.86,4.90,.94,pot='vase',evidence=[45,60,75,82,135,179]);grass('grass_window_near',-3.16,-1.2,.88,evidence=[90,100]);grass('grass_reception_corner',4.55,14.7,.75,evidence=[0,45,135]);tree('tree_reception_left',-2.12,14.86);tree('tree_reception_right',1.84,14.86)
birdplant('plant_tall_left',-1.35,-1.20);birdplant('plant_tall_right',2.50,-.35)
lamp('lamp_reception',3.31,14.5,[0,45,135,179]);lamp('lamp_recess',5.52,8.56,[45,60,75,82]);lamp('lamp_near',2.75,-1.54,[90,100])
# Angular reception desk at far wall.
begin('reception_desk','reception_counter',[0,45,100,110,125,135,179],'Faceted angular dark reception desk with inset working surface',confidence='medium',assumptions=['Depth observations of desk vary by 1.5 m between views; placement uses the consistent far-loop views.','Hidden working side and support inferred.'])
x0=-1.8;x1=1.75;y0=13.55;y1=14.30
verts=[(x0,y0,.15),(x1,y0,.15),(x1+.12,y0,.84),(x0-.12,y0,.84),(x0,y1,.15),(x1,y1,.15),(x1,y1,.84),(x0,y1,.84),(-.35,y0-.16,.41)]
mesh('faceted_shell',verts,[(0,1,8),(1,2,8),(2,3,8),(3,0,8),(0,4,5,1),(3,7,4,0),(1,5,6,2),(2,6,7,3),(4,7,6,5)],black)
cube('counter_top',(-.025,13.91,.85),(3.78,.87,.05),black,.012)
begin('desk_small_plant','decorative_plant',[0,45,125,135],'Small plant on reception counter',confidence='low');cylinder('pot',(.8,13.9,.93),.065,.13,ceramic);leaves_mesh('leaves',[((.8,13.9,.99),(.8+random.uniform(-.09,.09),13.9+random.uniform(-.07,.07),1.2+random.uniform(0,.1)),.027) for _ in range(12)],leaf)
# Abstract wall emblem/horns observed above desk.
begin('wall_emblem','wall_art',[0,45,125,135,179],'Abstract shield and curved metal line emblem above reception');cube('shield_upper',(-.05,15.89,2.60),(.55,.055,.65),linen,.01);o=cylinder('shield_round',(-.05,15.88,2.30),.275,.055,linen,scale=(1,.7,1));o.rotation_euler[0]=pi/2
curve=bpy.data.curves.new('curved metal emblem','CURVE');curve.dimensions='3D';curve.bevel_depth=.016;curve.bevel_resolution=3;s=curve.splines.new('BEZIER');coords=[(-1.35,15.84,3.45),(-1.35,15.84,2.87),(-1.08,15.84,2.76),(-.05,15.84,2.76),(1.08,15.84,2.76),(1.30,15.84,2.87),(1.30,15.84,3.45)];s.bezier_points.add(len(coords)-1)
for p,co in zip(s.bezier_points,coords):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
o=bpy.data.objects.new('emblem',curve);scene.collection.objects.link(o);tag(o,'curved_horns',metal);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
# Pendants: independent irregular staggered rows inferred from several traversals.
pendants=[(-2.25,-.35,.72),(0.10,-.3,.84),(2.1,-.25,.71),(-2.1,3.0,.74),(.1,1.65,.87),(2.25,2.55,.84),(-2.0,4.4,.79),(.25,4.7,.76),(2.15,4.9,.80),(-2.2,7.0,.68),(-.3,7.3,.76),(1.55,7.6,.70),(-2.2,9.7,.74),(-.25,10.0,.76),(1.9,10.1,.67),(-2.1,12.0,.63),(-.2,12.65,.64),(1.85,12.55,.69),(-1.65,14.45,.55),(.30,14.55,.6),(2.25,14.35,.58)]
for k,(x,y,r) in enumerate(pendants):light_bowl('pendant_%02d'%k,x,y,4.22+(.11 if k%3==1 else .0),r,[0,45,82,90,125,135])
# Area light sources approximate luminous glazing and ceiling bounce.
def area(name,loc,target,energy,size,color=(1,.95,.82),shape='DISK',size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape=shape;d.size=size;d.color=color
 if size_y is not None:d.size_y=size_y
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
for y in [1,6,11,15]:area('daylight_window_%s'%y,(-3.82,y,3.2),(1,y,1.5),420,4.0,(.94,.98,1),'RECTANGLE',3.7)
for y in [1,6,11,15]:area('soft_ceiling_%s'%y,(0,y,4.82),(0,y,0),80,3,(1,.85,.64))
# All 180 native input poses, same rigid transform and no predicted camera substitutions.
frames=[]
for f in J['frames']:
 c=M@Matrix(f['camera_to_world']);frames.append({k:f[k] for k in ['sample_index','source_index','timestamp_ns']}|{'camera_to_world':[list(r) for r in c],'intrinsics':f['intrinsics'],'valid':True})
json.dump({'frames':frames,'coordinate_frame':'model','pose_convention':'OpenCV RDF camera-to-world','model_from_input':T['model_from_input'],'geometry_scale':1.0},open(O/'cameras.json','w'),indent=2)
camd=bpy.data.cameras.new('check_camera');cam=bpy.data.objects.new('check_camera',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.type='PERSP';camd.sensor_fit='HORIZONTAL';camd.sensor_width=36;camd.lens=762.8*36/1280;camd.clip_start=.025;camd.clip_end=100;camd.shift_x=0;camd.shift_y=0
# Compute exact component bounds and stable record mapping.
bpy.context.view_layer.update()
for rec in records:
 pts=[]
 for name in rec['component_names']:
  obj=bpy.data.objects.get(name)
  if obj is None:continue
  pts.extend([obj.matrix_world@Vector(c) for c in obj.bound_box])
 if pts:
  mn=[min(p[i] for p in pts) for i in range(3)];mx=[max(p[i] for p in pts) for i in range(3)];rec['bounds_model_m']={'min':mn,'max':mx};rec['dimensions_m']=[mx[i]-mn[i] for i in range(3)];rec['centroid_m']=[(mx[i]+mn[i])/2 for i in range(3)]
 rec['physical']={'static':True,'friction':.6,'restitution':.05,'coefficient_provenance':'assumed; not measured'}
json.dump({'objects':records,'coordinate_frame':'model','units':'metres'},open(O/'objects.json','w'),indent=2)
colliders=[]
for rec in records:
 if rec['category'] not in ['wall_art','decorative_plant','decorative_bowl','pendant_light','wall_mirror']:
  colliders.append({'object_id':rec['id'],'shape':'component_meshes' if rec['category'] in ['wall','floor','window_wall','open_passage'] else 'bounds_box','component_names':rec['component_names'],'bounds_model_m':rec.get('bounds_model_m'),'static':True,'simplification':'Conservative AABB for furniture/foliage; compound components for architectural apertures','friction':.6,'restitution':.05})
json.dump({'colliders':colliders,'units':'metres','physical_coefficients':'inferred'},open(O/'colliders.json','w'),indent=2)
json.dump({'method_id':'M2','version':VERSION,'coordinate_frame':'model','model_from_input':T['model_from_input'],'scale':1.,'room':{'window_x':-4.05,'main_right_wall_x':3.58,'recess_right_wall_x':6.23,'recess_start_y':7.48,'near_end_y':-2.52,'reception_end_y':16.02,'floor_z':0,'ceiling_z':4.96},'semantic_object_ids':[r['id'] for r in records],'object_groups':{'seating_group_far':['seat_far_%02d'%k for k in range(1,7)]+['table_far'],'seating_group_near':['seat_near_%02d'%k for k in range(1,5)]+['table_near']},'uncertainty':'Far depth and static windows inconsistent; reliable floor/common walls robustly interpreted without scale correction.'},open(O/'layout.json','w'),indent=2)
json.dump({'objects':[{k:v for k,v in r.items() if k not in ['component_names','bounds_model_m','physical']} for r in records],'all_contact_sheets_inspected':['000_029','030_059','060_089','090_119','120_149','150_179'],'full_rgb_inspected':[0,45,60,75,82,90,100,110,125,135,179]},open(O/'analysis/object_inventory.json','w'),indent=2)
manifest={'method_id':'M2','model_id':'gpt-6-astra','status':'building_initial_checks','quality_status':'limited','model_from_input':T['model_from_input'],'geometry_scale':1.0,'revisions':VERSION,'checking_render_count':5,'input_packet_sha256':hashlib.sha256((P/'packet.json').read_bytes()).hexdigest(),'unresolved_issues':['DA3 input depth in near-static windows has gross metric scale inconsistencies; no rescaling applied.','Native ViPE camera trajectory and predicted depths retain drift/conflicts.','Fine woven pendant pattern, plant species detail and floor reflection relief approximate.','Hidden backs, thickness, joints, materials, light strengths and physical coefficients inferred.'],'scope_declaration':'Only generic contract/tools, assigned M2 packet and own output read. No GT, held-out RGB, other methods or prior scenes.','constructed_from_empty_scene':True,'whole_scan_used_as_scene':False,'render_settings':{'engine':'CYCLES','device':'CPU','samples':12,'resolution':[640,480],'threads':4}}
json.dump(manifest,open(O/'modelling_manifest.json','w'),indent=2)
cam.matrix_world=Matrix(frames[0]['camera_to_world'])@Matrix.Diagonal((1,-1,-1,1))
bpy.ops.wm.save_as_mainfile(filepath=str(O/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'scene.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_apply=True)
# Fixed five projections; count each actual attempt before rendering.
log=json.load(open(O/'iteration_log.json'));log['versions'].append({'version':VERSION,'purpose':'Repair nine independent review issues; preserve cameras and metric units','object_count':len(records),'render_attempts':[]})
for i in [0,45,90,135,179]:
 attempt={'version':VERSION,'sample_index':i,'path':f'checks/v{VERSION}_{i:04d}.png','status':'attempted'};log['versions'][-1]['render_attempts'].append(attempt);log['checking_render_count']+=1;manifest['checking_render_count']=log['checking_render_count'];json.dump(log,open(O/'iteration_log.json','w'),indent=2);json.dump(manifest,open(O/'modelling_manifest.json','w'),indent=2)
 cam.matrix_world=Matrix(frames[i]['camera_to_world'])@Matrix.Diagonal((1,-1,-1,1));scene.render.filepath=str(O/attempt['path']);t=time.monotonic();bpy.ops.render.render(write_still=True);attempt['elapsed_seconds']=time.monotonic()-t;attempt['status']='completed';json.dump(log,open(O/'iteration_log.json','w'),indent=2)
manifest['status']='ready_for_final_review';json.dump(manifest,open(O/'modelling_manifest.json','w'),indent=2)
print('M2 ready_for_independent_review',len(records),'semantic records',log['checking_render_count'],'checking renders')
