"""Reconstruct a fresh M2 semantic scene from layout.json; no saved scene input.
Rebuild: blender -b --factory-startup --threads 2 --python build_scene.py -- --output-dir /path
"""
import bpy,bmesh,math,json,sys,argparse,random
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
SRC=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default=str(SRC));ap.add_argument('--layout',default=str(SRC/'layout.json'));args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=Path(args.output_dir);OUT.mkdir(parents=True,exist_ok=True);L=json.loads(Path(args.layout).read_text());random.seed(2002)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
records={};current=None;rod_requests=[];wall_parts={};seat_polygons={}

def material(name,color,rough=.5,metal=0,emission=0,noise=None):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 if noise:
  n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=noise;n.inputs['Detail'].default_value=2
  bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.015;m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
M={
 'stone':material('pale_polished_terrazzo',(.36,.34,.29),.16,noise=110),
 'blackfloor':material('dark_reflective_floor_inset',(.016,.014,.012),.13,metal=.3),
 'wood':material('vertical_light_wood_panels',(.27,.23,.17),.43,noise=65),
 'grey':material('grey_wall_panels',(.22,.22,.20),.48,noise=80),
 'dark':material('dark_metal',(.035,.036,.031),.29,metal=.65),
 'frame':material('window_mullion',(.16,.18,.17),.25,metal=.8),
 'glass':material('overexposed_glazing',(.96,.98,1),.3,emission=2.1),
 'brass':material('aged_brass',(.45,.32,.12),.22,metal=.8),
 'cloth':material('sage_lounge_fabric',(.25,.31,.16),.79,noise=145),
 'concrete':material('planter_concrete',(.29,.30,.29),.65,noise=80),
 'pot':material('blue_grey_glaze',(.37,.42,.43),.28,noise=45),
 'soil':material('soil',(.06,.045,.022),.9),
 'green':material('leaves_dark_sage',(.12,.22,.065),.8),
 'greenlight':material('leaves_light_sage',(.25,.34,.12),.75),
 'goldleaf':material('yellow_flowering_branches',(.48,.35,.055),.8),
 'trunk':material('branch_bark',(.17,.12,.06),.8),
 'mirror':material('silver_mirrors',(.9,.95,.92),.025,metal=1),
 'shade':material('ivory_shades',(.48,.44,.34),.75),
 'lamp':material('warm_diffusers',(1,.68,.29),.5,emission=4),
 'weave':material('woven_pendant_fibre',(.39,.31,.19),.55),
 'desk':material('faceted_dark_reception',(.10,.11,.105),.27,metal=.12),
 'ceiling':material('warm_plaster_ceiling',(.46,.43,.36),.86,noise=25),
 'marble':material('pale_wall_emblem',(.73,.72,.68),.34,noise=8),
}
# Stretch wood shader coordinates to visible vertical grain.
p=M['wood'].node_tree.nodes.get('Noise Texture');tex=M['wood'].node_tree.nodes.new('ShaderNodeTexCoord');mapping=M['wood'].node_tree.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1,1,.018);M['wood'].node_tree.links.new(tex.outputs['Generated'],mapping.inputs[0]);M['wood'].node_tree.links.new(mapping.outputs[0],p.inputs['Vector'])
# Inferred brass-dash material generated from scratch and packed/exportable; no input textures.
nt=M['blackfloor'].node_tree
width,height=512,2048;xx,yy=np.meshgrid((np.arange(width)+.5)/width,(np.arange(height)+.5)/height);periods=np.array(L['carpet']['dimensions'][:2])*14
mask=((xx*periods[0])%1<.23)&((yy*periods[1])%1<.56)
rgba=np.empty((height,width,4),np.float32);rgba[:]=[.014,.012,.01,1];rgba[mask]=[.17,.125,.055,1]
im=bpy.data.images.new('inferred_floor_dashes',width=width,height=height,alpha=True);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/'floor_pattern.png');im.file_format='PNG';im.save();im.pack();texf=nt.nodes.new('ShaderNodeTexImage');texf.image=im;nt.links.new(texf.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
for key in ['stone','wood','ceiling']:
 for n in M[key].node_tree.nodes:
  if n.type=='BUMP':n.inputs['Distance'].default_value=.002
def group(id,cat,frames,provenance='observed silhouette and measured DA3 region; hidden form, thickness and material inferred',support='floor'):
 global current
 current=id;records[id]={'id':id,'category':cat,'component_names':[],'evidence_frames':frames,'provenance':provenance,'relations':{'supported_by':support}}
def reg(obj,suffix,mat):
 obj.name=current+'__'+suffix;obj.data.name=obj.name+'_mesh';obj.data.materials.append(M[mat]);obj['semantic_id']=current;records[current]['component_names'].append(obj.name);return obj
def box(suffix,loc,dims,mat,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);reg(o,suffix,mat)
 if bevel:
  mod=o.modifiers.new('soft_edges','BEVEL');mod.width=bevel;mod.segments=2;mod=o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 return o
def cyl(suffix,loc,radius,depth,mat,vertices=40):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=bpy.context.object;reg(o,suffix,mat)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o
def sphere(suffix,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=loc);o=bpy.context.object;o.scale=scale;reg(o,suffix,mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def mesh(suffix,verts,faces,mat):
 me=bpy.data.meshes.new(suffix);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(suffix,me);bpy.context.collection.objects.link(o);return reg(o,suffix,mat)
def rod(suffix,a,b,r,mat):
 d=Vector(b)-Vector(a);o=cyl(suffix,(Vector(a)+Vector(b))/2,r,d.length,mat,12);o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');rod_requests.append({'name':o.name,'a':list(a),'b':list(b)});return o
def leaf_batch(suffix,centers,lengths,mat):
 vv=[];ff=[]
 for c,l in zip(centers,lengths):
  c=np.array(c);theta=random.uniform(0,6.283);axis=np.array([math.cos(theta),math.sin(theta),random.uniform(-.3,.6)]);axis/=np.linalg.norm(axis);side=np.array([-axis[1],axis[0],0]);k=len(vv);vv.extend([c-axis*l/2,c+side*l*.17+np.array([0,0,l*.06]),c+axis*l/2,c-side*l*.17]);ff.append((k,k+1,k+2,k+3))
 return mesh(suffix,vv,ff,mat)
def shrub(id,xy,size,pot_kind='bowl',gold=False,frames=[33,129]):
 group(id,'plant_and_planter',frames);x,y=xy;z=L['floor_z'];r,h=size
 if pot_kind=='bowl':sphere('vessel',(x,y,z+.21),(r,r,.24),'pot');base=z+.36
 elif pot_kind=='urn':sphere('vessel',(x,y,z+.32),(.30,.30,.35),'pot');cyl('rim',(x,y,z+.60),.20,.08,'pot');base=z+.65
 elif pot_kind=='tall':box('vessel',(x,y,z+.40),(.46,.46,.80),'concrete',.025);base=z+.80
 else:base=z+.70
 centers=[];lengths=[]
 for j in range(65 if gold else 65):
  theta=random.uniform(0,6.283);rad=random.uniform(.05,r);origin=np.array([x+random.uniform(-r*.6,r*.6),y+random.uniform(-r*.4,r*.4),base]);end=origin+np.array([math.cos(theta)*rad,math.sin(theta)*rad,random.uniform(h*.55,h)]);rod('stem_%02d'%j,origin,end,.009 if gold else .007,'trunk' if gold else 'green')
  for t in np.linspace(.2,1,12 if gold else 7):
   for side in [-1,1]:centers.append(origin*(1-t)+end*t+np.array([math.cos(theta+1.2)*.10*side,math.sin(theta+1.2)*.10*side,0]));lengths.append(random.uniform(.05,.095) if gold else random.uniform(.15,.29))
 leaf_batch('foliage',centers,lengths,'goldleaf' if gold else 'greenlight')
 return records[id]
# Architectural shell.
fz=L['floor_z'];b=L['bounds'];wx=b['window_x'];sy=b['side_x'];ry=b['recess_x'];yn=b['near_y'];yf=b['far_y'];cz=L['ceiling_z']
group('floor','floor',[33,61,82,91,100,129]);box('slab',((wx+ry)/2,(yn+yf)/2,fz-.08),(ry-wx+.4,yf-yn+.4,.16),'stone')
group('floor_inset','floor_finish',[33,91,100,108,155]);o=box('inset',L['carpet']['center'],L['carpet']['dimensions'],'blackfloor')
for face in o.data.polygons:
 for index in face.loop_indices:
  v=o.data.vertices[o.data.loops[index].vertex_index].co;o.data.uv_layers.active.data[index].uv=(v.x/L['carpet']['dimensions'][0]+.5,v.y/L['carpet']['dimensions'][1]+.5)
group('ceiling','ceiling',[33,82,100,129],support='walls');box('slab',((wx+ry)/2,(yn+yf)/2,cz+.08),(ry-wx,yf-yn,.16),'ceiling')
def panelwall(id,start,end,material='wood',horizontal=False,doors=[]):
 group(id,'wall',[33,61,74,82,91,129],support='floor');length=math.dist(start,end);n=max(1,round(length/.86));origin=start[0] if horizontal else start[1]
 # Continuous structural backing, split at exact aperture boundaries. Seams are shallow finish joints.
 cuts=sorted(set([origin,origin+length]+[v+d*w/2 for v,w in doors for d in [-1,1]]));parts=[]
 for j,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
  if hi<=origin or lo>=origin+length:continue
  lo=max(lo,origin);hi=min(hi,origin+length);mid=(lo+hi)/2;opening=any(abs(mid-v)<w/2 for v,w in doors);bottom=fz+L['passage']['height'] if opening else fz
  back_offset=-.10 if id in ['near_wall','recess_return'] else .10
  loc=(mid,start[1]+back_offset,(bottom+cz)/2) if horizontal else (start[0]+.10,mid,(bottom+cz)/2)
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
# Glazing emits as visible overexposed exterior, geometric depth terminates at facade.
group('glazed_facade','window_wall',[33,91,100,108,118,129]);box('panes',(wx-.05,(yn+yf)/2,(cz+fz)/2),(.05,yf-yn,cz-fz),'glass')
for j,y in enumerate(np.arange(yn,yf+.01,.85)):box('mullion_%02d'%j,(wx+.01,float(y),(cz+fz)/2),(.075,.055,cz-fz),'frame')
for j,z in enumerate([fz+.025,2.52,cz-.04]):box('transom_%02d'%j,(wx+.03,(yn+yf)/2,z),(.08,yf-yn,.07),'dark')
for j,y in enumerate([1.0,11.75]):
 group(f'entrance_doors_{j}','double_door',[100,108,118]);records[current]['state']='closed';
 for k,dy in enumerate([-.47,.47]):
  yy=y+dy
  for a,ddy in enumerate([-.45,.45]):box(f'jamb_{k}_{a}',(wx+.08,yy+ddy,1.17),(.09,.15,2.7),'brass')
  for a,z in enumerate([fz+.08,2.47]):box(f'rail_{k}_{a}',(wx+.08,yy,z),(.09,.9,.20),'brass')
  box(f'handle_{k}',(wx+.17,yy+(-.32 if k else .32),1.02),(.05,.026,.75),'dark')
group('round_column','column',[33,91,100,118,129]);cyl('shaft',L['column']['center'],L['column']['radius'],L['column']['height'],'wood',64)
# Ceiling side slats.
for side,(lo,hi) in enumerate([(wx,wx+1.42),(sy-1.40,ry)]):
 group(f'ceiling_slats_{side}','ceiling_trim',[33,82,100,129],support='ceiling')
 for j,y in enumerate(np.arange(yn,yf,.19)):box('slat_%03d'%j,((lo+hi)/2,float(y),cz-.09),(hi-lo,.06,.18),'dark')
# Modular seats have explicitly shared clip boundaries, with 6mm upholstery clearance.
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
 n=len(poly);vv=[(x,y,z) for z in [zlo,zhi] for x,y in poly];ff=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)];o=mesh(suffix,vv,ff,mat)
 for p in o.data.polygons:
  if len(p.vertices)==4 and abs(p.normal.z)<.1:p.use_smooth=True
 return o
for s in L['seats']:
 group(s['id'],'lounge_chair' if s['back'] else 'ottoman',s['evidence_frames']);x,y,z=s['center'];r=s['radius'];poly=seat_clip([[x+r*math.cos(a),y+r*math.sin(a)] for a in np.linspace(0,2*math.pi,65)[:-1]],s);prism('upholstered_base',poly,z-s['height']/2,z+s['height']/2,'cloth');seat_polygons[s['id']]=poly;records[current]['relations']['assembly']='far_modular_cluster' if s['id']<'lounge_seat_06' else 'near_modular_cluster'
 for j,(dx,dy) in enumerate([(-.15,-.15),(-.15,.15),(.15,-.15),(.15,.15)]):cyl('foot_%d'%j,(x+dx,y+dy,fz+.045),.021,.09,'frame',12)
 if s['back']:
  angles=np.linspace(s['yaw']+math.pi*.24,s['yaw']+math.pi*.94,33);poly=[[x+r*.99*math.cos(a),y+r*.99*math.sin(a)] for a in angles]+[[x+r*.73*math.cos(a),y+r*.73*math.sin(a)] for a in reversed(angles)];poly=seat_clip(poly,s);prism('curved_back',poly,z+.19,z+.53,'cloth')
for t in L['tables']:
 group(t['id'],'coffee_table',t['evidence_frames']);x,y,z=t['center'];r=t['radius'];top=cyl('top',(x,y,z),r,.055,'dark',64);top.scale.y=.78;cyl('pedestal',(x,y,(fz+z)/2),r*.32,z-fz,'dark')
 for k in range(22):
  a=2*math.pi*k/22;rod('rib_%02d'%k,(x+math.cos(a)*r*.49,y+math.sin(a)*r*.39,fz+.03),(x+math.cos(a)*r*.29,y+math.sin(a)*r*.25,z-.035),.014,'dark')
 if 'far' in t['id']:sphere('decor_bowl',(x,y,z+.105),(.14,.14,.09),'brass')
# Rectangular flowering planters are single semantic assemblies each.
for p in L['planters']:
 x,y,z=p['center'];group(p['id'],'flowering_planter',[33,82,91,108,129]);box('vessel',p['center'],p['dimensions'],'concrete',.02);box('soil',(x,y,z+.36),(1.55,.48,.02),'soil');saved=records[p['id']]
 shrub(p['id']+'_foliage',(x,y),(.74,.75),'none',True,[33,82,91,129]);fol=records.pop(p['id']+'_foliage');saved['component_names']+=fol['component_names'];
 for name in fol['component_names']:bpy.data.objects[name]['semantic_id']=p['id']
# Accent greenery.
shrub('grass_by_column',(-2.83,5.82),(.60,.63),'bowl');shrub('grass_near_corner',(-2.86,-.94),(.52,.63),'bowl',frames=[91,100]);shrub('grass_reception_corner',(4.8,14.05),(.49,.52),'bowl')
shrub('plant_below_mirrors',(3.15,4.9),(.30,.47),'urn',frames=[61,74,82]);
for j,(x,y) in enumerate([(-1.62,14.35),(2.67,14.36)]):
 group(f'reception_tree_{j}','potted_tree',[33,129]);sphere('urn',(x,y,fz+.30),(.22,.22,.32),'pot');rod('trunk',(x,y,fz+.5),(x,y,1.35),.035,'trunk');cc=[];ll=[]
 for k in range(500):
  theta=random.uniform(0,6.283);phi=random.uniform(-1,1);rr=random.random()**(1/3);cc.append([x+.49*rr*math.sqrt(1-phi*phi)*math.cos(theta),y+.40*rr*math.sqrt(1-phi*phi)*math.sin(theta),1.36+.34*rr*phi]);ll.append(random.uniform(.07,.14))
 leaf_batch('tree_crown',cc,ll,'green')
for j,(x,y) in enumerate([(2.4,-.8),(-1.2,-.9)]):
 shrub(f'tall_flower_{j}',(x,y),(.25,1.0),'tall',frames=[61,82,91]);group(f'orange_flower_{j}','flower',[61,82,91],support=f'tall_flower_{j}')
 rod('stem',(x,y,.6),(x,y,1.65),.015,'green');sphere('bloom',(x+.05,y,1.67),(.11,.04,.05),'brass')
# Circular mirror cluster on vertical wall, no copied reflected furniture.
group('mirror_installation','wall_mirrors',[61,74,82],support='mirror_wall')
for j,d in enumerate(L['mirrors']['discs']):
 o=cyl('disc_%02d'%j,d['center'],d['radius'],.032,'mirror',64);o.rotation_euler[1]=math.pi/2
# Faceted reception desk with real silhouette facets.
group('reception_desk','reception_desk',[33,108,118,129]);x,y,z=L['reception']['center'];w,d,h=L['reception']['dimensions'];verts=[(x-w/2,y-d/2,z+h/2),(x+w/2,y-d/2,z+h/2),(x+w*.55,y+d*.4,z+h*.25),(x-w*.55,y+d*.4,z+h*.25),(x-w*.40,y-d*.27,z-h/2),(x+w*.42,y-d*.27,z-h/2),(x+w*.49,y+d*.25,z-h/2),(x-w*.45,y+d*.25,z-h/2),(x+.12,y-d*.66,z-.02)];mesh('faceted_body',verts,[(0,1,8),(0,8,4),(1,5,8),(4,8,5),(1,2,6,5),(3,0,4,7),(2,3,7,6),(0,3,2,1),(4,5,6,7)],'desk');box('counter',(x,y,z+h/2+.015),(w,.9,.045),'dark',0)
# End-wall insignia is an inferred semantic decoration shape.
group('wall_emblem','wall_decoration',[33,118,129],support='end_wall');o=sphere('shield',(.55,yf-.105,2.20),(.28,.035,.44),'marble');box('crest',(.55,yf-.115,2.44),(.56,.06,.40),'marble')
for s in [-1,1]:rod('horn_vertical_'+str(s),(.55+s*1.1,yf-.13,2.57),(.55+s*1.1,yf-.13,3.33),.024,'dark');rod('horn_horizontal_'+str(s),(.55,yf-.13,2.57),(.55+s*1.1,yf-.13,2.57),.024,'dark')
# Freestanding floor lamps.
for j,(x,y) in enumerate([(4.7,13.6),(4.4,8.8),(2.9,-1.1)]):
 group(f'floor_lamp_{j}','floor_lamp',[33,74,82,91]);cyl('shade',(x,y,1.45),.23,.46,'shade');
 for k in [-1,1]:rod('leg_'+str(k),(x+k*.13,y-.04,fz),(x+k*.035,y,1.31),.013,'brass')
# Measured woven bowl pendants. Woven rings and radial ribs retained as semantic mesh components.
for li in L['lights']:
 group(li['id'],'pendant_light',li['evidence_frames'],li['uncertainty'],support='ceiling');x,y,z=li['center'];r=li['diameter']/2
 # concave bowl shell open above, descending toward inner diffuser.
 vv=[];ff=[];nr=10;ns=64
 for k in range(nr+1):
  rr=r*(.2+.8*k/nr);zz=z+.25*(k/nr)**1.3
  for j in range(ns):a=2*math.pi*j/ns;vv.append((x+rr*math.cos(a),y+rr*math.sin(a),zz))
 for k in range(nr):
  for j in range(ns):a=k*ns+j;bb=k*ns+(j+1)%ns;ff.append((a,bb,bb+ns,a+ns))
 mesh('bowl',vv,ff,'weave');cyl('diffuser',(x,y,z-.008),r*.23,.026,'lamp',48);rod('suspension',(x,y,z+.05),(x,y,cz),.007,'dark')
 # Narrow radial weave and concentric ridges give real relief at render resolution.
 for k in range(1,8):
  rr=r*(.2+.8*k/8);zz=z+.25*(k/8)**1.3
  bpy.ops.mesh.primitive_torus_add(major_radius=rr,minor_radius=.012,major_segments=48,minor_segments=6,location=(x,y,zz-.006));reg(bpy.context.object,'weave_ring_%d'%k,'shade')
 for k in range(24):
  a=k*2*math.pi/24;rod('radial_%d'%k,(x+r*.23*math.cos(a),y+r*.23*math.sin(a),z),(x+r*math.cos(a),y+r*math.sin(a),z+.25),.009,'shade')
# Illumination inferred, no extra image geometry helpers.
world=bpy.data.worlds.new('lobby_world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.8,.9,1);world.node_tree.nodes['Background'].inputs[1].default_value=.24;bpy.context.scene.world=world
for j,y in enumerate([0,5.5,11.5]):
 data=bpy.data.lights.new('daylight_%d'%j,'AREA');data.energy=420;data.shape='RECTANGLE';data.size=4;data.size_y=4.5;o=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(o);o.location=(wx+.3,y,2.6);o.rotation_euler=(0,-math.pi/2,0)
for j,y in enumerate([1.5,7,12]):
 data=bpy.data.lights.new('ceiling_fill_%d'%j,'AREA');data.energy=90;data.size=5;o=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(o);o.location=(0,y,4.55)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.view_transform='AgX';scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
# Default inspection camera is exact native packet camera transformed by X.
cameras=json.loads((SRC/'cameras.json').read_text());T=np.array(cameras['frames'][33]['camera_to_world']);data=bpy.data.cameras.new('native_camera_33');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);cam.matrix_world=Matrix((T@np.diag([1,-1,-1,1])).tolist());data.lens=762.8*36/1280;data.sensor_width=36;scene.camera=cam
bpy.context.view_layer.update()
for rec in records.values():
 pts=[]
 for name in rec['component_names']:
  o=bpy.data.objects[name];pts.extend([o.matrix_world@Vector(c) for c in o.bound_box])
 a=np.array(pts);rec['dimensions']=(a.max(0)-a.min(0)).tolist();rec['bounds']=[a.min(0).tolist(),a.max(0).tolist()]
(OUT/'objects.json').write_text(json.dumps({'objects':list(records.values())},indent=2))
coll=[]
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
if OUT!=SRC:
 (OUT/'layout.json').write_text(json.dumps(L,indent=2));(OUT/'cameras.json').write_text(json.dumps(cameras,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene.blend'));bpy.ops.export_scene.gltf(filepath=str(OUT/'scene.glb'),export_format='GLB',export_apply=True,export_cameras=False,export_lights=False)
print('BUILD_COMPLETE',len(records),'semantic objects',len([o for o in scene.objects if o.type=='MESH']),'meshes')
