"""Author repair preparation, M1-only. Does not render or read saved scenes."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parent
J=lambda p:json.loads((R/p).read_text())
def save(p,x):(R/p).write_text(json.dumps(x,indent=2)+'\n')
# Preserve prior author records and supplement the existing v1 parameter/artifact snapshot.
old=R/'versions/v1/author_records_before_repair';old.mkdir(parents=True,exist_ok=True)
for n in ['colliders.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/measurements.json','analysis/camera_checks.json','analysis/object_inventory.json']:
 dst=old/n;dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copyfile(R/n,dst)
L=J('layout.json');L['version']=2
L['seating_groups'][0]['center']=[3.1,7.9]
L['seat_offsets']=[[-1.1,-.25],[-.95,.73],[0,1.1],[1.0,.7],[1.3,-.3]]
L['planter_dividers_y']=[9.8]
L['side_seats_xy']=[[5.5,7.1],[5.5,6.14],[5.2,5.23]]
L['side_table_xy']=[4.2,5.8]
L['parameter_provenance']='RGB-only inference conditional on unchanged v1 estimated cameras. Cross-view disagreements in analysis/author_repair/rgb_ray_plane_measurements.json; no input depth.'
L['uncertainties']={'north_group_xy_m':1.2,'divider_y_m':.8,'side_seats_xy_m':1.2,'scale_anchor_height_m':[2.6,.35],'south_group':'retained original estimate; sample82 implies more southern table than other views','partition':'retained because moving a common wall to clear camera108 conflicts with61/74/82'}
save('layout.json',L)
s=(R/'build_scene.py').read_text()
s=s.replace('import bpy, math, random, json, argparse, sys','import bpy, bmesh, math, random, json, argparse, sys')
s=s.replace("sc.cycles.samples=12","sc.cycles.samples=12;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.use_file_extension=True;sc.render.image_settings.file_format='PNG';bpy.context.preferences.filepaths.save_version=0")
s=s.replace("default_value=.45","default_value=.18")
s=s.replace("sc.view_settings.view_transform='AgX'","sc.view_settings.view_transform='AgX';sc.view_settings.exposure=-.5")
s=s.replace("records=[];current=None",'''# Appearance adjustments are inferred from fixed source RGB, not measured BRDFs.
for name,color in {'wall_oak':(.30,.275,.225),'wall_gray':(.25,.255,.245),'ceiling':(.43,.415,.37),'shade_weave':(.17,.135,.085),'shade':(.50,.47,.39),'metal_dark':(.035,.038,.034),'brass':(.30,.225,.085)}.items():
 M[name].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
mat('slat_wood',(.065,.052,.035),.62,noise=.15)
# Anisotropic grain in the existing wall shader; generated in object coordinates.
nt=M['wall_oak'].node_tree;noise_node=next(n for n in nt.nodes if n.type=='TEX_NOISE');tex=nt.nodes.new('ShaderNodeTexCoord');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(2,2,.045);nt.links.new(tex.outputs['Generated'],scale.inputs[0]);nt.links.new(scale.outputs[0],noise_node.inputs['Vector'])
records=[];current=None''')
s=s.replace("s=.032;k=len(vs)","s=.012*(.75+.5*random.Random(x*1000+y).random());k=len(vs)")
s=s.replace("(1.4,.065,.16),'wall_oak'","(1.4,.065,.16),'slat_wood'")
s=s.replace("offsets=[(-1.05,-.15),(-.85,.72),(0,1.02),(.90,.75),(1.18,-.1)]","offsets=L['seat_offsets']")
s=s.replace("f.extend([(0,17,34,51),(16,33,50,67)]);o=mesh('curved_back',v,f,'sage');b=o.modifiers.new('rounded_upholstery','BEVEL');b.width=.055;b.segments=3", "f.extend([(51,34,17,0),(16,33,50,67)]);o=mesh('curved_back',v,f,'sage');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()")
s=s.replace("for j,(x,y) in enumerate([(4.9,3.5),(5.5,3.8),(5.4,2.6)]):\n begin('south_side_seat_'+str(j),'modular_lounge_seat',[61,82,91]);lathe('seat',(x,y,0),[(.36,.10),(.45,.17),(.45,.48),(.38,.54),(0,.54)],'sage')", """for j,(x,y) in enumerate(L['side_seats_xy']):
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
x,y=L['side_table_xy'];begin('mirror_side_coffee_table','coffee_table',[33,61,155],{'supported_by':'black_floor_insert','member_of':'mirror_side_seating'},'third table observed beside mirror seats; position inferred compromise across incompatible estimated cameras');cyl('tabletop',(x,y,.43),.60,.048,'metal_dark',64);cyl('support',(x,y,.225),.25,.42,'metal_dark')""")
s=s.replace("begin('reception_desk','reception_counter',[33,108,118,129,155]);", "begin('reception_desk','reception_counter',[33,108,118,129,155],{'supported_by':'floor','support_component':'reception_desk__inferred_plinth'});")
s=s.replace("# Mirror disks:","begin('unused_marker','unused',[])\n# Mirror disks:") if False else s
s=s.replace("begin('reception_wall_emblem'", "box('inferred_plinth',(cx,cy,.055),(2.8,.55,.11),'metal_dark')\nbegin('reception_wall_emblem'")
s=s.replace('# Golden rectangular divider planters, four physical containers.','# Golden divider pair: opposite camera directions observe the same two containers.')
s=s.replace('d.energy=450','d.energy=260').replace('d.energy=120','d.energy=65')
# Remove repeated pole vertices without changing profiles/dimensions; prevent degenerate GLB triangles.
s=s.replace("o=mesh(n,vs,fs,ma)\n for f in o.data.polygons:f.use_smooth=True", "o=mesh(n,vs,fs,ma)\n bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()\n for f in o.data.polygons:f.use_smooth=True")
oldline="colliders.append({'id':rec['id'],'type':'AABB','bounds_min':lo,'bounds_max':hi,'provenance':'inferred simple physics approximation','enabled':rec['category'] not in ['flowering_shrub','shrub','ornamental_grass','topiary','flowering_plant','pendant_light','ceiling_detail']})"
newline="""enabled=rec['category'] not in ['flowering_shrub','shrub','ornamental_grass','topiary','flowering_plant','pendant_light','ceiling_detail']
 if rec['id'] in ['mirror_partition','south_opening']:
  parts=[]
  for name in rec['component_names']:
   o=bpy.data.objects[name];pts=[o.matrix_world@Vector(c) for c in o.bound_box];parts.append({'component_name':name,'type':'AABB','bounds_min':[min(c[k] for c in pts) for k in range(3)],'bounds_max':[max(c[k] for c in pts) for k in range(3)]})
  colliders.append({'id':rec['id'],'object_id':rec['id'],'type':'COMPOUND','parts':parts,'provenance':'component boxes preserve open south doorway; finite rear recess wall inferred','enabled':True})
 else:
  colliders.append({'id':rec['id'],'object_id':rec['id'],'type':'AABB','bounds_min':lo,'bounds_max':hi,'provenance':'inferred simple physics approximation of this logical object','enabled':enabled})"""
assert oldline in s;s=s.replace(oldline,newline)
s=s.replace("json.dumps({'colliders':colliders},indent=2)","json.dumps({'colliders':colliders,'portals':[{'id':'south_opening','clear_bounds_min':[6.70,3.55,.02],'clear_bounds_max':[7.85,4.30,2.55],'width_m':.75,'height_m':2.53,'state':'enterable_finite_recess','onward_connectivity':'unobserved; inferred back wall atx7.95; not a validated through-route'},{'id':'north_metal_door','state':'closed','collider_id':'north_metal_door'}]},indent=2)")
(R/'build_scene.py').write_text(s)
m=J('modelling_manifest.json');m.update(revisions=2,status='building_repaired_candidate',quality_status='LIMITED');save('modelling_manifest.json',m)
print('V2_PREPARED; cameras unchanged; no build or render yet')
