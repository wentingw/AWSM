"""Executed by build_scene.py. Semantic compound proxies, no one-box doorway blockers."""
coll=[];portals=[]
def bound(name):
 o=bpy.data.objects[name];pts=[o.matrix_world@Vector(c) for c in o.bound_box];return [[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]]
for r in records:
 parts=[]
 for name in r['components']:
  local=name.split('__',1)[1]
  if any(q in local for q in ['foliage','leaves','branch','weave','soil','stem','trunk']):continue
  state='door_leaf_closed' if r['category']=='door' and ('leaf' in local) else 'static'
  parts.append(dict(component_name=name,shape='box',bounds=bound(name),state=state))
 if r['category']=='pendant_light':parts=[q for q in parts if 'bowl' in q['component_name']]
 coll.append(dict(id=r['id'],object_id=r['id'],shape='compound',parts=parts,physics='inferred static or closed-door proxy; each part tied to real mesh; foliage noncolliding',bounds=r['bounds']))
for d in L['doors']:
 x,w,h=d['x'],d['width'],d['height'];portals.append(dict(id=d['id']+'_portal',door_object_id=d['id'],state='closed',traversable_now=False,traversable_when_leaves_disabled=True,opening_bounds=[[x-w/2+.07,25.86,.13],[x+w/2-.07,26.10,h-.07]],clear_width_m=w-.14,clear_height_m=h-.20,leaf_components=[n for r in records if r['id']==d['id'] for n in r['components'] if '__leaf_' in n],connects=['lobby','unobserved_exterior'],confidence='Observed closed frame; exterior unmodelled and articulation inferred'))
for j,(x,y) in enumerate([(17.1,18.04),(20.4,16.12),(23.1,16.12)]):
 id=f'interior_door_{j}';portals.append(dict(id=id+'_portal',door_object_id=id,state='closed',traversable_now=False,traversable_when_leaves_disabled=True,opening_bounds=[[x-.46,y-.25,.02],[x+.46,y+.12,1.97]],clear_width_m=.92,clear_height_m=1.95,leaf_components=[n for r in records if r['id']==id for n in r['components'] if '__leaf' in n],connects=['lobby','unobserved_interior'],confidence='Closed observed metallic leaf; wall opening and hidden continuation inferred, no destination room claimed'))
portals.append(dict(id='side_corridor_recess',state='open_recess',traversable_now=True,traversable_extent_m=1.4,opening_bounds=[[10.05,16.31,.02],[10.98,18.05,1.96]],connects=['lobby','finite_inferred_recess'],confidence='Only recess visible; rear cap is declared unknown-extent boundary, not a claimed connected corridor'))
json.dump(dict(coordinate_frame='model native metric Z up',colliders=coll,portals=portals,status='author logical proxy validation pending; no dynamics simulation'),open(R/'colliders.json','w'),indent=2)
