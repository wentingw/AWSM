"""M3 Astra semantic parametric scene. Run in Blender 5.2 with --background --python.
Input geometry_plan.json is derived only from the packet's RGB, OpenVINS and MapAnything.
All coordinates remain in supplied OpenVINS native metric frame; no GT or other scene.
"""
import bpy, math, json, sys, random, hashlib, time
from pathlib import Path
from mathutils import Matrix,Vector
OUT=Path(__file__).resolve().parent
PLAN=json.load(open(OUT/'geometry_plan.json'))
PACKET=json.load(open(PLAN['packet_path']))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1.0
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=20
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Daylight');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.70,.80,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.22
scene.view_settings.view_transform='AgX'
materials={}
def mat(name,col,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*col,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;materials[name]=m;return m
mat('stone',(.48,.47,.42),.24);mat('panel',(.55,.53,.45),.6);mat('joint',(.095,.085,.07),.48);mat('upholstery',(.22,.29,.15),.84);mat('charcoal',(.018,.017,.014),.42);mat('planter_gray',(.25,.26,.25),.72);mat('soil',(.045,.035,.02),1);mat('leaf',(.12,.22,.06),.8);mat('yellow_leaf',(.43,.34,.08),.82);mat('trunk',(.14,.095,.04),.9);mat('gold',(.39,.28,.12),.28,.75);mat('mirror',(.92,.94,.94),.025,1);mat('metal',(.55,.56,.55),.25,.7);mat('lamp',(.91,.84,.66),.5)
emit=mat('window',(.97,.98,1),.2);bs=emit.node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=(.97,.98,1,1);bs.inputs['Emission Strength'].default_value=.9
mat('carpet',(.025,.022,.017),.10)
mat('orange_flower',(.85,.21,.015),.55);mat('emblem_white',(.80,.82,.79),.3);mat('facet_light',(.075,.080,.074),.27);mat('facet_dark',(.023,.027,.024),.33)
# Subtle aligned rectangular motif: procedural material, never a pasted scene image.
m=materials['carpet'];nt=m.node_tree;tex=nt.nodes.new('ShaderNodeTexBrick');tex.inputs['Color1'].default_value=(.16,.12,.045,1);tex.inputs['Color2'].default_value=(.005,.004,.003,1);tex.inputs['Mortar'].default_value=(.0015,.0012,.001,1);tex.inputs['Scale'].default_value=63;tex.inputs['Mortar Size'].default_value=.075;tex.inputs['Brick Width'].default_value=.55;tex.inputs['Row Height'].default_value=.38;nt.links.new(tex.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
allobjects=[];colliders=[];current=[]
def remember(o,material):
 if material:o.data.materials.append(materials[material])
 current.append(o);return o

def box(name,c,s,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name=name;o.dimensions=s;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('soft edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return remember(o,material)
def cylinder(name,c,r,h,material,vertices=40):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=h,location=c);o=bpy.context.object;o.name=name
 for p in o.data.polygons:p.use_smooth=(len(p.vertices)==4)
 return remember(o,material)
def sphere(name,c,s,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=1,location=c);o=bpy.context.object;o.name=name;o.scale=s
 for p in o.data.polygons:p.use_smooth=True
 return remember(o,material)
def rod(name,a,b,r,material):
 a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,material,12);o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');return o

def arc_back(name,c,r,h,z,theta,material):
 # Thick upholstered back, lower opening oriented toward the central table.
 vertices=[];N=26;thick=.15*r
 for height in [z,z+h]:
  for radius in [r-thick,r]:
   for i in range(N+1):
    a=theta+math.radians(35+290*i/N);vertices.append((c[0]+radius*math.cos(a),c[1]+radius*math.sin(a),height))
 faces=[];L=N+1
 for i in range(N):
  faces += [(i,i+1,L+i+1,L+i),(2*L+i,3*L+i,3*L+i+1,2*L+i+1),(i,2*L+i,2*L+i+1,i+1),(L+i,L+i+1,3*L+i+1,3*L+i)]
 faces.extend([(0,L,3*L,2*L),(N,2*L-1,4*L-1,3*L-1)])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);remember(o,material);mod=o.modifiers.new('upholstered radius','BEVEL');mod.width=.035;mod.segments=3

def leaves(name,c,extent,yellow=False,count=24):
 random.seed(name);material='yellow_leaf' if yellow else 'leaf'
 for i in range(count):
  a=random.uniform(0,2*math.pi);rr=math.sqrt(random.random());pt=(c[0]+math.cos(a)*extent[0]*rr,c[1]+math.sin(a)*extent[1]*rr,c[2]+random.uniform(-.3,.7)*extent[2]);o=sphere(name+'_leaf',pt,((.065 if yellow else extent[0]*.14),(.018 if yellow else extent[1]*.08),(.050 if yellow else extent[2]*.23)),material);o.rotation_euler=(random.uniform(-.7,.7),random.uniform(-.7,.7),a)
  if yellow:rod(name+'_twig',c,pt,.004,'trunk')


def mesh_obj(name,verts,faces,material):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);return remember(o,material)

def tube_paths(name,paths,radius,material):
 verts=[];faces=[];sides=6
 for path in paths:
  start=len(verts)
  for j,p in enumerate(path):
   pt=Vector(p);tangent=Vector(path[min(j+1,len(path)-1)])-Vector(path[max(j-1,0)]);tangent.normalize();side=tangent.cross(Vector((0,0,1)))
   if side.length<.01:side=tangent.cross(Vector((0,1,0)))
   side.normalize();up=tangent.cross(side).normalized()
   for k in range(sides):verts.append(tuple(pt+radius*(math.cos(k*2*math.pi/sides)*side+math.sin(k*2*math.pi/sides)*up)))
  for j in range(len(path)-1):
   for k in range(sides):a=start+j*sides+k;b=start+j*sides+(k+1)%sides;faces.append((a,b,b+sides,a+sides))
 return mesh_obj(name,verts,faces,material)

def grass_blades(name,c,radius,height,count=110,broad=False):
 random.seed(name);verts=[];faces=[]
 for j in range(count):
  a=random.random()*2*math.pi;r=radius*math.sqrt(random.random())*.55;root=Vector((c[0]+r*math.cos(a),c[1]+r*math.sin(a),c[2]));h=height*random.uniform(.5,1.1);spread=radius*random.uniform(.25,.8);width=(.095 if broad else .016)*random.uniform(.5,1.3);side=Vector((-math.sin(a),math.cos(a),0));start=len(verts)
  for k in range(6):
   t=k/5;pt=root+Vector((math.cos(a)*spread*t*t,math.sin(a)*spread*t*t,h*(t-.15*t*t)));w=width*math.sin(math.pi*(.04+.96*t))
   verts.extend([tuple(pt-side*w),tuple(pt+side*w)])
  for k in range(5):faces.append((start+2*k,start+2*k+1,start+2*k+3,start+2*k+2))
 return mesh_obj(name,verts,faces,'leaf')

def open_bowl(name,c,r,h,material):
 verts=[];faces=[];profile=[(r*.45,-h*.50),(r*.80,-h*.32),(r,-h*.02),(r,h*.43),(r*.91,h*.50),(r*.85,h*.32),(r*.64,-h*.27),(r*.22,-h*.32)];N=48
 for rr,zz in profile:
  for j in range(N):a=j*2*math.pi/N;verts.append((c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),c[2]+zz))
 for k in range(len(profile)-1):
  for j in range(N):a=k*N+j;b=k*N+(j+1)%N;faces.append((a,b,b+N,a+N))
 faces.append(tuple(range((len(profile)-1)*N,len(profile)*N)))
 return mesh_obj(name,verts,faces,material)

entity_objects={}
for ent in PLAN.get('scene_entities',[]):
 root=bpy.data.objects.new(ent['object_id'],None);scene.collection.objects.link(root);root['category']=ent['category'];entity_objects[ent['object_id']]=root
for ent in PLAN.get('scene_entities',[]):
 if ent.get('parent'):entity_objects[ent['object_id']].parent=entity_objects[ent['parent']]

for spec in PLAN['objects']:
 current=[];oid=spec['object_id'];kind=spec['category'];c=spec['center'];s=spec['size'];x,y,z=c;dx,dy,dz=s;base=z-dz/2;attributes=spec.get('attributes',{})
 if kind in ['floor','wall','ceiling','carpet','surface_inlay','door','window','wall_panel']:
  box(oid,c,s,spec.get('material',{'floor':'stone','wall':'panel','ceiling':'stone','carpet':'carpet','surface_inlay':'carpet','door':'metal','window':'window','wall_panel':'panel'}[kind]),.01 if kind=='wall_panel' else 0)
 elif kind=='column':cylinder(oid,c,dx/2,dz,'stone')
 elif kind in ['lounge_chair','ottoman']:
  cylinder(oid+'_seat',(x,y,base+dz*.34),min(dx,dy)/2,dz*.55,'upholstery');cylinder(oid+'_plinth',(x,y,base+dz*.07),min(dx,dy)*.39,dz*.14,'charcoal')
  if kind=='lounge_chair':arc_back(oid+'_back',c,min(dx,dy)/2,dz*.43,base+dz*.52,spec.get('yaw',0),'upholstery')
 elif kind=='coffee_table':
  cylinder(oid+'_top',(x,y,z+dz*.40),dx/2,dz*.18,'charcoal');cylinder(oid+'_base',(x,y,base+dz*.09),dx*.32,dz*.16,'charcoal')
  for j in range(22):
   a=2*math.pi*j/22;rod(oid+'_leg',(x+dx*.30*math.cos(a),y+dx*.30*math.sin(a),base+dz*.1),(x+dx*.19*math.cos(a),y+dx*.19*math.sin(a),base+dz*.8),.025,'charcoal')
 elif kind=='rectangular_planter':
  box(oid+'_container',c,s,'planter_gray',.025);box(oid+'_soil',(x,y,z+dz*.48),(dx*.94,dy*.90,.025),'soil')
  yellow='yellow' in attributes.get('foliage','')
  random.seed(oid)
  for j in range(14 if yellow else 0):
   px=x+random.uniform(-.43,.43)*dx;py=y+random.uniform(-.4,.4)*dy;h=spec.get('foliage_height',dz*1.4)*random.uniform(.7,1);rod(oid+'_branch',(px,py,z+dz/2),(px+random.uniform(-.15,.15),py+random.uniform(-.15,.15),z+dz/2+h),.011 if yellow else .028,'trunk');leaves(oid+str(j),(px,py,z+dz/2+h*.7),(dx*.15,dy*.3,h*.5),yellow,12 if yellow else 4)
  if not yellow:
   grass_blades(oid+'_upright_leaves',(x,y,z+dz/2),max(dx,dy)*.75,spec.get('foliage_height',1.4),18,True)
   stemtop=(x+.11,y-.03,z+dz/2+spec.get('foliage_height',1.4)*1.05);rod(oid+'_flower_stem',(x,y,z+dz/2),stemtop,.018,'leaf')
   for k in range(5):
    o=sphere(oid+'_orange_petals',(stemtop[0]+k*.035,stemtop[1],stemtop[2]+.06+k*.015),(.028,.025,.15),'orange_flower');o.rotation_euler[1]=-.8+k*.22
 elif kind=='round_planter':
  sphere(oid+'_bowl',(x,y,base+dz*.54),(dx*.5,dy*.5,dz*.57),'planter_gray');cylinder(oid+'_soil',(x,y,base+dz*.95),dx*.43,.035,'soil');fh=spec.get('foliage_height',dx*.75)
  if 'tree' in attributes.get('foliage',''):
   for j in [-1,0,1]:rod(oid+'_trunk',(x+j*.07,y,base+dz),(x+j*.10,y,base+dz+fh*.8),.025,'trunk')
   leaves(oid,(x,y,base+dz+fh*.8),(dx*.7,dy*.7,fh*.55),False,70)
  elif oid in ['planter_window_mid','planter_mirror']:grass_blades(oid+'_fine_foliage',(x,y,base+dz*.90),dx*.62,fh,170 if oid=='planter_window_mid' else 210,False)
  else:leaves(oid,(x,y,base+dz+fh*.35),(dx*.55,dy*.55,fh),False,100)
 elif kind=='reception_desk':
  # Observed strongly folded front; named panels remain parts of one desk.
  lower=[(x+dx*.10,y-dy*.48,base+.07*dz),(x+dx*.45,y-dy*.14,base+.03*dz),(x+dx*.12,y+dy*.48,base+.09*dz)]
  upper=[(x+dx*.49,y-dy*.50,base+.96*dz),(x-dx*.07,y-dy*.08,base+.72*dz),(x+dx*.48,y+dy*.50,base+.94*dz)]
  mesh_obj(oid+'_front_fold_left',[lower[0],lower[1],upper[1],upper[0]],[(0,1,2),(0,2,3)],'facet_light')
  mesh_obj(oid+'_front_fold_right',[lower[1],lower[2],upper[2],upper[1]],[(0,1,3),(1,2,3)],'facet_dark')
  mesh_obj(oid+'_visible_end_left',[lower[0],upper[0],(x-dx*.49,y-dy*.5,base+dz),(x-dx*.42,y-dy*.48,base)],[(0,1,2,3)],'facet_dark')
  mesh_obj(oid+'_visible_end_right',[lower[2],upper[2],(x-dx*.49,y+dy*.5,base+dz),(x-dx*.42,y+dy*.48,base)],[(0,1,2,3)],'facet_light')
  box(oid+'_recessed_counter',(x-dx*.17,y,base+dz*.63),(dx*.60,dy*.91,.055),'charcoal',.01)
  box(oid+'_rear_rim_inferred',(x-dx*.465,y,base+dz*.91),(.075,dy,.18*dz),'facet_dark')
  box(oid+'_hidden_base_inferred',(x-dx*.10,y,base+.04),(dx*.63,dy*.88,.08),'charcoal')
 elif kind=='decorative_bowl':open_bowl(oid,c,dx/2,dz,'metal')
 elif kind=='wall_installation':
  # Shield and surrounding U share a single semantic installation parent.
  sw=.62;sh=.93;vs=[(x+.045,y-sw/2,z+sh/2),(x+.045,y+sw/2,z+sh/2),(x+.045,y+sw*.45,z-sh*.18),(x+.045,y,z-sh*.50),(x+.045,y-sw*.45,z-sh*.18),(x+.09,y,z)]
  mesh_obj(oid+'_shield_relief',vs,[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5)],'emblem_white')
  path=[(x+.02,y-1.45,z+1.1),(x+.02,y-1.45,z+.51),(x+.02,y-1.37,z+.37),(x+.02,y-1.2,z+.30),(x+.02,y+1.2,z+.30),(x+.02,y+1.37,z+.37),(x+.02,y+1.45,z+.51),(x+.02,y+1.45,z+1.1)]
  tube_paths(oid+'_surrounding_U',[path],.025,'joint')
 elif kind=='mirror':
  o=cylinder(oid,c,dx/2,dy,'mirror');o.rotation_euler[0]=math.pi/2
 elif kind=='pendant_light':
  paths=[];R=dx/2
  for k in range(2,13):
   rr=R*k/12;zz=z-dz*.50*math.sqrt(max(0,1-(rr/R)**2));paths.append([(x+rr*math.cos(a*2*math.pi/64),y+rr*math.sin(a*2*math.pi/64),zz) for a in range(65)])
  for a in range(48):
   angle=a*2*math.pi/48;paths.append([(x+R*t*math.cos(angle),y+R*t*math.sin(angle),z-dz*.50*math.sqrt(max(0,1-t*t))) for t in [.12,.2,.3,.4,.5,.6,.7,.8,.9,1.]])
  tube_paths(oid+'_open_woven_shade',paths,.008,'gold');cylinder(oid+'_diffuser',(x,y,z-dz*.40),dx*.16,.025,'lamp');rod(oid+'_suspension',(x,y,z),(x,y,PLAN['ceiling_z']),.012,'joint')
 elif kind=='floor_lamp':
  cylinder(oid+'_stand',(x,y,base+dz*.42),.025,dz*.80,'metal');cylinder(oid+'_base',(x,y,base+.025),dx*.35,.05,'metal');cylinder(oid+'_shade',(x,y,base+dz*.85),dx/2,dz*.3,'lamp')
 else:box(oid,c,s,spec.get('material','charcoal'),.02)
 # Semantic parents make GLB readable without converting the model into an opaque scan.
 parent=bpy.data.objects.new(oid,None);scene.collection.objects.link(parent);parent['category']=kind
 target=next((r['object_id'] for r in spec.get('spatial_relations',[]) if r['relation']=='member_of'),'lobby')
 if target in entity_objects:parent.parent=entity_objects[target]
 for ob in current:ob.parent=parent;ob['semantic_object_id']=oid
 bpy.context.view_layer.update()
 points=[ob.matrix_world@Vector(v) for ob in current for v in ob.bound_box]
 lo=[min(v[k] for v in points) for k in range(3)];hi=[max(v[k] for v in points) for k in range(3)]
 obj={**spec,'bounds':[lo,hi],'center':[(lo[k]+hi[k])/2 for k in range(3)],'spatial_relations':spec.get('spatial_relations',[{'relation':'inside','object_id':'lobby'}])};allobjects.append(obj)
 if spec.get('collider',True):
  # Hard collision body excludes soft plant leaves and decorative lamp suspension.
  bc=spec.get('collider_center',c);bs=spec.get('collider_size',s);colliders.append({'object_id':oid,'role':'floor' if kind=='floor' else ('overhead_obstacle' if kind=='pendant_light' else 'obstacle'),'bounds':[[bc[k]-bs[k]/2 for k in range(3)],[bc[k]+bs[k]/2 for k in range(3)]],'shape':'aabb','geometry_provenance':spec.get('geometry_provenance'),'physical_obstacle':True,'planning_policy':'support' if kind=='floor' else 'blocked','physical_assumptions':'rigid static; plant foliage omitted from hard body' if 'planter' in kind else 'rigid static'})
planning_exclusions=[]
for obj in allobjects:
 if obj['category'] in ['rectangular_planter','round_planter']:
  planning_exclusions.append({'object_id':obj['object_id'],'role':'vegetation_keepout','bounds':obj['bounds'],'physical_obstacle':False,'planning_policy':'blocked','reason':'Plant silhouette is a conservative planning exclusion; foliage is not a rigid collider.'})
# Diffuse area light at the observed glazing, plus weak broad ceiling fill.
bpy.ops.object.light_add(type='AREA',location=PLAN['window_light_location']);light=bpy.context.object;light.name='daylight_through_observed_glazing';light.data.energy=2000;light.data.shape='RECTANGLE';light.data.size=14;light.data.size_y=5;direction=Vector(PLAN['room_center'])-light.location;light.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(PLAN['room_center'][0],PLAN['room_center'][1],PLAN['ceiling_z']-.2));light=bpy.context.object;light.name='broad_ceiling_illumination';light.data.energy=850;light.data.size=15
cameras=[]
for f in PACKET['frames']:
 if 'camera_to_world' not in f:continue
 fid=f['keyframe_index'];T=Matrix(f['camera_to_world']);bpy.ops.object.camera_add();cam=bpy.context.object;cam.name=f'input_camera_{fid:03d}';cam.matrix_world=T@Matrix.Diagonal((1,-1,-1,1));cam.data.lens=762.8/1280*36;cam.data.sensor_width=36;cam.data.sensor_fit='HORIZONTAL';cam.data.clip_start=.02;cam.data.clip_end=200;cameras.append({'frame_id':fid,'camera_to_world':f['camera_to_world'],'pose_convention':'OpenCV RDF','intrinsics':[[762.8,0,640],[0,762.8,480],[0,0,1]],'resolution':[1280,960],'model_camera_to_world':f['camera_to_world']})
json.dump({'scene_entities':PLAN.get('scene_entities',[]),'conflict_field_semantics':PLAN.get('conflict_field_semantics',{}),'objects':allobjects,'T_input_model':PLAN['T_input_model'],'units':'m'},open(OUT/'objects.json','w'),indent=2)
json.dump({'colliders':colliders,'units':'m','coordinate_frame':'native OpenVINS input frame','planning_exclusions':planning_exclusions,'navigation':PLAN['navigation'],'unknown_regions':PLAN['navigation']['unknown_regions'],'consumer_contract':'For planning, treat every non-floor collider as blocked and everything outside the model_based_planning_domain as unknown/blocked; inflate by vehicle extent and margin. Physical simulation may omit entries with physical_obstacle=false.'},open(OUT/'colliders.json','w'),indent=2)
json.dump({'cameras':cameras,'T_input_model':PLAN['T_input_model']},open(OUT/'cameras.json','w'),indent=2)
json.dump(PLAN['navigation'],open(OUT/'known_space.json','w'),indent=2)
json.dump({'schema_version':1,'units':'m','coordinate_frame':'native OpenVINS, Z up','T_input_model':PLAN['T_input_model'],'known_navigation_bounds':PLAN['navigation']['model_based_planning_domain']['bounds'],'unknown_regions':PLAN['navigation']['unknown_regions'],'vegetation_keepouts':planning_exclusions,'outside_known_bounds_policy':'unknown_blocked','unknown_regions_are_physical_colliders':False,'required_margin_m':.15,'inflate_by_agent_extent':True,'physical_collision_layer_alone_is_sufficient':False,'limitations':'Model-space simulation domain only. Metric input conflicts remain; this is not a validated real-world navigation map.'},open(OUT/'navigation_constraints.json','w'),indent=2)
scene['method']='M3';scene['geometry_inputs']='supplied OpenVINS + MapAnything';scene['T_input_model']=str(PLAN['T_input_model'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'scene.glb'),export_format='GLB',export_cameras=True,export_lights=False,export_yup=False)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--render' in args:
 ids=PLAN.get('render_frames',[5,60,90,105,126]);scene.render.resolution_x=640;scene.render.resolution_y=480
 for fid in ids:
  scene.camera=bpy.data.objects[f'input_camera_{fid:03d}'];scene.render.filepath=str(OUT/f'check_r{PLAN["revision"]}_{fid:03d}.png');bpy.ops.render.render(write_still=True)
print('M3 semantic scene complete:',len(allobjects),'objects,',len(colliders),'colliders')
