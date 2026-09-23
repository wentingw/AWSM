from pathlib import Path
p=Path(__file__).with_name('build_scene.py');s=p.read_text()
s=s.replace("mat('carpet',(.025,.022,.017),.28)","mat('carpet',(.025,.022,.017),.10)\nmat('orange_flower',(.85,.21,.015),.55);mat('emblem_white',(.80,.82,.79),.3);mat('facet_light',(.075,.080,.074),.27);mat('facet_dark',(.023,.027,.024),.33)")
s=s.replace("(.040,.026,.008,1)","(.16,.12,.045,1)").replace("default_value=80","default_value=63")
helpers='''
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
'''
s=s.replace("for spec in PLAN['objects']:",helpers+"\nfor spec in PLAN['objects']:")
s=s.replace("['floor','wall','ceiling','carpet','door','window','wall_panel']","['floor','wall','ceiling','carpet','surface_inlay','door','window','wall_panel']")
s=s.replace("'carpet':'carpet','door'","'carpet':'carpet','surface_inlay':'carpet','door'")
# Reception parts use the same measured bounding dimensions, not a new localization.
a=s.index(" elif kind=='reception_desk':");b=s.index(" elif kind=='mirror':",a)
s=s[:a]+''' elif kind=='reception_desk':
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
'''+s[b:]
a=s.index(" elif kind=='pendant_light':");b=s.index(" elif kind=='floor_lamp':",a)
s=s[:a]+''' elif kind=='pendant_light':
  paths=[];R=dx/2
  for k in range(2,13):
   rr=R*k/12;zz=z-dz*.50*math.sqrt(max(0,1-(rr/R)**2));paths.append([(x+rr*math.cos(a*2*math.pi/64),y+rr*math.sin(a*2*math.pi/64),zz) for a in range(65)])
  for a in range(48):
   angle=a*2*math.pi/48;paths.append([(x+R*t*math.cos(angle),y+R*t*math.sin(angle),z-dz*.50*math.sqrt(max(0,1-t*t))) for t in [.12,.2,.3,.4,.5,.6,.7,.8,.9,1.]])
  tube_paths(oid+'_open_woven_shade',paths,.008,'gold');cylinder(oid+'_diffuser',(x,y,z-dz*.40),dx*.16,.025,'lamp');rod(oid+'_suspension',(x,y,z),(x,y,PLAN['ceiling_z']),.012,'joint')
'''+s[b:]
# Select observed vegetation silhouettes, keeping every leaf inside the same planter parent.
s=s.replace("  for j in range(14 if yellow else 7):", "  for j in range(14 if yellow else 0):")
needle=" elif kind=='round_planter':"
s=s.replace(needle,"""  if not yellow:
   grass_blades(oid+'_upright_leaves',(x,y,z+dz/2),max(dx,dy)*.75,spec.get('foliage_height',1.4),18,True)
   stemtop=(x+.11,y-.03,z+dz/2+spec.get('foliage_height',1.4)*1.05);rod(oid+'_flower_stem',(x,y,z+dz/2),stemtop,.018,'leaf')
   for k in range(5):
    o=sphere(oid+'_orange_petals',(stemtop[0]+k*.035,stemtop[1],stemtop[2]+.06+k*.015),(.028,.025,.15),'orange_flower');o.rotation_euler[1]=-.8+k*.22
"""+needle)
s=s.replace("  else:leaves(oid,(x,y,base+dz+fh*.35),(dx*.55,dy*.55,fh),False,100)","  elif oid in ['planter_window_mid','planter_mirror']:grass_blades(oid+'_fine_foliage',(x,y,base+dz*.90),dx*.62,fh,170 if oid=='planter_window_mid' else 210,False)\n  else:leaves(oid,(x,y,base+dz+fh*.35),(dx*.55,dy*.55,fh),False,100)")
s=s.replace("parent['category']=kind","parent['category']=kind\n target=next((r['object_id'] for r in spec.get('spatial_relations',[]) if r['relation']=='member_of'),'lobby')\n if target in entity_objects:parent.parent=entity_objects[target]")
s=s.replace("'role':'floor' if kind=='floor' else 'obstacle'","'role':'floor' if kind=='floor' else ('overhead_obstacle' if kind=='pendant_light' else 'obstacle')")
s=s.replace("'physical_assumptions':'rigid static;", "'physical_obstacle':True,'planning_policy':'support' if kind=='floor' else 'blocked','physical_assumptions':'rigid static;")
# Extra machine-readable nonphysical planning exclusions must never become made-up walls.
s=s.replace("# Diffuse area light", """for obj in allobjects:
 if obj['category'] in ['rectangular_planter','round_planter']:
  colliders.append({'collider_id':obj['object_id']+'.vegetation_keepout','object_id':obj['object_id'],'role':'vegetation_keepout','bounds':obj['bounds'],'shape':'aabb','physical_obstacle':False,'planning_policy':'blocked','reason':'Conservative plant silhouette; botanical geometry and softness are unmeasured. Required for drone routing; not counted as rigid wall.'})
for region in PLAN['navigation']['unknown_regions']:
 colliders.append({'collider_id':region['region_id'],'object_id':region['region_id'],'role':'unknown','bounds':region['bounds'],'shape':'aabb','physical_obstacle':False,'planning_policy':'blocked','reason':region['reason']})
# Diffuse area light""")
s=s.replace("{'objects':allobjects,'T_input_model'", "{'scene_entities':PLAN.get('scene_entities',[]),'conflict_field_semantics':PLAN.get('conflict_field_semantics',{}),'objects':allobjects,'T_input_model'")
s=s.replace("{'colliders':colliders,'units':'m','coordinate_frame':'native OpenVINS input frame'}", "{'colliders':colliders,'units':'m','coordinate_frame':'native OpenVINS input frame','navigation':PLAN['navigation'],'unknown_regions':PLAN['navigation']['unknown_regions'],'consumer_contract':'For planning, treat every non-floor collider as blocked and everything outside the model_based_planning_domain as unknown/blocked; inflate by vehicle extent and margin. Physical simulation may omit entries with physical_obstacle=false.'}")
s=s.replace("scene['method']='M3'", "json.dump(PLAN['navigation'],open(OUT/'known_space.json','w'),indent=2)\nscene['method']='M3'")
p.write_text(s)
