"""Revision 3: clean-review fixes; uses only existing authorized semantic measurements.
No input geometry, poses, units or global scale is changed.
"""
import math,copy,itertools
import numpy as np

def apply_review_fixes(plan):
 plan=copy.deepcopy(plan);plan['revision']=3;objs=plan['objects'];by={o['object_id']:o for o in objs};floor=plan['floor_z'];ceiling=plan['ceiling_z'];moves=[]
 # Deterministic local circle separation: preserve each group's centroid and leave 3cm.
 for prefix in ['seat_middle_','seat_front_']:
  seats=[o for o in objs if o['object_id'].startswith(prefix)];original={o['object_id']:np.array(o['center'][:2]) for o in seats}
  for _ in range(100):
   changed=False
   for a,b in itertools.combinations(seats,2):
    pa=np.array(a['center'][:2]);pb=np.array(b['center'][:2]);v=pb-pa;dist=float(np.linalg.norm(v));r=(min(a['size'][:2])+min(b['size'][:2]))/2;gap=r+.03-dist
    if gap>1e-8:
     d=v/max(dist,1e-9)*gap/2;pa-=d;pb+=d;a['center'][:2]=pa.tolist();b['center'][:2]=pb.tolist();changed=True
   if not changed:break
  table=by['table_middle' if prefix=='seat_middle_' else 'table_front']
  for o in seats:
   delta=np.array(o['center'][:2])-original[o['object_id']];o['yaw']=math.atan2(table['center'][1]-o['center'][1],table['center'][0]-o['center'][0]);o['local_layout_adjustment']={'revision':3,'delta_xy_m':delta.tolist(),'translation_norm_m':float(np.linalg.norm(delta)),'reason':'Resolve generated seat-solid intersections from clean review R01 with a 3cm gap; uncertain local layout only; supplied measurements unchanged'};moves.append({'object_id':o['object_id'],**o['local_layout_adjustment']})
 # One observed installation with multiple named mesh parts, not extra instance credit.
 e=by['reception_wall_emblem'];e['category']='wall_installation';e['attributes']={'shape':'white pointed shield and surrounding dark U-shaped feature','instance_counting':'one grouped wall installation'};e['geometry_provenance']['revision3_shape']='RGB frames5/126 support shield silhouette and U-shaped surrounding rod; exact relief/thickness inferred';e['size']=[.10,3.05,1.7]
 by['reception']['attributes'].update({'shape':'folded angular front panels with recessed counter and raised perimeter','unseen_backside':'inferred plain rear closure'});by['reception']['geometry_provenance']['revision3_shape']='Strong front facets and visible recessed countertop authored from personally inspected frame105/126 RGB; native metric placement retained as uncertain.'
 # Table bowl: visible original frames5/60, metric size inferred relative to measured table.
 t=by['table_middle'];bowl={'object_id':'table_middle_bowl','category':'decorative_bowl','center':[t['center'][0],t['center'][1],floor+.655],'size':[.34,.34,.20],'attributes':{'shape':'small open dark metallic bowl','measurement_status':'RGB relative proportion; no reliable isolated depth'},'evidence':{'frame_ids':[5,60],'modeller_observation':'visible bowl on center coffee table'},'geometry_provenance':{'source':'permitted RGB and existing table support plane','conflict_present':True,'conflict_reason':'inherits uncertain middle-table metric placement','native_measurements_retained':True},'observed_geometry':'open bowl and rim silhouette','inferred_geometry':'thickness, hidden underside and exact dimensions','confidence':'low','collider':True}
 objs.append(bowl);by[bowl['object_id']]=bowl
 # Resolve semantics and uncertainty consistently for every generated element.
 explicit_conflict={'floor','ceiling','end_wall','entry_wall','window_wall','mirror_wall','table_middle','reception','planter_center_left','planter_center_right','planter_window_mid','planter_mirror','planter_back_left','planter_back_right','planter_back_corner'}|{o['object_id'] for o in objs if o['object_id'].startswith('seat_middle_')}
 for o in objs:
  oid=o['object_id'];cat=o['category'];prov=o['geometry_provenance'];prov=copy.deepcopy(prov) if isinstance(prov,dict) else {'source':prov};o['geometry_provenance']=prov
  prov.pop('conflicting_input_preserved',None);text=str(prov).lower();conflict=oid in explicit_conflict or 'conflict' in text or cat in ['door','column'];prov.pop('conflicting_input_preserved',None);prov['conflict_present']=bool(conflict);prov['native_measurements_retained']=True
  if conflict:prov.setdefault('conflict_reason','Native per-view depth/localization disagreements remain in the measurement logs; selected semantic parameters are an explicit compromise.')
  if oid in explicit_conflict or cat in ['door','column']:o['confidence']='low'
  rel=[{'relation':'inside','object_id':'lobby'}]
  if oid.startswith('window_mullion_') or oid=='window_transom':rel.append({'relation':'part_of','object_id':'window_wall'})
  elif oid.startswith('door_frame_'):
   door='glazed_door_-20.3' if '-20.3' in oid else 'glazed_door_-8.0';rel.append({'relation':'part_of','object_id':door})
  elif oid.startswith('ceiling_slat_'):rel.append({'relation':'part_of','object_id':'ceiling'})
  elif oid.startswith('end_wall_joint_'):rel.append({'relation':'part_of','object_id':'end_wall'})
  elif oid.startswith('wall_joint_'):rel.append({'relation':'part_of','object_id':'mirror_wall'})
  if oid.startswith('seat_middle_') or oid=='table_middle':rel.append({'relation':'member_of','object_id':'seating_group_middle'})
  if oid.startswith('seat_front_') or oid=='table_front':rel.append({'relation':'member_of','object_id':'seating_group_front'})
  if cat in ['lounge_chair','ottoman','coffee_table','rectangular_planter','round_planter','reception_desk','floor_lamp','column']:rel.append({'relation':'supported_by','object_id':'floor'})
  if cat=='pendant_light':rel.append({'relation':'suspended_from','object_id':'ceiling'});o['collider']=True
  if cat=='mirror':rel.append({'relation':'mounted_on','object_id':'mirror_wall'})
  if cat=='wall_installation':rel.append({'relation':'mounted_on','object_id':'end_wall'})
  if oid=='table_middle_bowl':rel.append({'relation':'supported_by','object_id':'table_middle'})
  if oid=='carpet_main':
   o['category']='surface_inlay';o['attributes'].update({'appearance':'dark glossy floor inset with bright rectangular pattern','material_identity':'unknown; carpet is not established from RGB'});rel.append({'relation':'supported_by','object_id':'floor'})
  if cat=='floor_lamp':o['collider_size']=o['size'][:];prov['collision_revision3']='AABB enlarged to entire 0.55m shade diameter, including stand and base; no longer claims narrow stand box covers shade.'
  o['spatial_relations']=rel
 by['ceiling']['geometry_provenance']['regularization']='Median of supplied ceiling normal-mode positions in frames60,90,105,120,126; not the floor rule; no rescaling.'
 for oid in ['glazed_door_-20.3','window_column_-18.8','reception']:
  by[oid]['unresolved_localization']={'frames':[105,126],'issue':'Door/column/reception relative image positions remain inconsistent with selected native metric parameters. No reliable joint localization has been established from conflicting supplied depths. Kept unchanged rather than introducing unsupported correction.','alternatives_log':'depth_semantic_measurements.json and plane_consensus.json'}
 plan['scene_entities']=[{'object_id':'lobby','category':'scene_root','counted_as_model_element':False},{'object_id':'seating_group_middle','category':'semantic_group','parent':'lobby','counted_as_model_element':False},{'object_id':'seating_group_front','category':'semantic_group','parent':'lobby','counted_as_model_element':False}]
 plan['conflict_field_semantics']={'conflict_present':'True means this element is subject to a known depth, pose-relative localization or inherited support conflict, whether one or multiple measurements are attached.','native_measurements_retained':'True means original allowed measurements remain unchanged in the referenced logs; it does not imply agreement or confidence.'}
 # This is a planning constraint, never a made-up physical wall.
 unknown={'region_id':'unknown_mirror_side_continuation','bounds':[[-24.3,4.65,floor],[-13.5,8.15,ceiling]],'classification':'unknown','reason':'Unsupported mirror-wall continuation; visible floor does not establish enclosure or safe egress.','planning_policy':'blocked','physical_obstacle':False,'evidence_frame_ids':[60,90,105,126]}
 plan['navigation']={'schema_version':1,'coordinate_frame':'native OpenVINS, Z up, metres','T_input_model':plan['T_input_model'],'floor_top_z':floor,'model_based_planning_domain':{'bounds':[[-23.2,-4.05,floor],[.10,4.65,ceiling-.35]],'meaning':'Conservative domain of this uncertain reconstruction, not independently validated free space. Must subtract inflated obstacle/vegetation/unknown volumes.','outside_policy':'unknown_blocked'},'unknown_regions':[unknown],'ground_policy':{'support_object_id':'floor','body_bottom_z':floor,'required_obstacle_margin_m':.15,'inflate_by_agent_radius':True},'drone_policy':{'minimum_above_floor_m':.30,'maximum_center_z_before_radius_inflation':ceiling-.35,'required_obstacle_margin_m':.15,'include_overhead_obstacles':True,'include_vegetation_keepouts':True,'inflate_by_vehicle_radius':True},'all_consumers':{'unknown_is_free':False,'physical_collision_layer_alone_is_sufficient':False,'require_navigation_domain':True,'input_metric_accuracy':'unresolved source conflicts; useful for model-space simulation only, not a validated real-world navigation map'}}
 plan['revision3_local_layout_adjustments']=moves
 plan['unresolved'] += ['Door/column/reception relative localization in frames105/126 remains unresolved; chosen metric locations unchanged.','Model-space navigation requires known-domain bounds and unknown/vegetation exclusions; no real-world safety or metric accuracy claim.','Fine weave, botanical structure and relief are parametric approximations; object inventory is not a verified coverage metric.']
 return plan
