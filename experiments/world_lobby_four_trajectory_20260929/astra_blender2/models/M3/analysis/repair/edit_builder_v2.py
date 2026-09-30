from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'build_scene.py';s=p.read_text()
s=s.replace('model v1.', 'model v2 repaired candidate.').replace('import bpy,math,json,random','import bpy,bmesh,math,json,random')
s=s.replace("mat('oak_vertical',(.48,.445,.36)","mat('oak_vertical',(.30,.28,.235)")
s=s.replace("mat('concrete',(.30,.31,.29)","mat('concrete',(.16,.17,.16)")
s=s.replace("materials[name]=m;return m","if name in ['limestone','inset_black_polished'] and noise: bump.inputs['Strength'].default_value=0\n materials[name]=m;return m")
s=s.replace("for p in o.data.polygons:p.use_smooth=True\n return register(o,part,material)","for p in o.data.polygons:p.use_smooth=(len(p.vertices)==4)\n return register(o,part,material)",1)
s=s.replace("cube('bright_glass',((xmin+xmax)/2,3.92,2.625),(xmax-xmin,.045,5.25),'glazing_bright')\nfor j in range(27):cube('mullion_'+str(j),(xmin+j*(xmax-xmin)/26,3.85,2.625),(.035,.08,5.25),'metal_dark')", """door_ranges=[(c-.865,c+.865) for c in L['door_centres']]
facade_cuts=sorted([xmin,xmax]+[v for pair in door_ranges for v in pair])
for j,(a,b) in enumerate(zip(facade_cuts[:-1],facade_cuts[1:])):
 z0=2.74 if any(a>=lo and b<=hi for lo,hi in door_ranges) else 0
 cube('bright_glass_'+str(j),((a+b)/2,3.92,(z0+5.25)/2),(b-a,.045,5.25-z0),'glazing_bright')
for j in range(27):
 xx=xmin+j*(xmax-xmin)/26
 if not any(lo<xx<hi for lo,hi in door_ranges):cube('mullion_'+str(j),(xx,3.85,2.625),(.035,.08,5.25),'metal_dark')""")
s=s.replace("(.065,.10,2.74),'bronze'","(.14,.10,2.74),'bronze'").replace("(.83,.10,.14),'bronze'","(.83,.10,.22),'bronze'")
s=s.replace("for k,dx in enumerate([-.43,.43]):","for k,dx in enumerate([-.43,.43]):\n  cube(f'leaf{k}_glass',(xc+dx,3.79,1.37),(.73,.035,2.52),'glazing_bright')")
s=s.replace("cyl('shaft',(6.75,3.1,2.625),.36,5.25,'limestone',64)","cyl('shaft',L['column']['location'],L['column']['radius'],5.25,'limestone',64)")
s=s.replace("o=mesh('curved_back',vs,fs,'sage_fabric');b=o.modifiers.new", "o=mesh('curved_back',vs,fs,'sage_fabric');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();b=o.modifiers.new")
s=s.replace("bush(x,y,dz,.40,dy*.50,.95,True)","for yy in np.linspace(y-dy*.35,y+dy*.35,4):bush(x,yy,dz,.25,dy*.19,.83,True)")
# Desk shape preserves XY observations; inferred support matches floor inset and shell bottom.
s=s.replace("x,y,z=L['desk']['location'];vs=", "x,y,z=L['desk']['location'];top=L['desk']['top_z'];vs=")
s=s.replace("y-1.6,1.15","y-1.6,top").replace("y+1.6,1.15","y+1.6,top").replace("y+1.5,1.15","y+1.5,top").replace("y-1.5,1.15","y-1.5,top").replace("y-.1,.63","y-.1,.50")
s=s.replace("mesh('faceted_shell',vs,[(0,1,8),(1,5,8),(5,4,8),(4,0,8),(0,4,7,3),(1,2,6,5),(4,5,6,7),(0,3,2,1)],'table_charcoal')", """o=mesh('faceted_shell',vs,[(0,1,8),(1,5,8),(5,4,8),(4,0,8),(0,4,7,3),(1,2,6,5),(4,5,6,7),(0,3,2,1),(3,7,6,2)],'table_charcoal')
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
cube('concealed_plinth',(x,y,.109),(.76,2.50,.182),'table_charcoal')""")
s=s.replace("(15.4,-.5,1.24)","(15.4,-.5,top+.09)").replace("(15.4,-.5,1.3),(15.41,-.5,1.5)","(15.4,-.5,top+.15),(15.41,-.5,top+.35)")
s=s.replace("[(0,1,2,3,4,5,6)],'limestone'","[(6,5,4,3,2,1,0)],'white_linen'")
a=s.index('pendants=[');b=s.index('\nfor j,(x,y,z,r)',a);s=s[:a]+"pendants=L['pendants']"+s[b:]
s=s.replace("# Derive actual semantic bounds for interoperability and conservative physics proxies.","# Semantic bounds and compound logical-object colliders; open portals remain open.")
a=s.index('bpy.context.view_layer.update();out=[];coll=[]');b=s.index('bpy.ops.wm.save_as_mainfile',a)
s=s[:a]+'''bpy.context.view_layer.update();out=[];coll=[]
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
(R/'objects.json').write_text(json.dumps(dict(objects=out),indent=2)+'\\n');(R/'colliders.json').write_text(json.dumps(dict(coordinate_frame='model',units='m',colliders=coll,limitations='Static inferred compound proxies. Doors closed; opening simulation not supplied. Open partition passage has no parent enclosing collider.'),indent=2)+'\\n')
''' +s[b:]
s=s.replace('export_apply=True)','export_apply=True,export_extras=True)')
p.write_text(s)
