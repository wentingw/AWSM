from repair_measure import *
import copy,math
old=copy.deepcopy(L);changes=[];measurements=[]
def change(obj,param,before,after,obs,reason,kind='inferred with RGB constraints'):
 ev=[]
 for i,u,v in obs:
  ev.append(dict(sample_index=i,pixel_uv_1280=[u,v],v1_signed_depth=residual(i,u,v)))
 changes.append(dict(object_id=obj,parameter=param,before=before,after=after,evidence=ev,rationale=reason,provenance=kind))
def lamp_fit(id,obs,radius_px):
 pt,e=triang(obs);measurements.append(dict(object_id=id,observations=obs,world_diffuser_center=pt.tolist(),reprojection_errors_px=e,own_DA3_world=[own_depth(*o) for o in obs]))
 # Radius from rim width measured in first observation, source center is bottom diffuser.
 i,u,v=obs[0];z=project(pt,i)[1];rad=radius_px*z/762.8
 return dict(id=id,center=pt.tolist(),radius=round(rad,3),evidence_frames=[o[0] for o in obs],observations=obs,reprojection_errors_px=e,provenance='Multi-view RGB diffuser-center triangulation; hand picks and correspondence uncertain; rim radius from projected width, thickness/weave inferred')
features={
0:([(33,359,73),(129,256,126)],110),1:([(33,462,153),(129,538,211)],71),2:([(33,441,210),(129,588,287)],57),3:([(33,554,217),(129,793,292)],58),4:([(33,635,239),(129,874,275)],54),5:([(33,738,240),(129,1061,269)],66),6:([(33,697,188),(129,910,212)],53),7:([(33,790,174),(129,678,135)],89),9:([(33,809,245),(129,1170,274)],41),10:([(33,528,280),(129,830,359)],35),11:([(33,594,259),(129,878,331)],34),12:([(33,619,293),(129,936,364)],31),13:([(33,661,268),(129,982,329)],33),14:([(33,734,287),(129,1126,348)],35)}
for j,(obs,radpx) in features.items():
 d=lamp_fit(f'pendant_{j:02d}',obs,radpx);before=L['pendants'][j];L['pendants'][j]=d
 change(d['id'],'center,radius',{k:before[k] for k in ['center','radius']},{k:d[k] for k in ['center','radius']},obs,'Replace single-view assumed height by two-view diffuser correspondence; >5px fits remain approximate','measured approximate')
# Well identified missing mirror pendant, matched across FOUR views.
obs=[(61,579,125),(74,891,79),(82,823,334),(91,316,119)]
d=lamp_fit('pendant_15',obs,113);L['pendants'].append(d);change(d['id'],'added',None,d,obs,'Missing fixture is consistent across four camera rays','measured approximate')
# West cluster: measured DA3 backprojection with RGB validation in opposite-facing82/91.
# These additional identities are uncertain, so mark inferred, not triangulated.
west=[(91,446,60,95),(91,463,85,64),(91,511,113,51),(91,579,112,45),(91,631,98,54),(91,681,64,53)]
for j,(i,u,v,rpx) in enumerate(west,16):
 pt=np.array(own_depth(i,u,v));pt[2]=float(np.clip(pt[2],3.55,4.45));z=project(pt,i)[1];rad=min(.82,max(.35,rpx*z/762.8));obs=[(i,u,v)];uv,zz=project(pt,82)
 if zz>0 and 0<=uv[0]<1280 and 0<=uv[1]<960:obs.append((82,float(uv[0]),float(uv[1])))
 d=dict(id=f'pendant_{j:02d}',center=pt.tolist(),radius=rad,evidence_frames=[91,82,100],provenance='Inferred west fixture identity; DA3 anchor from91 (NPZ K), plausible height bounds;82 projection is diagnostic, NOT an independent point correspondence')
 L['pendants'].append(d);measurements.append(dict(object_id=d['id'],observations=[west[j-16]],world_anchor=pt.tolist(),projected_82=uv.tolist(),uncertain=True));change(d['id'],'added',None,d,obs,'Fill observed west cluster; exact identities/radii uncertain. Projection82 is a diagnostic region only.')
# Furniture re-fit uses plane-constrained tops, approximate correspondence and nonpenetration.
seatdata={
'seat_A_0':([15.90,23.23,.32],.40,0,False,[(33,445,620),(129,325,820)]),
'seat_A_1':([16.69,23.24,.32],.37,-1.57,True,[(33,461,595),(129,414,768)]),
'seat_A_2':([17.16,22.57,.32],.37,0,True,[(33,539,578),(129,510,754)]),
'seat_A_3':([17.75,21.96,.32],.44,0,False,[(33,593,559),(129,635,755)]),
'seat_A_4':([17.05,20.99,.32],.39,-1.0,True,[(33,691,575),(129,738,840),(74,576,889)]),
'seat_A_5':([17.02,21.79,.32],.36,0,False,[(33,622,574),(129,650,790)]),
'seat_B_0':([13.46,20.61,.32],.38,0,False,[(61,762,695),(155,890,800)]),
'seat_B_1':([12.70,20.70,.32],.38,1.57,True,[(61,901,728),(155,906,855)]),
'seat_B_2':([12.05,21.14,.32],.38,-1.57,True,[(61,1033,786),(155,987,945)]),
'seat_B_3':([11.80,22.02,.32],.43,0,False,[(61,1144,938),(91,567,347)])}
for d in L['chairs']:
 b=copy.deepcopy(d);c,r,rot,back,obs=seatdata[d['id']];d.update(center=c,radius=r,rotation=rot,back=back,evidence_frames=sorted(set(o[0] for o in obs)),provenance='Plane-constrained RGB tops, own DA3 diagnostic; centres/radii jointly regularized for solid clearance. Ambiguous top correspondences and rotations inferred.')
 change(d['id'],'center,radius,rotation,back',{k:b[k] for k in ['center','radius','rotation','back']},{k:d[k] for k in ['center','radius','rotation','back']},obs,'Separate solid upholstery and table; source top correspondences imperfect, so constrained estimate not exact measurement')
for d in L['tables']:
 if d['id']=='side_table_B':continue
 b=copy.deepcopy(d);obs=[(33,575,618),(129,480,859)] if d['id']=='coffee_table_A' else [(61,824,856),(155,655,849)]
 d['center']=[16.02,21.95,.40] if d['id']=='coffee_table_A' else [12.97,21.90,.40];d['radii']=[.53,.43] if d['id']=='coffee_table_A' else [.60,.48]
 change(d['id'],'center,radii',b,d,obs,'Source top-height/backprojection uncertain; maintain separation from upholstery and original visual oval form')
# Explicit construction parameters used by the scene builder.
L['repair_construction']={'wall_panel_x_sign':{'west_end_wall':1,'feature_return_east':1},'chair_back_bevel':.02,'chair_foot_bottom':.011,'table_foot_bottom':.011,'desk_support_bottom':.011,'door_frame_width':.13,'floor_grid_pitch':.085,'floor_grid_fill':[.040,.031],'shrub_branches':75,'shrub_reach':[.10,.42],'shrub_leaf_length':.07,'shrub_leaf_half_width':.005,'shrub_height_above_pot':[.30,.80],'mirror_fern_radius':.40,'mirror_fern_top':1.22,'ambient_strength':.16,'daylight_energy':650,'exposure':0,'pendant_weave_surface':'underside','door_state':'closed, leaf colliders separated from static frame; clear aperture when leaves disabled','corridor_extent':'inferred recess only, terminates at y16.25; not claimed as known connected route'}
for obj,param,b,a,obs,why in [
('west_end_wall','panel_offset_x',-.09,.0975,[(91,540,240),(100,40,270)],'Expose panels on room-facing +X surface'),('feature_return_east','panel_offset_x',-.09,.0975,[(74,170,260),(82,445,400)],'Expose panels on +X surface'),('all_chair_backs','end_cap_winding/bevel',{'same_end_winding':True,'bevel':.06},{'outward_consistent':True,'bevel':.02},[(61,905,715),(74,576,830),(129,733,817)],'Fix independently audited inconsistent winding and degenerate bevel'),('reception_desk','shell_winding/support',{'signed_volume':-2.073760054,'bottom':.09},{'outward':True,'support_bottom':.011,'support_top':.11},[(33,620,459),(129,951,587)],'Reverse shell faces; inferred hidden plinth connects floor to underside'),('all_seats_tables','feet_bottom',{'seat':.02672,'table':.03813},.011,[(61,760,792),(129,450,920)],'Inferred hidden foot pads meet inlay top'),('shrubs','procedural_dimensions',{'branches':100,'reach':[.15,.65],'leaf_length':.14,'leaf_half_width':.015,'height':[.35,1]},L['repair_construction'],[(82,655,710),(91,437,425),(108,240,700),(118,530,830)],'Narrow leaves and reduce canopy spread; local negative signed errors and broad RGB silhouette'),('mirror_fern','canopy',{'spiky_radius':.62,'top':1.4},{'rounded_radius':.40,'top':1.22},[(61,518,502),(74,691,516)],'Fine rounded source silhouette, retain measured pot position'),('entries','frame_width',.085,.13,[(100,912,415),(108,778,442),(118,728,412)],'Source shows broad dark bronze members; inferred gauge'),('dark_inlay','surface_grid',None,{'pitch':.085,'fill':[.040,.031]},[(91,650,800),(100,830,750),(108,815,730)],'Persistent regular floor pattern distinct from view-dependent round fixture reflections; inferred metallic inlay texture, no depth displacement')]:change(obj,param,b,a,obs,why)
L['version']=2;L['inference_notes'].append('Revision construction parameters and every changed layout field documented in analysis/repair_changes_v2.json. Native cameras/scale unchanged.')
json.dump(L,open(R/'layout.json','w'),indent=2);json.dump({'method':'RGB triangulation/plane intersections and own DA3; no additional render','measurements':measurements},open(R/'analysis/repair_measurements_v2.json','w'),indent=2);json.dump({'from_version':1,'to_version':2,'signed_residual_convention':'model minus own DA3, metres; diagnostic ROIs are not masks','changes':changes},open(R/'analysis/repair_changes_v2.json','w'),indent=2)
print('Wrote',len(changes),'changes',len(measurements),'measurements')
