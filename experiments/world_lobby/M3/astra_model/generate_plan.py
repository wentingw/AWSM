"""Make explicitly regularized semantic solids from logged M3 measurements."""
import json,hashlib,math
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent;ROOT=OUT.parents[3];packet=ROOT/'data/packets/M3/packet.json'
p=json.load(open(packet));m=json.load(open(OUT/'depth_semantic_measurements.json'));ann={o['id']:o for o in m['objects']};planes=json.load(open(OUT/'plane_consensus.json'))
floor=float(np.median([r['planes']['floor']['median'] for r in planes['frames']]));ceiling=float(np.median([r['planes']['ceiling']['median'] for r in planes['frames'] if r['frame'] in [60,90,105,120,126]]))
objs=[]
def add(oid,cat,c,s,frames,provenance,**kw):
 objs.append({'object_id':oid,'category':cat,'center':list(c),'size':list(s),'attributes':kw.pop('attributes',{}),'evidence':{'frame_ids':frames,'modeller_observation':'personally inspected original RGB; manually marked regions in annotations.json'},'geometry_provenance':provenance,'observed_geometry':kw.pop('observed_geometry','visible surface dimensions approximated by parametric primitive'),'inferred_geometry':'unseen backside, closed base, thickness, joints; rigid static physics assumed','confidence':kw.pop('confidence','medium'),**kw})
planeprov={'source':'supplied MapAnything depth + OpenVINS','measurement_log':'plane_consensus.json','regularization':'one horizontal support plane: equal-weight median of ten time-spaced measured floor modes; no input pose/depth rescaling'}
# Floor extents use observed depth across the camera loop. The far mirror-side wall is
# left unclosed because its extrapolation intersects supplied camera poses.
add('floor','floor',[-11.4,1.65,floor-.10],[25.8,13.0,.20],[5,60,90,105,126],planeprov)
add('ceiling','ceiling',[-11.4,.3,ceiling+.08],[25.8,10.4,.16],[60,90,105,120,126],planeprov)
add('window_wall','window',[-11.4,-4.55,(floor+ceiling)/2],[25.8,.08,ceiling-floor],[5,90,105,126],{'source':'median window plane from representative native depth; glowing opaque approximation to overexposed glazing'})
add('mirror_wall','wall',[-6.0,5.13,(floor+ceiling)/2],[15.0,.16,ceiling-floor],[60,90],{'source':'direct semantic ROI wall y medians 4.906 and5.335m','unresolved':'wall continuation beyond x=-13.5 unmodeled: poses reach y7.8, conflicting with straight extension'},confidence='medium')
add('end_wall','wall',[-23.56,1.65,(floor+ceiling)/2],[.16,13.0,ceiling-floor],[105,120,126],{'source':'near end-wall modes x=-24.526,-23.871,-22.272; median=-23.871; semantic ROI126=-22.291; compromise x=-23.56','conflict':'frame5 end-wall depth puts same surface x=-15.004'},confidence='low')
add('entry_wall','wall',[.6,.3,(floor+ceiling)/2],[.16,10.4,ceiling-floor],[90],{'source':'frame90 ROI median x=-.14; inferred thickness/extent; placement +.6 reserves observed camera margin'},confidence='low')
add('carpet_main','carpet',[-11.0,.1,floor+.008],[22.5,6.2,.016],[5,60,90,105],{'source':'RGB visible black rectangular patterned floor region; depth supplies shared floor height','inference':'planar decorative material boundary'},collider=False)
# Explicit modular wall panels/mullions, dimensions from room shell rather than an imported scene.
for x in np.arange(-23.0,1.0,1.4):
 add(f'window_mullion_{len(objs)}','trim',[x,-4.47,(floor+ceiling)/2],[.035,.06,ceiling-floor],[5,105,126],{'source':'observed repeating glazing mullions; spacing regularized within measured shell'},material='joint',collider=False)
add('window_transom','trim',[-11.4,-4.45,floor+3.5],[25.8,.075,.04],[105,126],{'source':'observed horizontal glazing transom'},material='joint',collider=False)
for x in [-20.3,-8.0]:
 add('glazed_door_'+str(x),'door',[x,-4.40,floor+1.7],[1.8,.10,3.4],[5,105,126],{'source':'two double-door bays directly visible along glazing; approximate native positioning'},material='window')
 for dx in [-.9,0,.9]:add('door_frame_'+str(x)+str(dx),'trim',[x+dx,-4.32,floor+1.7],[.08,.12,3.4],[105,126],{'source':'observed gold door frames'},material='gold',collider=False)
for x in [-18.8,-8.5]:add('window_column_'+str(x),'column',[x,-3.83,(floor+ceiling)/2],[.58,.58,ceiling-floor],[5,105,126],{'source':'observed round glazing-side columns; near frame126 depth and regularized radius'})
for x in np.arange(-13,1.5,1.4):add('wall_joint_'+str(round(x,2)),'trim',[x,5.025,(floor+ceiling)/2],[.025,.018,ceiling-floor],[60,90],{'source':'RGB thin vertical panel joints'},material='joint',collider=False)
for z in [floor+2.25,floor+4.35]:add('wall_joint_h_'+str(z),'trim',[-6,5.022,z],[15,.018,.022],[60,90],{'source':'RGB horizontal panel joints'},material='joint',collider=False)
# Main furniture. Source-specific conflicting measurements remain in metadata. Objects
# at floor level use the consensus support plane; this changes hidden bottoms only.
def semantic(oid,c,s,frames=None,**kw):
 ob=ann.get(oid,{});measure=ob.get('measurements',[]);fs=frames or [r['frame'] for r in measure]
 prov={'source':'direct supplied depth in hand-marked RGB box','measurement_log':'depth_semantic_measurements.json','object_measurements':measure,'selection_rule':kw.pop('selection_rule','native measured visible medians; coherent solid dimensions rounded; ground contact regularized to consensus floor'),'conflicting_input_preserved':len(measure)>1}
 add(oid,ob.get('category',kw.pop('category','prop')),c,s,fs,prov,attributes=ob.get('attributes',{}),**kw)
semantic('reception',[-20.6,.7,floor+.72],[1.3,4.5,1.44],selection_rule='near frame126 primary; initial frame5 measurement retained as conflict')
semantic('planter_center_left',[-12.65,-1.45,floor+.47],[1.0,2.25,.94],foliage_height=1.1,selection_rule='near frame90/126 depth x about -13.3/-12.2; frame5 depth -8 retained as conflict')
semantic('planter_center_right',[-12.65,1.55,floor+.47],[1.0,2.25,.94],foliage_height=1.1,selection_rule='near frame90/126 depths; left/right reverse under reverse-facing camera90')
semantic('table_middle',[-9.35,-.1,floor+.28],[1.6,1.6,.56],selection_rule='RGB relation between seats and near-view planter row; frame5 visible depth conflicts with near-view row; x weakly regularized using RGB+pose triangulation')
seat_layout=[('seat_middle_left_front',[-8.8,-1.35],1.12,'lounge_chair'),('seat_middle_left_back',[-10.5,-1.05],1.0,'lounge_chair'),('seat_middle_center',[-10.6,.05],1.4,'ottoman'),('seat_middle_right_front',[-9.8,.95],1.05,'ottoman'),('seat_middle_right_back',[-10.3,1.8],1.1,'lounge_chair')]
for oid,xy,dia,kind in seat_layout:
 h=.88 if kind=='lounge_chair' else .53;semantic(oid,[*xy,floor+h/2],[dia,dia,h],yaw=math.atan2(-.1-xy[1],-9.35-xy[0]),selection_rule='RGB relations to the locally measured central planter row and supplied-pose triangulation; individual frame5 depth remains in evidence; disagreement means low confidence',confidence='low')
semantic('table_front',[-3.59,.58,floor+.28],[1.6,1.6,.56])
for oid,xy,dia,kind in [('seat_front_left',[-4.1,1.72],.98,'ottoman'),('seat_front_center',[-3.18,1.88],1.1,'lounge_chair'),('seat_front_right',[-2.19,1.62],1.08,'lounge_chair')]:
 h=.90 if kind=='lounge_chair' else .55;semantic(oid,[*xy,floor+h/2],[dia,dia,h],yaw=math.atan2(.58-xy[1],-3.59-xy[0]))
semantic('planter_window_mid',[-9.96,-2.82,floor+.4],[1.25,1.25,.8],foliage_height=.95,selection_rule='near frame126 centroid; frame5 position -5.98 retained as conflict')
semantic('planter_mirror',[-6.9,4.16,floor+.52],[.8,.8,1.04],foliage_height=.65,selection_rule='near frame60 centroid; frame5 position retained as conflict')
semantic('planter_front_tall',[-1.15,2.3,floor+.65],[.62,.7,1.3],foliage_height=1.4)
semantic('planter_back_left',[-22.06,-1.95,floor+.48],[.68,.68,.96],foliage_height=1.2,selection_rule='near frame126 centroid; frame5 measurement retained as conflict')
semantic('planter_back_right',[-22.06,3.0,floor+.48],[.68,.68,.96],foliage_height=1.2,selection_rule='RGB bilateral reception relationship; initial measured y2.0 and nearest left planter x; low-confidence unobserved base',confidence='low')
semantic('planter_back_corner',[-22.0,6.3,floor+.32],[1.0,1.0,.64],foliage_height=.6,selection_rule='frame5 position conflicts strongly; near reception relative layout from RGB only; low confidence',confidence='low')
# Circular mirror arrangement visible on near wall, measured in frame60.
for j,(x,z,r) in enumerate([(-5.3,.2,.82),(-3.5,-.25,.72),(-2.2,.75,.61),(-3.2,1.52,.42),(-4.5,1.05,.35),(-6.65,1.12,.35),(-6.9,.12,.24),(-6.5,-.65,.34),(-4.65,-.83,.22),(-1.95,-.65,.29)]):
 add('round_mirror_%02d'%j,'mirror',[x,5.017,z],[r*2,.035,r*2],[60,72,90],{'source':'RGB arrangement plus measured mirror-wall plane; reflected depth excluded as nonphysical surface'},collider=False)
for j,x in enumerate([-2,-5,-8,-11,-14,-17,-20,-23]):
 for k,y in enumerate([-2.6,1.0,3.6]):
  if (j+k)%5==0:continue
  add(f'pendant_{j}_{k}','pendant_light',[x+(k%2)*.55,y,ceiling-.48-(j%3)*.16],[1.25+(j%2)*.3,1.25+(j%2)*.3,.28],[5,60,90,105,126],{'source':'observed multiple staggered circular suspended shades; spatial pattern approximate from RGB; height follows depth ceiling','uncertainty':'individual shade correspondence is weak'},collider=False,confidence='low')
for j,xy in enumerate([[-20.3,5.7],[-17.2,6.7]]):add('floor_lamp_'+str(j),'floor_lamp',[*xy,floor+1.4],[.55,.55,2.8],[5,90],{'source':'observed tall white floor lamps near far-side wall; approximate native metric placement'},collider_size=[.25,.25,2.8])
# RGB-observed dark longitudinal ceiling strips are modular slats, not inferred obstacles.
for j,x in enumerate(np.arange(-23.5,1.0,.34)):
 for k,y in enumerate([-3.25,3.50]):
  add(f'ceiling_slat_{j}_{k}','trim',[float(x),y,ceiling-.075],[.085,2.05,.15],[5,60,90,105,126],{'source':'direct RGB dark parallel ceiling slats; spacing regularized in measured ceiling frame'},material='joint',collider=False)
for j,y in enumerate(np.arange(-4.5,8.1,1.4)):
 add('end_wall_joint_'+str(j),'trim',[-23.46,float(y),(floor+ceiling)/2],[.025,.025,ceiling-floor],[5,126],{'source':'RGB end-wall vertical panels'},material='joint',collider=False)
for j,z in enumerate([floor+2.35,floor+4.40]):
 add('end_wall_joint_h_'+str(j),'trim',[-23.45,1.65,z],[.025,13.0,.025],[5,126],{'source':'RGB end-wall horizontal panel joints'},material='joint',collider=False)
# The white central wall emblem is observed, while fine design is deliberately simplified.
add('reception_wall_emblem','wall_panel',[-23.44,.5,floor+3.1],[.045,.62,.93],[5,126],{'source':'RGB white sculptural shield/emblem above desk; simplified rectangular silhouette'},material='stone',collider=False,confidence='low')
plan={'revision':2,'packet_path':str(packet),'packet_sha256':hashlib.sha256(open(packet,'rb').read()).hexdigest(),'T_input_model':np.eye(4).tolist(),'units':'m','floor_z':floor,'ceiling_z':ceiling,'room_center':[-11.4,.3,0.5],'window_light_location':[-11.4,-4.3,1.2],'objects':objs,'render_frames':[5,60,90,105,126], 'unresolved':['Supplied native depth has substantial time-dependent scale inconsistency relative to fixed metric poses. No rescaling applied.','One coherent support floor cannot follow all supplied measurements: measured modes span -3.056 to -1.708 m.','Far continuation of mirror wall omitted because extrapolation crosses supplied camera path; unobserved closure is not fabricated.','Central furniture dimensions and correspondence remain uncertain across conflicting views; low-confidence semantic regularization is explicit.','Reflective mirrors/glazing do not provide trustworthy physical depth.']}
from review_fixes import apply_review_fixes
plan=apply_review_fixes(plan)
json.dump(plan,open(OUT/'geometry_plan.json','w'),indent=2)
print('objects',len(plan['objects']),'floor',floor,'ceiling',ceiling)
