"""M3 fresh semantic model v3 repaired candidate. Rebuilds from empty scene, own layout only.
Native scale=1; no image textures, imported meshes, saved scenes or fused depth geometry.
"""
import os
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import bpy,bmesh,math,json,random
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;L=json.loads((R/'layout.json').read_text());random.seed(329)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('daylight_world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.85,.93,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
scene.view_settings.view_transform='AgX'
materials={}
def mat(name,col,rough=.5,metal=0,noise=0,scale=50,stretch=None,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
  coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=stretch or (1,1,1);l.new(coord.outputs['Generated'],mapping.inputs[0]);l.new(mapping.outputs[0],tex.inputs['Vector'])
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[c*(1-noise) for c in col],1);ramp.color_ramp.elements[1].color=(*[min(1,c*(1+noise)) for c in col],1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.025;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 if name in ['limestone','inset_black_polished'] and noise: bump.inputs['Strength'].default_value=0
 materials[name]=m;return m
mat('limestone',(.47,.455,.40),.23,noise=.3,scale=160)
mat('inset_black_polished',(.026,.028,.023),.11,.4,noise=.12,scale=110)
mat('oak_vertical',(.30,.28,.235),.44,noise=.3,scale=7,stretch=(14,14,.25))
mat('wall_grey',(.33,.335,.31),.62,noise=.2,scale=80)
mat('ceiling_plaster',(.62,.59,.52),.7,noise=.12,scale=30)
mat('dark_batten',(.105,.085,.064),.42)
mat('metal_dark',(.065,.07,.065),.22,.85)
mat('bronze',(.38,.28,.105),.22,.82)
mat('aluminium',(.60,.61,.57),.25,.9)
mat('mirror',(.92,.96,.91),.025,1)
mat('sage_fabric',(.31,.37,.21),.84,noise=.2,scale=150)
mat('table_charcoal',(.055,.052,.045),.28)
mat('concrete',(.16,.17,.16),.72,noise=.4,scale=95)
mat('ceramic',(.50,.56,.55),.23,noise=.4,scale=13)
mat('soil',(.035,.023,.013),1)
mat('leaf',(.095,.20,.045),.62)
mat('leaf_light',(.18,.29,.09),.6)
mat('gold_leaf',(.48,.36,.035),.72)
mat('twig',(.20,.125,.036),.9)
mat('orange_flower',(.8,.22,.015),.45)
mat('shade_woven',(.54,.39,.22),.6)
mat('shade_glow',(.95,.73,.43),.5,emission=3)
mat('white_linen',(.82,.81,.74),.7)
mat('glazing_bright',(.98,.99,1),.14,emission=2)
objects=[];active=None

def semantic(id,category,frames,source='Observed silhouette/category; dimensions and placement from measured layout; concealed topology, materials and detail inferred',relations=None):
 global active
 active=dict(id=id,category=category,components=[],evidence_frames=frames,provenance=source,relations=relations or {'supported_by':'floor'},_objs=[]);objects.append(active)
def register(o,part,material):
 o.name=active['id']+'__'+part;o['semantic_id']=active['id'];o['provenance']='semantic authored mesh'
 if material:o.data.materials.append(materials[material])
 active['components'].append(o.name);active['_objs'].append(o);return o
def cube(part,loc,size,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('rounded_edges','BEVEL');mod.width=bevel;mod.segments=3
 return register(o,part,material)
def cyl(part,loc,r,depth,material,vertices=40):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object
 for p in o.data.polygons:p.use_smooth=(len(p.vertices)==4)
 return register(o,part,material)
def uvball(part,loc,size,material,segments=20,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.scale=size
 for p in o.data.polygons:p.use_smooth=True
 return register(o,part,material)
def mesh(part,verts,faces,material):
 m=bpy.data.meshes.new(active['id']+'_'+part);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(m.name,m);scene.collection.objects.link(o);return register(o,part,material)
def rods(part,lines,radius,material,sides=6):
 vs=[];fs=[]
 for a,b in lines:
  a=Vector(a);b=Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<.01:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u);start=len(vs)
  for p in [a,b]:
   for j in range(sides):vs.append(tuple(p+radius*(math.cos(j*2*math.pi/sides)*u+math.sin(j*2*math.pi/sides)*v)))
  fs.append(tuple(start+j for j in reversed(range(sides))));fs.append(tuple(start+sides+j for j in range(sides)))
  for j in range(sides):fs.append((start+j,start+(j+1)%sides,start+(j+1)%sides+sides,start+j+sides))
 return mesh(part,vs,fs,material)
def torus(part,loc,major,minor,material):
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=6,location=loc,major_radius=major,minor_radius=minor);return register(bpy.context.object,part,material)
def lathe(part,loc,profile,material,n=48):
 vs=[];fs=[]
 for r,z in profile:
  for j in range(n):a=2*math.pi*j/n;vs.append((loc[0]+r*math.cos(a),loc[1]+r*math.sin(a),loc[2]+z))
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 o=mesh(part,vs,fs,material)
 for p in o.data.polygons:p.use_smooth=True
 return o
# Shell, with semantic panels and deliberately limited concealed thickness.
room=L['room'];xmin,xmax,ymin,ymax=-2.2,18.25,-6.4,3.85
semantic('floor','floor',[33,82,91,108,129]);cube('slab',((xmin+xmax)/2,(ymin+ymax)/2,-.1),(xmax-xmin,ymax-ymin,.2),'limestone')
semantic('floor_inset','floor_finish',[33,91,108,129]);cube('polished_rectangle',(7.225,-.275,.009),(17.75,4.65,.018),'inset_black_polished')
semantic('ceiling','ceiling',[33,82,108],relations={'above':'room'});cube('plaster',((xmin+xmax)/2,(ymin+ymax)/2,5.34),(xmax-xmin,ymax-ymin,.18),'ceiling_plaster')
# Wall panel function excludes low door rectangles.
def wall_x(id,x,y0,y1,grey=False):
 semantic(id,'wall',[33,82,91,129]);cube('substrate',(x,(y0+y1)/2,2.625),(.15,y1-y0,5.25),'dark_batten')
 count=round((y1-y0)/.85)
 for j in range(count):
  ya=y0+(y1-y0)*j/count;yb=y0+(y1-y0)*(j+1)/count
  for k,(z0,z1) in enumerate([(0,1.72),(1.75,3.5),(3.53,5.25)]):cube(f'panel_{j}_{k}',(x-(.082 if x>0 else -.082),(ya+yb)/2,(z0+z1)/2),(.045,yb-ya-.018,z1-z0),'wall_grey' if grey else 'oak_vertical')
wall_x('reception_wall',18.25,-6.4,3.85)
wall_x('near_end_wall',-2.2,-6.4,3.85)
def wall_y(id,y,x0,x1,doors=[],grey=False):
 semantic(id,'wall',[33,61,74,82,91]);cuts=sorted(set([x0,x1]+[v for d in doors for v in d]));
 for j,(a,b) in enumerate(zip(cuts[:-1],cuts[1:])):
  door=any(a>=d[0] and b<=d[1] for d in doors);z0=2.25 if door else 0
  cube(f'core{j}',((a+b)/2,y, (z0+5.25)/2),(b-a,.15,5.25-z0),'dark_batten')
  count=max(1,round((b-a)/.8))
  for k in range(count):
   for h,(lo,hi) in enumerate([(z0,max(z0,2.25)),(2.28,3.75),(3.78,5.25)]):
    if hi<=lo:continue
    cube(f'panel{j}_{k}_{h}',(a+(k+.5)*(b-a)/count,y+.09,(lo+hi)/2),((b-a)/count-.016,.045,hi-lo),'wall_grey' if grey else 'oak_vertical')
wall_y('recess_wall',-6.4,-2.2,18.25,[(9.15,10.15),(13.45,14.45)],True)
wall_y('mirror_partition',-4.2,-.6,8,[(6.45,7.45),(-.6,.45)])
semantic('partition_end','wall',[74,82]);cube('return',(8,-5.3,2.625),(.14,2.2,5.25),'oak_vertical')
for j,(x,y) in enumerate([(6.95,-4.15),(9.65,-6.35),(13.95,-6.35)]):
 semantic('metal_door_'+str(j),'door',[33,61,74,82]);cube('leaf',(x,y,1.12),(.94,.06,2.24),'aluminium');cube('handle',(x-.34,y+.055,1.0),(.025,.07,.36),'metal_dark')
# Transparent exterior is deliberately represented by bright opaque panes for geometric first-hit checks.
semantic('glazed_facade','window_wall',[33,91,100,108,118,129],source='Measured DA3 plane y3.85; frames and pane segmentation from RGB. Opaque bright glass proxy: exterior not observed. Thickness inferred.')
door_ranges=[(c-.865,c+.865) for c in L['door_centres']]
facade_cuts=sorted([xmin,xmax]+[v for pair in door_ranges for v in pair])
for j,(a,b) in enumerate(zip(facade_cuts[:-1],facade_cuts[1:])):
 z0=2.74 if any(a>=lo and b<=hi for lo,hi in door_ranges) else 0
 cube('bright_glass_'+str(j),((a+b)/2,3.92,(z0+5.25)/2),(b-a,.045,5.25-z0),'glazing_bright')
for j in range(27):
 xx=xmin+j*(xmax-xmin)/26
 if not any(lo<xx<hi for lo,hi in door_ranges):cube('mullion_'+str(j),(xx,3.85,2.625),(.035,.08,5.25),'metal_dark')
cube('transom',((xmin+xmax)/2,3.80,2.8),(xmax-xmin,.1,.065),'metal_dark')
for j,xc in enumerate(L['door_centres']):
 semantic('entry_double_door_'+str(j),'door',[33,100,108,118]);
 for k,dx in enumerate([-.43,.43]):
  cube(f'leaf{k}_glass',(xc+dx,3.79,1.37),(.73,.035,2.52),'glazing_bright')
  for side in [-1,1]:cube(f'leaf{k}_upright{side}',(xc+dx+side*.4,3.73,1.37),(.14,.10,2.74),'bronze')
  for z in [.07,2.67]:cube(f'leaf{k}_rail{z}',(xc+dx,3.73,z),(.83,.10,.22),'bronze')
  cube(f'leaf{k}_handle',(xc+dx+(.32 if k==0 else -.32),3.63,1.25),(.025,.045,.85),'bronze')
semantic('window_column','column',[33,91,108,118,129],source='Cylinder visually observed; radius and position inferred from ray-plane estimates. Silhouette triangulation was rejected.')
cyl('shaft',L['column']['location'],L['column']['radius'],5.25,'limestone',64)
# Ceiling battens, separated slats produce real reflections on inset.
for side,ya,yb in [('window',2.4,3.85),('inner',-6.4,-3.7)]:
 semantic('ceiling_battens_'+side,'ceiling_detail',[33,82,108],relations={'attached_to':'ceiling'})
 for j in range(100):cube('slat_'+str(j),(xmin+(j+.5)*(xmax-xmin)/100,(ya+yb)/2,5.19),(.055,yb-ya,.13),'dark_batten')
# Modular circular seating with separately modelled wrap-around upholstered back.
def chair(id,x,y,angle,back=True):
 semantic(id,'armchair' if back else 'ottoman',[33,61,91,129,155],source='Seat footprint from RGB ray-plane anchors; visible curved back and four feet. Diameter .88–1.0 m and upholstery thickness inferred within DA3 spread.')
 cyl('seat',(x,y,.36),.455,.43,'sage_fabric',48)
 torus('seat_piping',(x,y,.565),.442,.008,'sage_fabric')
 for j in range(4):
  a=math.pi/4+j*math.pi/2;cyl('foot'+str(j),(x+.32*math.cos(a),y+.32*math.sin(a),.08),.022,.16,'aluminium',10)
 if back:
  vs=[];fs=[];n=28;theta=math.radians(angle)
  for z in [.51,.90]:
   for r in [.355,.47]:
    for j in range(n+1):a=theta+math.radians(-78+156*j/n);vs.append((x+r*math.cos(a),y+r*math.sin(a),z))
  for j in range(n):
   for a,b in [(0,n+1),(2*(n+1),3*(n+1)),(0,2*(n+1)),(n+1,3*(n+1))]:fs.append((a+j,a+j+1,b+j+1,b+j))
  for j in [0,n]:fs.append((j,j+n+1,j+3*(n+1),j+2*(n+1)))
  o=mesh('curved_back',vs,fs,'sage_fabric');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  for p in o.data.polygons:p.use_smooth=(abs(p.normal.z)<.5 and len(p.vertices)==4)

def table(id,x,y,z,bowl=False):
 semantic(id,'coffee_table',[33,61,91,129,155]);o=cyl('oval_top',(x,y,z),.60,.045,'table_charcoal',64);o.scale=(1.05,.83,1)
 cyl('base_disc',(x,y,.04),.33,.055,'metal_dark')
 for j in range(24):
  a=j*2*math.pi/24;v=[]
  for zz,rr in [(.07,.32),(.20,.22),(z-.03,.30)]:
   for da in [-.028,.028]:v.append((x+rr*math.cos(a+da),y+rr*math.sin(a+da),zz))
  mesh('radial_fin'+str(j),v,[(0,1,3,2),(2,3,5,4)],'metal_dark')
 if bowl:
  semantic(id+'_bowl','decorative_bowl',[33,129,155],relations={'supported_by':id});lathe('bowl',(x,y,z+.023),[(.06,0),(.13,.02),(.17,.11),(.165,.14),(.145,.14),(.12,.055),(.05,.025)],'bronze')
for group in L['seating']:
 for j,(x,y,a) in enumerate(group['chairs']):chair(group['id']+'_chair'+str(j),x,y,a)
 for j,(x,y) in enumerate(group['ottomans']):chair(group['id']+'_ottoman'+str(j),x,y,0,False)
 table(group['id']+'_table',*group['table'],group['id']=='lounge_a')
# Leaves are batched explicit meshes; deterministic inferred botanical detail.
def leaves(part,centres,material,sz=.035):
 vs=[];fs=[]
 for c in centres:
  c=Vector(c);u=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.2,1))).normalized()*sz;v=u.cross(Vector((0,0,1))).normalized()*sz*.40;n=len(vs)
  vs.extend([tuple(c-u),tuple(c+v),tuple(c+u),tuple(c-v)]);fs.append((n,n+1,n+2,n+3))
 return mesh(part,vs,fs,material)
def bush(x,y,z,rx,ry,height,gold=False):
 branches=[];centres=[]
 for j in range(65 if gold else 100):
  a=random.uniform(0,math.tau);rad=random.uniform(.3,1);end=np.array([x+rx*math.cos(a)*rad,y+ry*math.sin(a)*rad,z+height*random.uniform(.55,1)]);start=np.array([x+random.uniform(-.1,.1),y+random.uniform(-.1,.1),z]);mid=start*.4+end*.6;branches.append((start,end))
  for k in range(4):
   base=start+(end-start)*(.3+k*.16);tip=base+np.array([random.uniform(-.2,.2),random.uniform(-.2,.2),random.uniform(.10,.23)]);branches.append((base,tip))
   for t in np.linspace(0,1,7):centres.append(base+(tip-base)*t+np.random.default_rng(j*33+k).uniform(-.018,.018,3))
  for t in np.linspace(.25,1,10):centres.append(start+(end-start)*t)
 rods('branches',branches,.004 if gold else .003,'twig',4);leaves('foliage',centres,'gold_leaf' if gold else 'leaf',.032 if gold else .047)
for d in L['dividers']:
 semantic(d['id'],'planter',[33,82,91,108,129],source='Triangulated visible front corners and ray-plane baseline. Concrete shell thickness and shrub topology inferred.');x,y,z=d['location'];dx,dy,dz=d['dimensions']
 cube('body',(x,y,z),(dx,dy,dz),'concrete',.025);cube('soil',(x,y,dz+.005),(dx-.08,dy-.08,.025),'soil')
 for yy in np.linspace(y-dy*.35,y+dy*.35,4):bush(x,yy,dz,.25,dy*.19,.83,True)
def pot(id,x,y,r=.35,h=.58,topiary=False):
 semantic(id,'potted_plant',[33,61,91,108,118,129],source='Visible plant category and approximate RGB ray-plane placement; pot profile, foliage and branches inferred.')
 lathe('ceramic_pot',(x,y,0),[(r*.65,0),(r*.90,.08),(r,h*.48),(r*.8,h),(r*.7,h),(r*.73,h-.09)],'ceramic');cyl('soil',(x,y,h-.025),r*.7,.02,'soil')
 if topiary:
  rods('trunks',[((x+.05*j,y,h),(x+.08*j,y,h+.9)) for j in [-1,0,1]],.018,'twig');bush(x,y,h+.65,r*1.4,r*1.4,.55)
 else:bush(x,y,h-.02,r*1.35,r*1.35,.56)
for args in [('window_grass_middle',6.35,3.0,.55,.40,False),('window_grass_near',-.85,3.0,.53,.42,False),('wall_grass',5.75,-3.6,.34,.62,False),('reception_tree_left',16.7,2,.32,.7,True),('reception_tree_right',16.7,-2.5,.32,.7,True),('reception_grass',17,-4.6,.47,.35,False)]:pot(*args)
for j,(x,y) in enumerate([(.5,-2.55),(-1.45,.4)]):
 semantic('tall_plant_'+str(j),'potted_plant',[61,82,91]);cube('square_planter',(x,y,.45),(.55,.55,.9),'concrete',.02);cube('soil',(x,y,.905),(.46,.46,.02),'soil');lines=[];vs=[];fs=[]
 for k in range(13):
  a=k*2.4;tip=Vector((x+.4*math.cos(a),y+.4*math.sin(a),1.25+random.random()*.8));base=Vector((x,y,.9));lines.append((base,tip));u=Vector((math.cos(a),math.sin(a),.7)).normalized();v=Vector((-math.sin(a),math.cos(a),0))*.085;n=len(vs);vs.extend([tuple(tip-u*.3),tuple(tip+v),tuple(tip+u*.32),tuple(tip-v)]);fs.append((n,n+1,n+2,n+3))
 rods('stems',lines,.013,'leaf');mesh('long_leaves',vs,fs,'leaf_light')
 for k in range(2):uvball('orange_flower'+str(k),(x+.1*k,y,2.02+k*.15),(.09,.035,.035),'orange_flower')
# Angular reception desk.
semantic('reception_desk','reception_counter',[33,108,118,129,155],source='Desk endpoints triangulated 0.3–0.9 px. Top and side facets observed, hidden back and thickness inferred.')
x,y,z=L['desk']['location'];top=L['desk']['top_z'];vs=[(x-.5,y-1.6,.18),(x-.5,y+1.6,.18),(x+.45,y+1.4,.15),(x+.45,y-1.4,.15),(x-.55,y-1.6,top),(x-.55,y+1.6,top),(x+.4,y+1.5,top),(x+.4,y-1.5,top),(x-.7,y-.1,.50)]
o=mesh('faceted_shell',vs,[(0,1,8),(1,5,8),(5,4,8),(4,0,8),(0,4,7,3),(1,2,6,5),(4,5,6,7),(0,3,2,1),(3,7,6,2)],'table_charcoal')
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
cube('concealed_plinth',(x,y,.109),(.76,2.50,.182),'table_charcoal')
semantic('desk_vase','decor',[33,129],relations={'supported_by':'reception_desk'});cyl('vase',(15.4,-.5,top+.09),.05,.18,'ceramic');rods('stems',[((15.4,-.5,top+.15),(15.41,-.5,top+.35))],.009,'leaf')
# Ten non-duplicated circular mirrors, radius from source pixel diameter / ray-plane scale.
anchors=json.loads((R/'analysis/anchors.json').read_text());mir=[a for a in anchors if a['label'].startswith('mirror')]
for j,(a,r) in enumerate(zip(mir,[.69,.61,.31,.21,.33,.21,.23,.47,.36,.29])):
 x,y,z=a['point_model'];semantic('wall_mirror_'+str(j),'mirror',[61,74,82],source='Centre ray-plane measured from original sample61 against y=-4.2; radius inferred from pixel extent; reflection not a duplicate object.',relations={'attached_to':'mirror_partition'})
 o=cyl('reflective_disc',(x,-4.075,z),r,.025,'mirror',64);o.rotation_euler[0]=math.pi/2
 o=torus('thin_rim',(x,-4.05,z),r,.012,'aluminium');o.rotation_euler[0]=math.pi/2
semantic('wall_crest','wall_art',[33,129,155],source='Top and bottom triangulated; shield outline visually inferred.',relations={'attached_to':'reception_wall'})
mesh('shield',[(18.10,-.08,2.64),(18.10,-.72,2.64),(18.10,-.72,1.8),(18.10,-.57,1.48),(18.10,-.4,1.38),(18.10,-.2,1.48),(18.10,-.08,1.8)],[(6,5,4,3,2,1,0)],'white_linen')
lines=[]
for side in [-1,1]:
 yy=-.4+side*1.1;pts=[(18.08,yy,3.55),(18.08,yy,2.9),(18.08,yy-side*.08,2.75),(18.08,yy-side*.25,2.68),(18.08,-.4,2.68)];lines.extend(zip(pts[:-1],pts[1:]))
rods('curved_emblem_lines',lines,.022,'metal_dark',8)
# Floor lamps.
for j,(x,y) in enumerate([(15.8,-4.3),(9,-5.7),(-1.55,-2.8)]):
 semantic('floor_lamp_'+str(j),'floor_lamp',[33,74,82,91]);cyl('base',(x,y,.025),.20,.05,'aluminium');cyl('stem',(x,y,.86),.019,1.7,'bronze');cyl('shade',(x,y,1.83),.25,.44,'white_linen');cyl('diffuser',(x,y,1.606),.23,.012,'shade_glow')
# Woven pendants: a shallow profiled bowl with separated crossing weave strands.
pendants=L['pendants']
for j,(x,y,z,r) in enumerate(pendants):
 semantic('pendant_'+str(j),'pendant_light',[33,82,108,129],source='Visible woven bowl type. Four centres triangulated; remaining staggered layout inferred from rays and occlusion. Weave, support thickness and power inferred.',relations={'suspended_from':'ceiling'})
 rods('cable',[((x,y,z+.20),(x,y,5.23))],.0035,'metal_dark',4)
 lathe('shade_body',(x,y,z),[(.20*r,0),(.35*r,.005),(.55*r,.045),(.78*r,.115),(r,.22),(r,.24),(.78*r,.135),(.55*r,.065),(.35*r,.025),(.20*r,.02)],'shade_woven',64)
 # Dense visible checker weaving added as crossing ribs; material body remains below strands.
 lines=[]
 for k in range(64):
  a=k*math.tau/64
  for t in range(10):
   rr1=r*(.21+.079*t);rr2=r*(.21+.079*(t+1));zz1=z+.23*(rr1/r)**2-.006;zz2=z+.23*(rr2/r)**2-.006
   aa=a+(.011 if t%2 else -.011);lines.append(((x+rr1*math.cos(aa),y+rr1*math.sin(aa),zz1),(x+rr2*math.cos(aa),y+rr2*math.sin(aa),zz2)))
 for k in range(10):
  rr=r*(.24+.078*k);zz=z+.23*(rr/r)**2-.018
  for t in range(64):a=t*math.tau/64;b=(t+1)*math.tau/64;lines.append(((x+rr*math.cos(a),y+rr*math.sin(a),zz),(x+rr*math.cos(b),y+rr*math.sin(b),zz)))
 rods('woven_strands',lines,.009,'white_linen',4);torus('rim',(x,y,z+.23),r,.012,'metal_dark');cyl('warm_diffuser',(x,y,z+.015),r*.21,.022,'shade_glow')
 light=bpy.data.lights.new('pendant_area_'+str(j),'AREA');light.energy=30;light.color=(1,.77,.48);light.shape='DISK';light.size=r*.5;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=(x,y,z-.025)
# broad inferred daylight sources; no mesh helpers.
for j,x in enumerate([1,6,11,16]):
 light=bpy.data.lights.new('daylight_'+str(j),'AREA');light.energy=650;light.shape='RECTANGLE';light.size=4;light.size_y=4;o=bpy.data.objects.new(light.name,light);scene.collection.objects.link(o);o.location=(x,3.65,3.2);o.rotation_euler=(Vector((x,-2,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Cameras are exact transformed native inputs. Store all; helper creates its own camera.
for f in json.loads((R/'cameras.json').read_text())['frames']:
 data=bpy.data.cameras.new('native_'+str(f['sample_index']).zfill(4));o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);data.lens=762.8*36/1280;data.sensor_width=36;data.clip_start=.01;data.clip_end=60
 from mathutils import Matrix
 o.matrix_world=Matrix((np.array(f['camera_to_world'])@np.diag([1,-1,-1,1])).tolist());o['sample_index']=f['sample_index']
 if f['sample_index']==33:scene.camera=o
# Semantic bounds and compound logical-object colliders; open portals remain open.
bpy.context.view_layer.update();out=[];coll=[]
for item in objects:
 pts=[];parts=[]
 for o in item.pop('_objs'):
  bb=np.array([list(o.matrix_world@Vector(c)) for c in o.bound_box]);pts.extend(bb.tolist())
  name=o.name;part=name.split('__')[1]
  # Botanical detail is visible geometry but not a solid collider.
  if any(w in part for w in ['foliage','branches','long_leaves','stems','trunks','orange_flower','soil','woven_strands','cable']):continue
  lo=bb.min(0);hi=bb.max(0)
  if np.any(hi-lo<.001):continue
  shape=dict(shape='aabb',component_names=[name],bounds=[lo.tolist(),hi.tolist()])
  if part in ['seat','shaft','ceramic_pot','base_disc']:
   shape=dict(shape='cylinder_z',component_names=[name],centre_xy=((lo[:2]+hi[:2])/2).tolist(),radius=float(max(hi[:2]-lo[:2])/2),z_range=[float(lo[2]),float(hi[2])])
  parts.append(shape)
 q=np.array(pts);mn=q.min(0);mx=q.max(0);item['component_names']=item['components'].copy();item['dimensions']=(mx-mn).tolist();item['bounds_model_m']=[mn.tolist(),mx.tolist()];item['position']=((mx+mn)/2).tolist();out.append(item)
 collider=dict(id=item['id'],semantic_id=item['id'],shape='compound',parts=parts,static=True,provenance='Inferred per-component solid proxies; foliage excluded; navigation dynamics unvalidated.')
 if item['category']=='door':
  collider.update(state='closed',opening_semantics='Separate leaf components; disable/transform leaf parts on opening. No continuous parent wall behind entry aperture.',traversable_in_current_state=False)
 if item['id']=='mirror_partition':collider['open_portals']=[dict(x_range=[-.6,.45],z_range=[0,2.25],y=-4.2,state='open',width_m=1.05)]
 coll.append(collider)
(R/'objects.json').write_text(json.dumps(dict(objects=out),indent=2)+'\n');(R/'colliders.json').write_text(json.dumps(dict(coordinate_frame='model',units='m',colliders=coll,limitations='Static inferred compound proxies. Doors closed; opening simulation not supplied. Open partition passage has no parent enclosing collider.'),indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(R/'scene.glb'),export_format='GLB',use_selection=False,export_cameras=False,export_lights=False,export_apply=True,export_extras=True)
print('BUILD_COMPLETE',len(objects),len([o for o in scene.objects if o.type=='MESH']))
