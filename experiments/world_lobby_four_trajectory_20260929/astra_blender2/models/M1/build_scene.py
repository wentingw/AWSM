"""Fresh RGB-only semantic lobby. Rebuild: blender -b --factory-startup --threads 2 --python build_scene.py -- --output-dir DIR. No renders."""
import bpy, bmesh, math, random, json, argparse, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output-dir',default=str(ROOT));a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);OUT=Path(a.output_dir);OUT.mkdir(parents=True,exist_ok=True)
L=json.loads((ROOT/'layout.json').read_text());random.seed(8033)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.unit_settings.system='METRIC';sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.use_file_extension=True;sc.render.image_settings.file_format='PNG';bpy.context.preferences.filepaths.save_version=0
sc.world=bpy.data.worlds.new('Daylight');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.84,.9,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.18
sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.5;sc.render.resolution_x=640;sc.render.resolution_y=480;sc.render.resolution_percentage=100
M={}
def mat(n,col,rough=.5,metal=0,noise=0,emission=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 if emission:bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=emission
 if noise:
  nt=m.node_tree;noise_node=nt.nodes.new('ShaderNodeTexNoise');noise_node.inputs['Scale'].default_value=95;noise_node.inputs['Detail'].default_value=2;b=nt.nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=noise;b.inputs['Distance'].default_value=.018;nt.links.new(noise_node.outputs['Fac'],b.inputs['Height']);nt.links.new(b.outputs['Normal'],bs.inputs['Normal'])
 M[n]=m;return m
mat('limestone',(.56,.54,.48),.23,noise=.12);mat('wall_oak',(.48,.455,.38),.5,noise=.16);mat('wall_gray',(.37,.375,.355),.6,noise=.1);mat('ceiling',(.68,.65,.57),.8,noise=.1);mat('dark_gap',(.022,.025,.023),.65);mat('black_polished',(.027,.03,.028),.09,.35);mat('inlay',(.16,.14,.08),.18,.65);mat('metal_dark',(.08,.085,.078),.28,.8);mat('brass',(.5,.39,.20),.26,.8);mat('mirror',(.87,.9,.88),.025,1);mat('sage',(.32,.405,.24),.85,noise=.5);mat('concrete',(.35,.37,.355),.78,noise=.3);mat('ceramic',(.57,.63,.64),.26,noise=.25);mat('soil',(.04,.025,.015),1);mat('leaf_green',(.105,.18,.042),.75);mat('leaf_light',(.24,.32,.08),.85);mat('gold_leaf',(.47,.36,.04),.65);mat('stem',(.16,.11,.035),.8);mat('shade',(.70,.70,.61),.72);mat('shade_weave',(.5,.43,.30),.65);mat('warm_glow',(1,.68,.3),.5,emission=3);mat('daylight',(1,1,1),.5,emission=2);mat('flower_orange',(.92,.20,.008),.6)
# Appearance adjustments are inferred from fixed source RGB, not measured BRDFs.
for name,color in {'wall_oak':(.30,.275,.225),'wall_gray':(.25,.255,.245),'ceiling':(.43,.415,.37),'shade_weave':(.17,.135,.085),'shade':(.50,.47,.39),'metal_dark':(.035,.038,.034),'brass':(.30,.225,.085)}.items():
 M[name].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
mat('slat_wood',(.065,.052,.035),.62,noise=.15)
# Anisotropic grain in the existing wall shader; generated in object coordinates.
nt=M['wall_oak'].node_tree;noise_node=next(n for n in nt.nodes if n.type=='TEX_NOISE');tex=nt.nodes.new('ShaderNodeTexCoord');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(2,2,.045);nt.links.new(tex.outputs['Generated'],scale.inputs[0]);nt.links.new(scale.outputs[0],noise_node.inputs['Vector'])
records=[];current=None
def begin(id,cat,evidence,relations=None,provenance='observed class/count/layout; dimensions and hidden geometry inferred from RGB'):
 global current
 current={'id':id,'category':cat,'component_names':[],'evidence_frames':evidence,'relations':relations or {},'provenance':provenance};records.append(current)
def register(o,n,ma):
 o.name=current['id']+'__'+n;o['semantic_id']=current['id'];o['category']=current['category'];o.data.materials.append(M[ma]);current['component_names'].append(o.name);return o
def box(n,loc,dim,ma,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);register(o,n,ma)
 if bevel:b=o.modifiers.new('soft_edges','BEVEL');b.width=bevel;b.segments=2;o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 return o
def mesh(n,vs,fs,ma):
 d=bpy.data.meshes.new(n);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);register(o,n,ma);return o
def cyl(n,loc,rad,depth,ma,vertices=32):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=rad,depth=depth,location=loc);o=register(bpy.context.object,n,ma)
 for f in o.data.polygons:f.use_smooth=True
 return o
def ell(n,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.scale=scale;register(o,n,ma);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 return o
def bar(n,p,q,r,ma):
 d=Vector(q)-Vector(p);o=cyl(n,(Vector(p)+Vector(q))/2,r,d.length,ma,12);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def lathe(n,center,profile,ma,seg=48):
 vs=[];fs=[]
 for r,z in profile:
  for j in range(seg):t=j*2*math.pi/seg;vs.append((center[0]+r*math.cos(t),center[1]+r*math.sin(t),center[2]+z))
 for i in range(len(profile)-1):
  for j in range(seg):k=i*seg+j;l=i*seg+(j+1)%seg;fs.append((k,l,l+seg,k+seg))
 o=mesh(n,vs,fs,ma)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=True
 return o
# Shell and glazing
begin('floor','architectural_floor',[33,91,100,155]);box('slab',(4,8,-.1),(8,16,.2),'limestone')
begin('black_floor_insert','floor_finish',[33,91,100,129,155]);box('surface',(3.5,8,.008),(5.1,14,.016),'black_polished')
vs=[];fs=[]
for x in range(43):
 for y in range(118):
  xx=1.03+x*.116;yy=1.08+y*.117;s=.012*(.75+.5*random.Random(x*1000+y).random());k=len(vs);vs.extend([(xx-s,yy-s,.018),(xx+s,yy-s,.018),(xx+s,yy+s,.018),(xx-s,yy+s,.018)]);fs.append((k,k+1,k+2,k+3))
mesh('subtle_inlay_grid',vs,fs,'inlay')
begin('ceiling','architectural_ceiling',[33,82,100,129]);box('slab',(4,8,4.7),(8,16,.2),'ceiling')
for side,y in [('north',16.08),('south',-.08)]:
 begin(side+'_wall','architectural_wall',[33,91,129,155]);box('backing',(4,y,2.3),(8,.16,4.6),'dark_gap')
 for x in range(8):
  for row,(z,h) in enumerate([(1.3,2.58),(3.6,1.96)]):box(f'panel_{x}_{row}',(x+.5,y+(-.09 if side=='north' else .09),z),(.983,.025,h),'wall_oak')
begin('east_recess_wall','architectural_wall',[74,82,91]);box('backing',(8.08,8,2.3),(.16,16,4.6),'dark_gap')
for y in range(16):
 for row,(z,h) in enumerate([(1.3,2.58),(3.6,1.96)]):box(f'panel_{y}_{row}',(7.986,y+.5,z),(.025,.982,h),'wall_gray')
# projecting mirror wall with genuine door openings
begin('mirror_partition','architectural_partition',[61,74,82]);box('upper',(6.87,7.25,3.6),(.14,7.5,2),'dark_gap')
for j in range(6):box('upper_panel_'+str(j),(6.785,3.5+(j+.5)*1.25,3.6),(.025,1.23,1.98),'wall_oak')
box('lower_core',(6.87,6.9,1.3),(.14,5.1,2.6),'dark_gap')
for j in range(4):box('lower_panel_'+str(j),(6.785,4.36+(j+.5)*1.27,1.3),(.025,1.25,2.58),'wall_oak')
box('north_end',(7.4,11,2.3),(1.2,.13,4.6),'wall_oak');box('south_end',(7.4,3.5,3.6),(1.2,.13,2),'wall_oak')
for id,y,w in [('north_metal_door',10.075,1.25),('south_opening',3.925,.85)]:
 begin(id,'door' if 'metal' in id else 'doorway',[61,74,82]);
 if 'metal' in id:box('leaf',(6.88,y,1.3),(.07,w-.035,2.59),'mirror')
 else:box('dark_recess',(7.96,y,1.3),(.02,w,2.6),'dark_gap')
begin('glazed_facade','window_wall',[33,91,100,108,118,129]);box('bright_glass',(-.055,8,2.3),(.04,16,4.6),'daylight')
for j in range(17):box('mullion_'+str(j),(.0,j,2.3),(.055,.034,4.6),'metal_dark')
box('transom',(.025,8,2.62),(.065,16,.045),'metal_dark')
for tag,y0 in [('south',2.2),('north',12.0)]:
 begin(tag+'_glazed_double_door','entrance_door',[33,100,108,118,129]);
 for j in range(3):box('stile_'+str(j),(.055,y0+j*.9,1.3),(.095,.075,2.6),'brass')
 for j in range(2):
  for z in [.075,2.55]:box(f'rail_{j}_{z}',(.055,y0+.45+j*.9,z),(.095,.88,.10),'brass')
  bar('handle_'+str(j),(.14,y0+.84+j*.12,.7),(.14,y0+.84+j*.12,1.55),.013,'metal_dark')
begin('central_round_column','structural_column',[33,100,108,118,129]);cyl('shaft',(.62,8,2.3),.35,4.6,'limestone',64)
begin('ceiling_slats','ceiling_detail',[33,82,100,129]);
for y in range(82):
 for j,x in enumerate([.7,6.85]):box(f'slat_{y}_{j}',(x,.12+y*.195,4.48),(1.4,.065,.16),'slat_wood')
# Furniture, fabric seats, segmented curved backs
for group in L['seating_groups']:
 gx,gy=group['center'];sign=group['facing_y'];gid=group['id'];e=[33,129,155] if gid=='north' else [61,82,91]
 offsets=L['seat_offsets']
 for j,(dx,dy) in enumerate(offsets):
  x=gx+dx;y=gy+dy*(-sign)
  begin(f'{gid}_seat_{j+1}','modular_lounge_seat',e,{'supported_by':'floor','member_of':gid+'_seating_group'});lathe('upholstered_seat',(x,y,0),[(.39,.12),(.46,.17),(.47,.47),(.42,.53),(.0,.54)],'sage')
  for lx in [-.25,.25]:
   for ly in [-.25,.25]:cyl(f'leg_{lx}_{ly}',(x+lx,y+ly,.075),.017,.15,'metal_dark',12)
  if j in [1,2,4]:
   theta=math.atan2(dy*(-sign),dx);v=[];f=[]
   for z,r in [(.48,.44),(.88,.43),(.9,.35),(.50,.36)]:
    for k in range(17):t=theta-.95+k*1.9/16;v.append((x+r*math.cos(t),y+r*math.sin(t),z))
   for layer in range(4):
    for k in range(16):f.append((layer*17+k,layer*17+k+1,((layer+1)%4)*17+k+1,((layer+1)%4)*17+k))
   f.extend([(51,34,17,0),(16,33,50,67)]);o=mesh('curved_back',v,f,'sage');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 begin(gid+'_coffee_table','coffee_table',e,{'supported_by':'floor'});ty=gy-.6*(-sign);cyl('tabletop',(gx,ty,.43),.68,.048,'metal_dark',64);cyl('base_core',(gx,ty,.22),.3,.4,'metal_dark')
 for k in range(24):
  t=k*2*math.pi/24;ob=box('radial_base_'+str(k),(gx+.34*math.cos(t),ty+.34*math.sin(t),.22),(.07,.15,.36),'metal_dark',.02);ob.rotation_euler.z=t
 begin(gid+'_table_bowl','decorative_bowl',e,{'supported_by':gid+'_coffee_table'});lathe('bowl',(gx,ty,.46),[(.13,0),(.18,.08),(.175,.13),(.155,.13),(.1,.035)],'brass')
# extra seats visible along mirror near foreground
for j,(x,y) in enumerate(L['side_seats_xy']):
 begin('south_side_seat_'+str(j),'modular_lounge_seat',[33,61,74,82,155],{'supported_by':'black_floor_insert','member_of':'mirror_side_seating'},'physical seats observed in61/74; coordinates reconciled by conditional ray-plane inference; hidden legs inferred');lathe('seat',(x,y,0),[(.36,.10),(.45,.17),(.45,.48),(.38,.54),(0,.54)],'sage')
 for lx in [-.24,.24]:
  for ly in [-.24,.24]:cyl(f'leg_{lx}_{ly}',(x+lx,y+ly,.065),.017,.13,'metal_dark',12)
 # Backrest on two observed seats. Closed annular section; no bevel that could collapse end faces.
 if j>0:
  v=[];f=[]
  for z,r in [(.48,.43),(.83,.42),(.85,.35),(.50,.36)]:
   for k in range(17):t=-.85+k*1.7/16;v.append((x+r*math.cos(t),y+r*math.sin(t),z))
  for layer in range(4):
   for k in range(16):f.append((layer*17+k,layer*17+k+1,((layer+1)%4)*17+k+1,((layer+1)%4)*17+k))
  f.extend([(51,34,17,0),(16,33,50,67)]);o=mesh('curved_back',v,f,'sage');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
x,y=L['side_table_xy'];begin('mirror_side_coffee_table','coffee_table',[33,61,155],{'supported_by':'black_floor_insert','member_of':'mirror_side_seating'},'third table observed beside mirror seats; position inferred compromise across incompatible estimated cameras');cyl('tabletop',(x,y,.43),.60,.048,'metal_dark',64);cyl('support',(x,y,.225),.25,.42,'metal_dark')
# Reception angular faceted desk
begin('reception_desk','reception_counter',[33,108,118,129,155],{'supported_by':'floor','support_component':'reception_desk__inferred_plinth'});cx,cy=4.1,15.15
v=[(cx-1.5,cy-.4,.1),(cx+1.45,cy-.4,.1),(cx+1.7,cy-.35,.87),(cx+1.5,cy+.4,1.08),(cx-1.6,cy+.4,1.08),(cx-1.7,cy-.35,.87),(cx,cy-.54,.63)]
f=[(0,1,6),(1,2,6),(2,3,4,5,6),(5,0,6),(0,5,4),(1,3,2),(0,4,3,1)];mesh('faceted_body',v,f,'metal_dark');box('worktop',(cx,cy+.05,1.02),(3,.65,.08),'metal_dark')
box('inferred_plinth',(cx,cy,.055),(2.8,.55,.11),'metal_dark')
begin('reception_wall_emblem','wall_art',[33,129,155]);box('shield_upper',(4.1,15.91,2.05),(.5,.045,.53),'ceramic');ell('shield_round',(4.1,15.90,1.82),(.25,.022,.24),'ceramic');bar('line_left',(3.1,15.925,2.22),(3.1,15.925,2.9),.012,'metal_dark');bar('line_right',(5.1,15.925,2.22),(5.1,15.925,2.9),.012,'metal_dark');bar('line_horizontal',(3.1,15.925,2.22),(5.1,15.925,2.22),.012,'metal_dark')
# Mirror disks: geometry exists once, reflected furniture deliberately not duplicated.
mirrors=[(7.65,2.15,.77),(6.22,1.55,.62),(8.95,2.75,.33),(9.02,2.05,.23),(8.80,1.42,.38),(6.8,1.03,.22),(6.52,3.17,.38),(5.60,2.64,.52),(5.52,1.71,.24),(7.25,2.8,.30)]
for j,(y,z,r) in enumerate(mirrors):
 begin('mirror_disk_'+str(j+1),'wall_mirror',[61,74,82,91],{'attached_to':'mirror_partition'});o=cyl('disc',(6.745,y,z),r,.026,'mirror',64);o.rotation_euler.y=math.pi/2
# Plant leaf batches reduce scene overhead while preserving semantic plant components.
def leaf_mesh(n,leaves,ma):
 v=[];f=[]
 for c,d,w in leaves:
  c=Vector(c);d=Vector(d);side=d.cross(Vector((0,0,1)))
  if side.length<.0001:side=Vector((1,0,0))
  side.normalize();k=len(v);v.extend([tuple(c),tuple(c+d*.45+side*w),tuple(c+d),tuple(c+d*.45-side*w)]);f.append((k,k+1,k+2,k+3))
 mesh(n,v,f,ma)
def foliage(center,radius,height,style):
 x,y,z=center;ls=[]
 for j in range(350 if style=='shrub' else 230):
  theta=random.random()*2*math.pi;rr=radius*math.sqrt(random.random());zz=random.random()*height
  c=(x+rr*math.cos(theta),y+rr*math.sin(theta),z+zz)
  if style=='grass':d=(math.cos(theta)*.35,math.sin(theta)*.35,.12+random.random()*.35);w=.018
  else:d=(math.cos(theta)*.12,math.sin(theta)*.12,.06);w=.045
  ls.append((c,d,w))
 leaf_mesh('foliage',ls,'leaf_green')
# Golden divider pair: opposite camera directions observe the same two containers.
for row,yy in enumerate(L['planter_dividers_y']):
 for j,xx in enumerate([2.2,4.65]):
  id=f'gold_planter_{row}_{j}';begin(id,'planter',[33,82,91,100,129,155],{'supported_by':'floor'});box('container',(xx,yy,.37),(1.95,.58,.66),'concrete',.03);box('soil',(xx,yy,.702),(1.80,.45,.025),'soil');box('foot',(xx,yy,.045),(1.8,.48,.085),'metal_dark')
  begin(id+'_plant','flowering_shrub',[33,82,91,100,129,155],{'planted_in':id},'observed yellow branching silhouette; deterministic inferred stems and leaves');leaves=[];vs=[];fs=[]
  for k in range(32):
   bx=xx+random.uniform(-.85,.85);by=yy+random.uniform(-.2,.2);height=random.uniform(.5,1.0);dx=random.uniform(-.45,.45);dy=random.uniform(-.35,.35)
   # flat narrow crossed stem strips provide geometry without hundreds of objects
   for branch in range(3):
    ex=bx+dx+random.uniform(-.2,.2);ey=by+dy+random.uniform(-.2,.2);top=.7+height*random.uniform(.7,1.1);q=len(vs);vs.extend([(bx-.008,by,.70),(bx+.008,by,.70),(ex+.005,ey,top),(ex-.005,ey,top)]);fs.append((q,q+1,q+2,q+3))
    for step in range(10):
     t=.25+step*.075;z=.7+(top-.7)*t;c=(bx+(ex-bx)*t,by+(ey-by)*t,z);ang=random.random()*6.28;leaves.append((c,(math.cos(ang)*.09,math.sin(ang)*.09,.04),.022))
  mesh('branches',vs,fs,'stem');leaf_mesh('yellow_foliage',leaves,'gold_leaf')
# Broad low pots near facade and corners
for j,(x,y) in enumerate([(.85,7.25),(.85,1.0),(7.0,14.9)]):
 begin('low_bowl_planter_'+str(j),'planter',[33,91,108,118,129]);lathe('bowl',(x,y,0),[(.30,.02),(.49,.13),(.62,.42),(.6,.47),(.55,.42),(.3,.09)],'ceramic');cyl('soil',(x,y,.39),.53,.03,'soil');begin('low_bowl_plant_'+str(j),'ornamental_grass',[33,91,108,118,129],{'planted_in':'low_bowl_planter_'+str(j)});foliage((x,y,.42),.46,.27,'grass')
for j,(x,y,tree) in enumerate([(6.18,9.4,False),(2.05,15.1,True),(6.0,15.1,True)]):
 begin('ceramic_vase_'+str(j),'planter',[33,61,74,129,155]);lathe('vase',(x,y,0),[(.20,0),(.32,.13),(.36,.40),(.29,.64),(.25,.67),(.22,.62)],'ceramic');cyl('soil',(x,y,.61),.24,.025,'soil');begin('vase_plant_'+str(j),'topiary' if tree else 'shrub',[33,61,74,129,155],{'planted_in':'ceramic_vase_'+str(j)})
 if tree:bar('trunk',(x,y,.62),(x,y,1.52),.032,'stem');foliage((x,y,1.4),.38,.55,'shrub')
 else:foliage((x,y,.65),.35,.35,'grass')
for j,(x,y) in enumerate([(6.0,2.0),(2.1,.95)]):
 begin('tall_square_planter_'+str(j),'planter',[61,82,91]);box('container',(x,y,.42),(.58,.58,.84),'concrete',.025);begin('bird_of_paradise_'+str(j),'flowering_plant',[61,82,91],{'planted_in':'tall_square_planter_'+str(j)});ls=[]
 for k in range(13):
  ang=k*2.4;h=random.uniform(.6,1.15);bar('stem_'+str(k),(x,y,.84),(x+.18*math.cos(ang),y+.18*math.sin(ang),.84+h*.6),.009,'leaf_green');ls.append(((x+.18*math.cos(ang),y+.18*math.sin(ang),.84+h*.55),(.3*math.cos(ang),.3*math.sin(ang),h*.6),.08))
 leaf_mesh('broad_leaves',ls,'leaf_green');leaf_mesh('orange_flowers',[((x,y,1.92),(.2,.02,.10),.045),((x+.08,y,2.02),(-.08,.03,.18),.035)],'flower_orange')
# Floor lamps at observed corners/recess
for j,(x,y) in enumerate([(7.0,12.8),(7.45,9.4),(6.8,.75)]):
 begin('floor_lamp_'+str(j),'floor_lamp',[33,61,74,82,91,155]);cyl('base',(x,y,.025),.19,.045,'metal_dark');cyl('post',(x,y,.82),.016,1.6,'brass');lathe('shade',(x,y,1.38),[(.26,0),(.25,.44),(.23,.44),(.24,0)],'shade');cyl('diffuser',(x,y,1.39),.235,.01,'warm_glow')
# Suspended bowl lights. Profile and woven texture are inferred from repeated observed fixtures.
for j,(x,y,r,z) in enumerate([(1.6,1.8,.68,3.9),(3.8,1.4,.7,3.93),(6,2.0,.78,3.82),(2,4,.65,3.9),(4.8,3.8,.8,3.9),(6,5.4,.6,3.84),(1.6,6.5,.78,4),(3.8,6.2,.65,3.78),(5.8,7.6,.77,3.92),(2.3,8.8,.6,3.88),(4.1,9.1,.78,3.95),(6.0,10,.63,3.8),(1.7,11.3,.65,3.96),(3.5,11.6,.58,3.81),(5.5,12.1,.7,3.98),(2.1,13.5,.53,3.92),(4.3,13.8,.6,3.83),(6.4,14.1,.6,3.95)]):
 begin('pendant_'+str(j+1),'pendant_light',[33,82,100,108,129,155],{'suspended_from':'ceiling'},'observed bowl fixture type and approximate distribution; exact count, coordinates and weave inferred');bar('suspension',(x,y,z),(x,y,4.56),.004,'metal_dark');lathe('bowl',(x,y,z),[(.19*r,-.23*r),(.32*r,-.23*r),(.50*r,-.18*r),(.75*r,-.1*r),(r,.04*r),(r,.07*r)],'shade_weave',64);cyl('diffuser',(x,y,z-.23*r),.20*r,.008,'warm_glow',32)
 # concentric rows of small raised quadrilaterals
 vs=[];fs=[]
 for rr in range(3,18):
  rad=r*rr/18;zz=z-.25*r+.30*r*(rad/r)**1.8
  for k in range(rr*7):
   t=2*math.pi*(k+.5*(rr%2))/(rr*7);dt=.35/(rr*7)*math.pi;dr=.015;k0=len(vs)
   for rad2,t2 in [(rad-dr,t-dt),(rad+dr,t-dt),(rad+dr,t+dt),(rad-dr,t+dt)]:vs.append((x+rad2*math.cos(t2),y+rad2*math.sin(t2),zz-.008))
   fs.append((k0,k0+1,k0+2,k0+3))
 mesh('woven_cells',vs,fs,'shade')
# Illumination, intentionally inferred; objects are nonmesh and not semantic occluders.
for y in [2,6,10,14]:
 d=bpy.data.lights.new('facade_light_'+str(y),'AREA');d.energy=260;d.shape='RECTANGLE';d.size=3.5;d.size_y=4;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=(.12,y,3);o.rotation_euler=(0,math.pi/2,0)
for y in [3,8,13]:
 d=bpy.data.lights.new('ceiling_fill_'+str(y),'AREA');d.energy=65;d.size=4;o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=(4,y,4.35)
# Semantic bounds and collision simplifications are computed from actual components.
bpy.context.view_layer.update()
colliders=[]
for rec in records:
 coords=[]
 for name in rec['component_names']:
  o=bpy.data.objects[name];coords.extend([o.matrix_world@Vector(c) for c in o.bound_box])
 lo=[min(c[k] for c in coords) for k in range(3)];hi=[max(c[k] for c in coords) for k in range(3)];rec['dimensions']=[hi[k]-lo[k] for k in range(3)];rec['bbox_min']=lo;rec['bbox_max']=hi
 enabled=rec['category'] not in ['flowering_shrub','shrub','ornamental_grass','topiary','flowering_plant','pendant_light','ceiling_detail']
 if rec['id'] in ['mirror_partition','south_opening']:
  parts=[]
  for name in rec['component_names']:
   o=bpy.data.objects[name];pts=[o.matrix_world@Vector(c) for c in o.bound_box];parts.append({'component_name':name,'type':'AABB','bounds_min':[min(c[k] for c in pts) for k in range(3)],'bounds_max':[max(c[k] for c in pts) for k in range(3)]})
  colliders.append({'id':rec['id'],'object_id':rec['id'],'type':'COMPOUND','parts':parts,'provenance':'component boxes preserve open south doorway; finite rear recess wall inferred','enabled':True})
 else:
  colliders.append({'id':rec['id'],'object_id':rec['id'],'type':'AABB','bounds_min':lo,'bounds_max':hi,'provenance':'inferred simple physics approximation of this logical object','enabled':enabled})
(OUT/'objects.json').write_text(json.dumps({'objects':records},indent=2)+'\n');(OUT/'colliders.json').write_text(json.dumps({'colliders':colliders,'portals':[{'id':'south_opening','clear_bounds_min':[6.70,3.55,.02],'clear_bounds_max':[7.85,4.30,2.55],'width_m':.75,'height_m':2.53,'state':'enterable_finite_recess','onward_connectivity':'unobserved; inferred back wall atx7.95; not a validated through-route'},{'id':'north_metal_door','state':'closed','collider_id':'north_metal_door'}]},indent=2)+'\n')
(OUT/'analysis').mkdir(exist_ok=True);(OUT/'analysis/object_inventory.json').write_text(json.dumps({'inventory':records,'scope':'all six RGB contact sheets covering180; ten original fixed images','reflection_handling':'Only ten physical mirror disks; furniture reflections are not additional inventory.'},indent=2)+'\n')
if OUT!=ROOT:(OUT/'layout.json').write_text(json.dumps(L,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'scene.glb'),export_format='GLB',export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
print('BUILD_COMPLETE',len(records),'semantic objects',len([o for o in bpy.data.objects if o.type=='MESH']),'mesh components')
