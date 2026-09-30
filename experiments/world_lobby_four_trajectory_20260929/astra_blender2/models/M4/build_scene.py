"""M4 independent semantic authoring. Reconstructs from layout.json, empty scene.
No historical geometry or saved scene read. Material/hidden construction inferred.
"""
import bpy,bmesh,math,json,random,os
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
R=Path(__file__).resolve().parent;L=json.load(open(R/'layout.json'));random.seed(40930)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)
S=bpy.context.scene;S.render.threads_mode='FIXED';S.render.threads=2
S.unit_settings.system='METRIC';S.unit_settings.scale_length=1
M={}; records=[]; current=None; C=L['repair_construction']
bpy.context.preferences.filepaths.save_version=0

def mat(name,color,metal=0,rough=.5,noise=None,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 if noise:
  nodes=m.node_tree.nodes;links=m.node_tree.links;t=nodes.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=noise[0];t.inputs['Detail'].default_value=3;b=nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=noise[1];b.inputs['Distance'].default_value=.025;links.new(t.outputs['Fac'],b.inputs['Height']);links.new(b.outputs['Normal'],p.inputs['Normal'])
 M[name]=m;return m
mat('limestone',(0.48,.47,.42),rough=.23,noise=(85,.13));mat('ivory_oak',(.49,.46,.38),rough=.45,noise=(7,.2));mat('panel_shadow',(.065,.06,.047),rough=.6);mat('black_polished_stone',(.028,.027,.023),rough=.14,noise=(20,.04));mat('ceiling_plaster',(.69,.67,.59),rough=.82,noise=(6,.1));mat('dark_slats',(.12,.105,.08),rough=.45);mat('bronze',(.32,.24,.11),metal=.8,rough=.22);mat('aluminium',(.5,.52,.49),metal=.85,rough=.25);mat('mirror',(.94,.97,.94),metal=1,rough=.025);mat('sage_fabric',(.38,.46,.27),rough=.83,noise=(145,.24));mat('table_dark',(.055,.051,.043),metal=.1,rough=.33);mat('concrete_pot',(.30,.31,.29),rough=.75,noise=(70,.4));mat('ceramic',(.47,.53,.52),metal=.12,rough=.3,noise=(18,.23));mat('soil',(.035,.031,.018),rough=1);mat('leaf_dark',(.075,.15,.028),rough=.68);mat('leaf_light',(.18,.27,.058),rough=.68);mat('leaf_yellow',(.37,.32,.055),rough=.63);mat('branch',(.19,.14,.053),rough=.8);mat('orange_flower',(.85,.26,.025),rough=.5);mat('lamp_woven',(.48,.37,.20),metal=.35,rough=.37);mat('lamp_glow',(1,.72,.35),rough=.4,emission=3);mat('window_white',(1,1,1),rough=.5,emission=1.5);mat('desk_grey',(.19,.19,.18),metal=.25,rough=.28);mat('marble_crest',(.72,.73,.70),rough=.3,noise=(4,.35))
# Directional oak grain via anisotropically scaled noise coordinates.
m=M['ivory_oak'];n=m.node_tree.nodes;l=m.node_tree.links;tex=next(t for t in n if t.type=='TEX_NOISE');tc=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(20,20,.22);l.new(tc.outputs['Generated'],v.inputs[0]);l.new(v.outputs[0],tex.inputs['Vector'])

# Inferred visual texture from source61/74. No image assets or external texture reads.
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.20,.18,.14,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.59,.55,.44,1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
# Persistent small rectangular metallic inlays; shader only, geometric depth unchanged.
m=M['black_polished_stone'];n=m.node_tree.nodes;l=m.node_tree.links;pbr=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],sep.inputs[0]);outs=[]
for axis,fill in [('X',.47),('Y',.36)]:
 mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=1/C['floor_grid_pitch'];l.new(sep.outputs[axis],mul.inputs[0]);fr=n.new('ShaderNodeMath');fr.operation='FRACT';l.new(mul.outputs[0],fr.inputs[0]);lt=n.new('ShaderNodeMath');lt.operation='LESS_THAN';lt.inputs[1].default_value=fill;l.new(fr.outputs[0],lt.inputs[0]);outs.append(lt.outputs[0])
mm=n.new('ShaderNodeMath');mm.operation='MULTIPLY';l.new(outs[0],mm.inputs[0]);l.new(outs[1],mm.inputs[1]);mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.012,.011,.009,1);mix.inputs[2].default_value=(.25,.17,.07,1);l.new(mm.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],pbr.inputs['Base Color']);pbr.inputs['Metallic'].default_value=.65;pbr.inputs['Roughness'].default_value=.22

def group(id,cat,evidence,provenance='observed semantic form; dimensions from measured layout; hidden construction and material inferred',relations=None):
 global current
 current=dict(id=id,category=cat,components=[],evidence_frames=evidence,provenance=provenance,relations=relations or ['supported_by:floor']);records.append(current)
def own(o,name,material):
 o.name=current['id']+'__'+name;o.data.name=o.name+'_mesh';o.data.materials.append(M[material]);o['semantic_id']=current['id'];o['provenance']=current['provenance'];current['components'].append(o.name);return o

def cube(name,loc,scale,material,bevel=0):
 vs=[(x*scale[0]/2,y*scale[1]/2,z*scale[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 o=mesh(name,vs,fs,material);o.location=loc
 if bevel:mod=o.modifiers.new('soft_edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,r,depth,material,vertices=48,rotation=None):
 vs=[(r*cos(2*pi*j/vertices),r*sin(2*pi*j/vertices),zz) for zz in [-depth/2,depth/2] for j in range(vertices)]
 fs=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]+[(j,(j+1)%vertices,(j+1)%vertices+vertices,j+vertices) for j in range(vertices)]
 o=mesh(name,vs,fs,material);o.location=loc
 if rotation:o.rotation_euler=rotation
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

def mesh(name,verts,faces,material):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(name,d);S.collection.objects.link(o);return own(o,name,material)

def line(name,a,b,r,material,vertices=8):
 a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,material,vertices);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def lathe(name,center,profile,material,N=48):
 vs=[(center[0]+r*cos(2*pi*j/N),center[1]+r*sin(2*pi*j/N),center[2]+z) for r,z in profile for j in range(N)];fs=[]
 for k in range(len(profile)-1):
  for j in range(N):a=k*N+j;b=k*N+(j+1)%N;fs.append((a,b,b+N,a+N))
 fs.extend([tuple(range(N-1,-1,-1)),tuple((len(profile)-1)*N+j for j in range(N))]);o=mesh(name,vs,fs,material)
 for f in o.data.polygons:f.use_smooth=True
 return o

def leaves_mesh(name,leaves,material):
 vs=[];fs=[]
 for a,b,width in leaves:
  a=Vector(a);b=Vector(b);d=b-a;side=d.cross(Vector((0,0,1)))
  if side.length<1e-6:side=Vector((1,0,0))
  side.normalize();mid=(a+b)*.5+Vector((0,0,.02));k=len(vs);vs.extend([a,mid+side*width,b,mid-side*width,mid+Vector((0,0,.025))]);fs.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)])
 return mesh(name,vs,fs,material)

def plant_detail(base,kind):
 x,y,z=base;leafsets=[[],[],[]]
 if kind=='tree':
  for k in range(3):line(f'trunk{k}',(x+.05*k,y,z+.55),(x+.07*(k-1),y+.035*k,z+1.55),.022,'branch')
  for k in range(420):
   a=random.uniform(0,2*pi);rr=random.random()**.5*.50;zz=random.uniform(1.25,1.9);aa=(x+rr*cos(a),y+rr*sin(a),z+zz);bb=(aa[0]+random.uniform(-.17,.17),aa[1]+random.uniform(-.17,.17),aa[2]+random.uniform(-.1,.1));leafsets[k%2].append((aa,bb,.035))
 elif kind=='vase':
  for k in range(650):
   a=random.uniform(0,2*pi);rr=.40*random.random()**.5;zz=.87+.30*math.sqrt(max(0,1-(rr/.42)**2));aa=(x+rr*cos(a),y+rr*sin(a),z+zz);bb=(aa[0]+random.uniform(-.08,.08),aa[1]+random.uniform(-.08,.08),aa[2]+random.uniform(-.06,.04));leafsets[k%2].append((aa,bb,.007))
 elif kind=='tall':
  for k in range(14):
   a=k*2.4;rr=random.uniform(.15,.5);top=(x+rr*cos(a),y+rr*sin(a),z+random.uniform(1.35,1.95));start=(x,y,z+.6);line('stem'+str(k),start,top,.012,'leaf_dark');aa=(x+.1*cos(a),y+.1*sin(a),z+1);leafsets[k%2].append((aa,top,.10))
  for k in range(3):
   top=(x+.14*k-.12,y,z+1.9+.12*k);line('flowerstem'+str(k),(x,y,z+.7),top,.012,'leaf_dark');leafsets[2].append((top,(top[0]+.18,top[1]+.025,top[2]+.12),.035))
 else:
  height=.9 if kind=='vase' else .62
  for k in range(380):
   a=random.uniform(0,2*pi);rr=random.uniform(.16,.62);aa=(x+random.uniform(-.12,.12),y+random.uniform(-.12,.12),z+height-.18);bb=(x+rr*cos(a),y+rr*sin(a),z+height+random.uniform(.0,.50));leafsets[k%2].append((aa,bb,.012 if kind=='bowl' else .02))
 for j,leaves in enumerate(leafsets):
  if leaves:leaves_mesh('foliage'+str(j),leaves,'orange_flower' if j==2 else ['leaf_dark','leaf_light'][j])

# Floor and ceiling.
r=L['room'];group('floor','architecture_floor',[33,61,91,100,108]);cube('slab',(17.75,21,-.12),(19.5,10,.24),'limestone')
group('dark_inlay','floor_finish',[33,91,100,108,155]);cube('polished_field',(16.95,21.8,.005),(17.5,4.4,.012),'black_polished_stone',.005)
group('ceiling','architecture_ceiling',[33,82,100,129]);cube('slab',(17.75,21,5.12),(19.5,10,.24),'ceiling_plaster')
# Walls regularized from independent numeric evidence. Panels create real joints.
def paneled_wall(id,axis,value,a,b,z0,z1,evidence):
 group(id,'architecture_wall',evidence,relations=['bounded_by:floor','bounded_by:ceiling']);length=b-a
 holes=[]
 if id=='mirror_feature_wall':holes=[(16.60,17.60,0,2.05)]
 if id=='south_recess_wall':holes=[(19.9,20.9,0,2.05),(22.6,23.6,0,2.05)]
 def wallbox(name,aa,bb,za,zb,offset,thick,material):
  pieces=[(aa,bb,za,zb)]
  for ha,hb,hz0,hz1 in holes:
   nxt=[]
   for x0,x1,y0,y1 in pieces:
    if x1<=ha or x0>=hb or y0>=hz1 or y1<=hz0:nxt.append((x0,x1,y0,y1));continue
    if x0<ha:nxt.append((x0,ha,y0,y1))
    if x1>hb:nxt.append((hb,x1,y0,y1))
    if y1>hz1:nxt.append((max(x0,ha),min(x1,hb),hz1,y1))
   pieces=nxt
  for k,(x0,x1,y0,y1) in enumerate(pieces):
   if x1-x0<1e-5 or y1-y0<1e-5:continue
   loc=[(x0+x1)/2,value+offset,(y0+y1)/2] if axis=='y' else [value+offset,(x0+x1)/2,(y0+y1)/2];dims=[x1-x0,thick,y1-y0] if axis=='y' else [thick,x1-x0,y1-y0];cube(name+'_'+str(k),loc,dims,material)
 wallbox('backing',a,b,z0,z1,0,.16,'panel_shadow')
 steps=round(length/.95);levels=[z0,z1] if z1-z0<2.8 else [z0,z0+2,z0+3.6,z1]
 for i in range(steps):
  for j in range(len(levels)-1):
   offset=.0975 if axis=='y' else .0975*C['wall_panel_x_sign'].get(id,-1)
   wallbox(f'panel_{i}_{j}',a+i*length/steps+.008,a+(i+1)*length/steps-.008,levels[j]+.009,levels[j+1]-.009,offset,.035,'ivory_oak')
paneled_wall('east_end_wall','x',27.5,16,26,0,5,[33,129,155]);paneled_wall('west_end_wall','x',8,16,26,0,5,[91,100]);paneled_wall('south_recess_wall','y',16,8,27.5,0,5,[82,33]);paneled_wall('mirror_feature_wall','y',17.88,11.1,18.2,0,5,[61,74,82]);paneled_wall('feature_return_east','x',18.2,16,17.9,0,5,[82]);paneled_wall('feature_return_west','x',11.1,16,17.9,0,5,[91]);
# Metallic inset door over front panel, and end wall recess doors.
for j,(x,y) in enumerate([(17.1,18.04),(20.4,16.12),(23.1,16.12)]):
 group(f'interior_door_{j}','door',[61,74,82]);cube('leaf',(x,y,1.0),(.96,.06,2),'aluminium');cube('upper_frame',(x,y+.03,2.035),(1.05,.08,.05),'aluminium')
# Opening at feature wall west edge has a dark jamb behind (inferred corridor).
group('side_corridor','architectural_opening',[82,91]);cube('dark_recess',(10.52,16.25,1.0),(1.05,.08,2),'panel_shadow')
# Window bays white observed exterior, semantically opaque panels for geometric Z.
group('glazed_facade','glazing',[33,91,100,108,118,129],provenance='Observed bright glazed wall. Exterior unobserved, white diffuse/emissive approximation. BVH first opaque glazing depth as prescribed.',relations=['bounded_by:floor','bounded_by:ceiling'])
# Split glazing around observed closed doors. No facade collider crosses an aperture.
spans=[8]+[v for d in sorted(L['doors'],key=lambda d:d['x']) for v in [d['x']-d['width']/2,d['x']+d['width']/2]]+[27.5]
for j in range(0,len(spans)-1,2):
 a,b=spans[j:j+2];cube('pane_segment_'+str(j),((a+b)/2,26.055,2.5),(b-a,.05,5),'window_white');cube('sill_'+str(j),((a+b)/2,25.98,.045),(b-a,.08,.09),'aluminium')
for d in L['doors']:cube('overdoor_'+d['id'],(d['x'],26.055,(5+d['height'])/2),(d['width'],.05,5-d['height']),'window_white')
for j in range(24):
 x=8+j*19.5/23;inside=next((d for d in L['doors'] if abs(x-d['x'])<d['width']/2+.03),None);z0=inside['height'] if inside else 0
 cube(f'mullion_{j}',(x,26,(z0+5)/2),(.045,.075,5-z0),'table_dark')
cube('transom',(17.75,25.98,3.03),(19.5,.075,.055),'table_dark')
for d in L['doors']:
 group(d['id'],'door',[33,100,108,118],provenance='Observed CLOSED double door; frame/leaf dimensions inferred; collider leaves may be disabled for aperture test, exterior unobserved.');x=d['x'];w=d['width'];h=d['height'];y=25.93;g=C['door_frame_width']
 for dx in [-w/2,w/2]:cube('static_jamb_'+str(dx),(x+dx,y,h/2),(g,.10,h),'bronze')
 cube('static_header',(x,y,h),(w,.1,.12),'bronze')
 for side in [-1,1]:
  xc=x+side*w/4;prefix='leaf_'+str(side)
  cube(prefix+'_glass',(xc,y+.015,h/2),(w/2-g,.035,h-.20),'window_white')
  for dx in [-w/4,w/4]:cube(prefix+'_stile_'+str(dx),(xc+dx,y,h/2),(g,.10,h),'bronze')
  for z in [.065,h-.05]:cube(prefix+'_rail_'+str(z),(xc,y,z),(w/2,.1,.13),'bronze')
  line(prefix+'_handle',(x+side*.10,y-.1,.85),(x+side*.10,y-.1,1.6),.015,'bronze',12)
group('window_column','structural_column',[33,91,100,118,129]);c=L['column'];cyl('round_column',c['center'],c['radius'],5,'limestone',64)
# Ceiling slats along two long edge strips.
for side,y,width in [('north',25.15,1.65),('south',17.1,2.2)]:
 group('ceiling_slats_'+side,'ceiling_finish',[33,82,100,129],relations=['attached_to:ceiling'])
 for j in range(98):cube('slat_%03d'%j,(8.05+j*.2,y,4.89),(.07,width,.16),'dark_slats')
# Ten distinct circular wall mirrors measured by camera rays to physical wall.
for m in L['mirrors']:
 group(m['id'],'wall_mirror',m['evidence_frames'],'Observed mirror circle; ray-plane center/radius on y18.045. Thickness inferred, reflected furnishings not duplicated.',relations=['attached_to:mirror_feature_wall']);c=m['center'];rad=m['radius'];cyl('rim',c,rad,.03,'aluminium',64,(pi/2,0,0));cyl('reflector',(c[0],c[1]+.018,c[2]),rad*.973,.014,'mirror',64,(pi/2,0,0))
# Seats: upholstered cylinders and curved partial backrest, small metal feet.
for d in L['chairs']:
 group(d['id'],'lounge_chair' if d['back'] else 'ottoman',[33,61,74,91,129,155]);x,y,z=d['center'];rad=d['radius'];o=cyl('seat',(x,y,.32),rad,.40,'sage_fabric',64);mod=o.modifiers.new('rounded_upholstery','BEVEL');mod.width=.055;mod.segments=4;o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 for k in range(4):
  a=pi/4+k*pi/2;cyl('foot_pad_'+str(k),(x+rad*.72*cos(a),y+rad*.72*sin(a),.023),.029,.024,'aluminium',12);line('foot_'+str(k),(x+rad*.72*cos(a),y+rad*.72*sin(a),.03),(x+rad*.68*cos(a),y+rad*.68*sin(a),.16),.025,'aluminium',12)
 if d['back']:
  vs=[];fs=[];N=32
  for zz in [.47,.87]:
   for rr in [rad*.78,rad]:
    for k in range(N+1):a=d['rotation']-.95+1.9*k/N;vs.append((x+rr*cos(a),y+rr*sin(a),zz))
  m=N+1
  for k in range(N):
   fs.extend([(k,k+1,m+k+1,m+k),(2*m+k,3*m+k,3*m+k+1,2*m+k+1),(k,2*m+k,2*m+k+1,k+1),(m+k,m+k+1,3*m+k+1,3*m+k)])
  fs.extend([(0,m,3*m,2*m),(3*m-1,4*m-1,2*m-1,N)]);o=mesh('curved_back',vs,fs,'sage_fabric');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.modifiers.new('normals','WEIGHTED_NORMAL')
for d in L['tables']:
 group(d['id'],'coffee_table',[33,61,91,129,155]);x,y,z=d['center'];rx,ry=d['radii'];o=cyl('top',(x,y,z),rx,.045,'table_dark',64);o.scale.y=ry/rx
 for k in range(24):
  a=k*2*pi/24;cyl('base_pad_'+str(k),(x+.34*cos(a),y+.28*sin(a),.0275),.024,.033,'table_dark',8);line('rib_'+str(k),(x+.34*cos(a),y+.28*sin(a),.045),(x+.22*cos(a),y+.18*sin(a),z-.02),.022,'table_dark')
 if d['id']=='coffee_table_A':lathe('decorative_bowl',(x,y,z+.024),[(.1,0),(.19,.08),(.18,.14),(.165,.14),(.15,.085),(.07,.035)],'bronze')
# Planter troughs, branching yellow shrub foliage mesh (not fused prediction).
for d in L['planters']:
 group(d['id'],'planter_shrub',[33,82,91,100,129]);x,y,z=d['center'];w,ln,h=d['dimensions'];cube('body',(x,y,z),(w,ln,h),'concrete_pot',.02);cube('soil',(x,y,h+.006),(w-.08,ln-.08,.025),'soil');leaves=[]
 for k in range(C['shrub_branches']):
  ax=x+random.uniform(-.20,.20);ay=y+random.uniform(-ln*.46,ln*.46);angle=random.uniform(0,2*pi);reach=random.uniform(*C['shrub_reach']);top=(ax+reach*cos(angle),ay+reach*sin(angle),h+random.uniform(*C['shrub_height_above_pot']));root=(ax,ay,h);line('branch_'+str(k),root,top,.006,'branch',5)
  for j in range(14):
   t=(j+1)/15;mid=Vector(root).lerp(Vector(top),t);a=angle+j*2.4;tip=mid+Vector((.07*cos(a),.07*sin(a),.025));leaves.append((mid,tip,.005))
 leaves_mesh('yellow_leaves',leaves,'leaf_yellow')
for d in L['plants']:
 group(d['id'],'potted_plant',d['evidence_frames'],'Observed plant type and support; procedural branch/leaf detail inferred');x,y,z=d['center'];kind=d['kind']
 if kind=='bowl':prof=[(.26,0),(.42,.10),(.59,.34),(.59,.40),(.53,.40),(.45,.27)];soil_h=.32
 elif kind in ['vase','tree']:prof=[(.19,0),(.24,.06),(.32,.34),(.29,.54),(.22,.65),(.19,.65),(.20,.55)];soil_h=.58
 else:prof=None;cube('square_pot',(x,y,.35),(.49,.49,.7),'concrete_pot',.015);soil_h=.69
 if prof:lathe('vessel',(x,y,z),prof,'ceramic' if kind!='bowl' else 'concrete_pot')
 cyl('soil',(x,y,soil_h),.20 if kind!='bowl' else .50,.015,'soil');plant_detail((x,y,z),kind)
# Faceted reception desk with triangulated front anchors.
group('reception_desk','reception_desk',[33,108,118,129],'Desk top front triangulated x25.06,y20.41..23.22,z.83..87. Rear depth, irregular facets and thickness inferred.')
x=25.55;y=21.8;vs=[(25.03,20.3,.88),(25.03,23.3,.88),(26.08,23.3,.88),(26.08,20.3,.88),(25.25,20.5,.09),(25.25,23.08,.09),(25.93,23.08,.09),(25.93,20.5,.09),(24.95,21.78,.40)];fs=[(0,1,2,3),(0,4,8),(4,5,8),(5,1,8),(1,0,8),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,7,6,5)];mesh('faceted_body',vs,[tuple(reversed(f)) for f in fs],'desk_grey');cube('hidden_support',(25.58,21.8,.0605),(.62,2.5,.099),'table_dark');cube('top',(25.55,21.8,.89),(1.04,2.98,.035),'table_dark',.01)
# Mini succulent on reception surface.
group('desk_succulent','tabletop_plant',[33,108,129],relations=['supported_by:reception_desk']);lathe('pot',(25.5,21.2,.92),[(.045,0),(.06,.1)],'ceramic',24);leaves_mesh('leaves',[((25.5,21.2,1),(25.5+.09*cos(k),21.2+.09*sin(k),1.2),.023) for k in range(7)],'leaf_light')
# Wall crest and U-shaped metal ornament.
group('reception_wall_emblem','wall_art',[33,129,155],relations=['attached_to:east_end_wall']);vs=[(27.34,21.43,2.62),(27.34,22.07,2.62),(27.34,22.07,1.95),(27.34,21.95,1.75),(27.34,21.75,1.67),(27.34,21.55,1.75),(27.34,21.43,1.95)];o=mesh('shield',vs,[tuple(range(7))],'marble_crest');mod=o.modifiers.new('thickness','SOLIDIFY');mod.thickness=.025
for side in [-1,1]:
 y=21.75+side*1.35;line('upright'+str(side),(27.30,y,2.8),(27.30,y,3.35),.018,'table_dark');line('crossarm'+str(side),(27.30,21.75,2.8),(27.30,y,2.8),.018,'table_dark')
for j,(x,y) in enumerate(L['floor_lamps']):
 group(f'floor_lamp_{j}','floor_lamp',[33,61,74,82,91]);cyl('base',(x,y,.035),.19,.07,'bronze');
 for k in [-1,0,1]:line('leg'+str(k),(x+k*.07,y,.04),(x+k*.018,y,1.6),.014,'bronze',12)
 lathe('shade',(x,y,1.47),[(.26,0),(.26,.47),(.245,.47),(.245,0)],'ceiling_plaster');cyl('diffuser',(x,y,1.48),.24,.014,'lamp_glow')
# Bowl pendant profiles and woven ribs. Non-planar rib geometry gives real silhouettes.
for d in L['pendants']:
 group(d['id'],'pendant_light',d['evidence_frames'],d['provenance'],relations=['suspended_from:ceiling']);x,y,z=d['center'];r=d['radius'];height=r*.28
 lathe('bowl',(x,y,z),[(r*.19,0),(r*.32,.015),(r*.55,height*.23),(r*.78,height*.57),(r,height),(r,height+.018),(r*.78,height*.57+.018),(r*.32,.033),(r*.19,.018)],'lamp_woven',64)
 cyl('diffuser',(x,y,z+.008),r*.23,.022,'lamp_glow',48)
 # Real underside ridges, aggregated into one semantic mesh for reproducible fast builds.
 vs=[];fs=[]
 def tube(a,b,rr=.008):
  a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<1e-5:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u);off=len(vs);N=5
  for q in [a,b]:
   for k in range(N):vs.append(q+rr*(u*cos(2*pi*k/N)+v*sin(2*pi*k/N)))
  fs.extend([tuple(off+k for k in range(N-1,-1,-1)),tuple(off+N+k for k in range(N))]);fs.extend([(off+k,off+(k+1)%N,off+(k+1)%N+N,off+k+N) for k in range(N)])
 def underside(t):
  knots=[(.19,0),(.32,.015),(.55,height*.23),(.78,height*.57),(1,height)]
  for (a,za),(b,zb) in zip(knots,knots[1:]):
   if a<=t<=b:return za+(zb-za)*(t-a)/(b-a)-.013
  return -.013
 for k in range(64):
  for j in range(12):
   t0=.26+.74*j/12;t1=.26+.74*(j+1)/12;a=2*pi*k/64+.22*t0;b=2*pi*k/64+.22*t1;tube((x+r*t0*cos(a),y+r*t0*sin(a),z+underside(t0)),(x+r*t1*cos(b),y+r*t1*sin(b),z+underside(t1)))
 for j in range(11):
  t=.29+j*.064
  for k in range(96):
   a=k*2*pi/96;b=(k+1)*2*pi/96;tube((x+r*t*cos(a),y+r*t*sin(a),z+underside(t)-.007),(x+r*t*cos(b),y+r*t*sin(b),z+underside(t)-.007),.006)
 mesh('underside_weave',vs,fs,'bronze')
 line('suspension',(x,y,z+height),(x,y,4.98),.007,'table_dark',8)
 # warm local area glow, no mesh helper
 data=bpy.data.lights.new(d['id']+'_light','AREA');data.energy=18;data.color=(1,.78,.51);data.shape='DISK';data.size=r*.6;o=bpy.data.objects.new(data.name,data);S.collection.objects.link(o);o.location=(x,y,z-.04)
# Inferred daylight through facade.
world=bpy.data.worlds.new('Lobby ambient') if not bpy.data.worlds else bpy.data.worlds[0];S.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.76,.8,.88,1);world.node_tree.nodes['Background'].inputs[1].default_value=C['ambient_strength']
for j,x in enumerate([11,17.5,24]):
 d=bpy.data.lights.new('daylight_'+str(j),'AREA');d.energy=C['daylight_energy'];d.shape='RECTANGLE';d.size=5;d.size_y=4;o=bpy.data.objects.new(d.name,d);S.collection.objects.link(o);o.location=(x,25.8,3.7);o.rotation_euler=(Vector((x,20,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
S.render.engine='CYCLES';S.cycles.device='CPU';S.cycles.samples=12;S.cycles.use_denoising=True;S.cycles.max_bounces=6;S.cycles.diffuse_bounces=3;S.cycles.glossy_bounces=4
S.view_settings.view_transform='AgX';S.view_settings.exposure=C['exposure']
# Exact all180 cameras stored in JSON; save one native camera for convenient inspection.
from mathutils import Matrix
T=json.load(open(R/'cameras.json'))['frames'][33]['camera_to_world'];data=bpy.data.cameras.new('native_sample_0033');o=bpy.data.objects.new(data.name,data);S.collection.objects.link(o);o.matrix_world=Matrix(T)@Matrix.Diagonal((1,-1,-1,1));data.lens=762.8*36/1280;data.sensor_width=36;S.camera=o
# Apply modifiers before export, preserving stable mesh components.
for o in list(S.objects):
 if o.type=='MESH' and o.modifiers:
  bpy.context.view_layer.objects.active=o;o.select_set(True)
  for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  o.select_set(False)
bpy.context.view_layer.update()
for r in records:
 pts=[o.matrix_world@Vector(corner) for n in r['components'] for o in [bpy.data.objects[n]] for corner in o.bound_box];mins=[min(v[k] for v in pts) for k in range(3)];maxs=[max(v[k] for v in pts) for k in range(3)];r['dimensions']=[maxs[k]-mins[k] for k in range(3)];r['bounds']=[mins,maxs]
for r in records:r['component_names']=list(r['components'])
json.dump(dict(objects=records),open(R/'objects.json','w'),indent=2)
exec(compile((R/'repair_colliders.py').read_text(),str(R/'repair_colliders.py'),'exec'))
json.dump(dict(objects=[dict(id=r['id'],category=r['category'],evidence_frames=r['evidence_frames'],provenance=r['provenance']) for r in records],contact_sheets_read=['000_029','030_059','060_089','090_119','120_149','150_179'],original_keyframes_inspected=[33,61,74,82,91,100,108,118,129,155],reflections='10 physical mirrors only; no reflected furniture duplicates'),open(R/'analysis/object_inventory.json','w'),indent=2)
exec(compile((R/'repair_mesh_audit.py').read_text(),str(R/'repair_mesh_audit.py'),'exec'))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(R/'scene.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_apply=True)
print('BUILD_COMPLETE',len(records),'semantic objects',sum(len(r['components']) for r in records),'components')
