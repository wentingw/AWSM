from pathlib import Path
B=Path(__file__).resolve().parent;p=B/'build_scene.py';s=p.read_text();(B/'build_scene_v2.py').write_text(s)
s=s.replace('import bpy, math, json','import bpy, bmesh, math, json')
s=s.replace("(.036,.037,.033),.25,.3","(.028,.030,.026),.05,.58")
s=s.replace("(1,.66,.27),0,.35,4","(.88,.57,.24),0,.35,1.2")
s=s.replace(".48,.14)",".48,.055)").replace("np.array([.24,.19,.095])","np.array([.42,.35,.21])").replace("uv.data[li].uv=(v.x/2.0,v.y/2.0)","uv.data[li].uv=(v.x,v.y)")
s=s.replace("[0,90,108,138],collide=False,attrs={'appearance'","[0,90,108,138],collide=True,attrs={'appearance'")
s=s.replace("for di,xc in enumerate([14.05,22.82]):","for di,(xc,dw) in enumerate([(13.021,2.073),(22.848,1.955)]):")
s=s.replace("def door(xc=xc):","def door(xc=xc,dw=dw):").replace("[xc-.79,xc,xc+.79]","[xc-dw/2+.07,xc,xc+dw/2-.07]").replace("(.115,.09,2.82)","(.14,.09,2.82)").replace("(1.65,.10,.14)","(dw,.10,.16)")
s=s.replace("def seat(x,y,r=.53,back=True,theta=0):","def seat(x,y,r=.53,back=True,theta=0,seat_top=.52):")
s=s.replace("s=cylinder('Round upholstered seat',(x,y,.32),r,.40,sage,64)","s=cylinder('Round upholstered seat',(x,y,(seat_top+.12)/2),r,seat_top-.12,sage,64)")
s=s.replace("for z in [.37,.79]:","for z in [seat_top-.15,seat_top+.27]:")
s=s.replace("(n,2*m-1,4*m-1,3*m-1)","(3*m-1,4*m-1,2*m-1,n)")
s=s.replace("o=mesh('Curved padded backrest',vs,fs,sage);be=o.modifiers.new", "o=mesh('Curved padded backrest',vs,fs,sage);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();be=o.modifiers.new")
s=s.replace("be.width=.045;be.segments=3","be.width=.028;be.segments=3")
s=s.replace("(12.66,20.43,.51,True,-1.3),(13.39,20.43,.54,False,0),(11.95,20.7,.50,True,-2.8)","(12.792,20.491,.36,True,-1.4),(13.396,20.445,.352,False,0),(12.301,20.783,.39,True,-2.7),(12.166,21.635,.41,False,0)")
s=s.replace("lambda x=x,y=y,r=r,b=b,t=t:seat(x,y,r,b,t),[0,60,70,90,138]", "lambda x=x,y=y,r=r,b=b,t=t,i=i:seat(x,y,r,b,t,.42 if i>=5 else .52),[0,60,66,70,90,138]")
s=s.replace("'seat_height_m':.52","'seat_height_m':.42 if i>=5 else .52")
s=s.replace("def table(x,y,rx,ry):","def table(x,y,rx,ry,theta=0):")
s=s.replace("o.scale=(rx,ry,1)","o.scale=(rx,ry,1);o.rotation_euler.z=theta")
s=s.replace("[(16.12,22.25,.46,.53),(12.858,21.429,.78,.58)]","[(16.12,22.25,.46,.53),(12.973,21.504,.40,.60)]")
s=s.replace("lambda x=x,y=y,rx=rx,ry=ry:table(x,y,rx,ry)","lambda x=x,y=y,rx=rx,ry=ry,i=i:table(x,y,rx,ry,-.22 if i else 0)")
s=s.replace("for i,y in enumerate([19.30,23.3]):sem('tropical_front_'+str(i),'potted_plant',lambda y=y:tropical(9.9,y),[90,100]", "for i,(x,y) in enumerate([(11.10,20.16),(9.9,23.3)]):sem('tropical_front_'+str(i),'potted_plant',lambda x=x,y=y:tropical(x,y),[60,66,90,100]")
needle="metadata={'method_id':'M4'"
insert="""# Explicit relations and uncertainty methods required by clean review M4-R08.
for rec in records:
 id=rec['object_id'];cat=rec['category'];rels=rec['spatial_relations']
 if cat in {'table','chair','ottoman','planter'} and not rels:rels.append({'relation':'supported_by','object_id':'floor_dark_inset'})
 if cat in {'potted_plant','floor_lamp','reception_desk','column','door'}:rels.append({'relation':'supported_by','object_id':'floor_stone'})
 if cat=='mirror':rels.append({'relation':'mounted_on','object_id':'wall_south_near'})
 if cat=='pendant_light':rels.append({'relation':'suspended_from','object_id':'ceiling_plaster'})
 if cat=='floor_finish':rels.append({'relation':'supported_by','object_id':'floor_stone'})
 if cat=='bowl':rels.append({'relation':'supported_by','object_id':'coffee_table_0'})
 if cat=='wall_decoration':rels.append({'relation':'mounted_on','object_id':'wall_reception'})
 if any('uncertainty' in k for k in rec['attributes']):rec['attributes']['uncertainty_method']='heuristic author estimate from cross-view inconsistency; not calibrated confidence or measured accuracy'
 if id.startswith('lounge_seat_') and int(id.rsplit('_',1)[1])>=5:rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: near_ottoman_left / near_chair_mid / near_chair_right / missing_ottoman';rec['geometry_provenance']['observed']='manual silhouettes in frames0,60,66,138 projected using supplied K and metric poses; near seat plane z0.42 inferred from triangulated furniture'
 if id=='coffee_table_1':rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: near_table';rec['geometry_provenance']['observed']='manual tabletop outline rays from frames60/138; fitted ellipse with residual retained in measurement file'
 if id=='tropical_front_0':rec['geometry_provenance']['measurement_reference']='revision3_measurements.json and review M4-R04; frame60 top/base rays; reverse90 semantic cross-check'
 if id.startswith('glazed_double_door_'):rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: door_front / door_rear'
 if id.startswith('pendant_'):rec['geometry_provenance']['measurement_reference']='layout_parameters.json and revision3_pendant_matches.json; rejected matches retained'
 if id.startswith('round_wall_mirror'):rec['geometry_provenance']['measurement_reference']='layout_parameters.json: mirrors, frame70 silhouettes on depth-constrained y18.13 plane'
for co in colliders:
 if co['object_id']=='floor_dark_inset':co['role']='floor';co['contact_surface_z']=co['bounds'][1][2];co['note']='Visible raised floor finish; use highest supporting floor top for contact.'
mesh_checks=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Curved padded backrest'):
  bm=bmesh.new();bm.from_mesh(o.data);mesh_checks.append({'mesh':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)});bm.free()
json.dump({'backrest_meshes':mesh_checks,'all_manifold_positive_volume':all(x['nonmanifold_edges']==0 and x['signed_volume']>0 for x in mesh_checks)},open(B/f'mesh_checks_v{REV}.json','w'),indent=2)
"""
s=s.replace(needle,insert+needle)
p.write_text(s)
