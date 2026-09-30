"""Manual RGB landmark projection fit. No automated features or external pose/depth models."""
import json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation,Slerp
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M1'
packet=json.loads((I/'packet.json').read_text());K=np.array(packet['intrinsics'])
# Landmarks are drawn from authored approximate geometry; fitting is conditional on that geometry.
P={'shield':(3.60,17.8,2.14),'desk_front':(3.65,16.15,.95),'tree_L':(1.75,17.2,1.61),'tree_R':(5.55,17.2,1.61),'seat_N1':(2.35,9.2,.575),'table_N':(3.40,9.1,.515),'planter_L':(2.52,11.415,.87),'planter_R':(4.78,11.415,.87),'column_base':(.60,10.6,0),'grass_N':(.65,9.50,.37),'urn_N':(6.77,9,.4),'mirror_big':(7.22,8.9,2.19),'mirror_smalltop':(7.22,10.04,2.88),'south_pot_L':(2.40,1.2,.9),'south_pot_R':(5.80,1.2,.9),'table_S':(4.35,6.45,.51),'south_corner':(0,0,0),'south_walltop':(0,0,5.2)}
obs={
0:{'shield':[845,340],'desk_front':[835,402],'tree_L':[722,360],'tree_R':[968,365],'seat_N1':[668,583],'table_N':[798,592],'planter_L':[750,486],'planter_R':[956,499],'grass_N':[496,562]},
45:{'shield':[479,421],'desk_front':[482,490],'tree_L':[357,451],'tree_R':[590,450],'seat_N1':[398,683],'table_N':[527,674],'planter_L':[441,575],'planter_R':[623,558],'grass_N':[142,688],'urn_N':[973,641],'mirror_smalltop':[1110,465],'column_base':[179,614]},
135:{'shield':[738,333],'desk_front':[716,400],'tree_L':[616,356],'tree_R':[860,362],'seat_N1':[290,584],'table_N':[422,600],'planter_L':[495,489],'planter_R':[694,514],'grass_N':[176,550],'urn_N':[1000,700],'mirror_smalltop':[1226,445],'column_base':[238,554]},
179:{'shield':[640,362],'desk_front':[635,428],'tree_L':[525,384],'tree_R':[751,384],'seat_N1':[440,605],'table_N':[569,608],'planter_L':[537,506],'planter_R':[729,505],'grass_N':[266,589],'urn_N':[1080,618],'mirror_smalltop':[1272,418],'table_S':[664,928],'column_base':[283,523]},
90:{'planter_L':[684,496],'planter_R':[438,495],'table_S':[560,401],'south_pot_L':[664,370],'south_pot_R':[483,369],'mirror_big':[291,334],'column_base':[904,528]}
}
# Pose parameters: xyz, horizontal heading toward +y, downward pitch, roll.
def c2w(p):
 x,y,z,yaw,down,roll=p
 f=np.array([math.sin(yaw)*math.cos(down),math.cos(yaw)*math.cos(down),-math.sin(down)])
 right=np.array([math.cos(yaw),-math.sin(yaw),0]);up=np.cross(right,f);up/=np.linalg.norm(up)
 rr=right*math.cos(roll)+up*math.sin(roll);uu=-right*math.sin(roll)+up*math.cos(roll)
 T=np.eye(4);T[:3,:3]=np.stack([rr,-uu,f],axis=1);T[:3,3]=[x,y,z];return T

def project(points,p):
 T=c2w(p);q=(np.array(points)-T[:3,3])@T[:3,:3];v=q@K.T;return v[:,:2]/v[:,2:]
initial={0:[3.0,4.5,2.7,-.24,.20,-.01],45:[3.6,4.8,2.7,.22,.06,.00],135:[5.3,5.8,2.8,-.25,.23,.015],179:[3.6,4,2.5,0,.18,0],90:[3.8,16.,2.7,math.pi,.24,.02]}
anchors={};checks=[]
for i,O in obs.items():
 keys=list(O);pts=np.array([P[k] for k in keys]);uv=np.array(list(O.values()));p0=np.array(initial[i])
 def residual(p):return np.r_[(project(pts,p)-uv).ravel(),(p[2]-2.65)*10,p[5]*20]
 fit=least_squares(residual,p0,bounds=([-5,-3,1.5,-10,-.6,-.3],[12,17.65,4.,10,.7,.3]),loss='soft_l1',f_scale=10,max_nfev=1000)
 p=fit.x;pr=project(pts,p);errors=np.linalg.norm(pr-uv,axis=1)
 anchors[i]=c2w(p)
 checks.append({'sample_index':i,'pose_parameters':p.tolist(),'confidence':'low','valid_for_check_render':True,'valid_for_metric_camera_evaluation':False,'method':'Manual semantic landmark pixel picking and nonlinear projection fit against assumed model geometry','landmarks':[{'name':k,'world_point':P[k],'pixel_observed':O[k],'pixel_projected':pr[j].tolist(),'residual_pixels':float(errors[j]),'pixel_pick_uncertainty':8} for j,k in enumerate(keys)],'median_residual_pixels':float(np.median(errors)),'rms_residual_pixels':float(np.sqrt(np.mean(errors**2)))})
# Extra poses describe the visible sweep. They are interpolation scaffolding, explicitly invalid.
for i,p in {12:[3.7,4.5,2.6,.11,.14,0],35:[3.7,4.7,2.6,.13,.14,0],62:[3.2,6.1,2.8,1.43,.31,.005],80:[2.5,12.6,2.6,1.73,-.01,.00],104:[5.9,13.1,2.8,-1.57,.17,0],118:[3.8,11.0,2.7,-.76,.16,.03],150:[3.6,4.1,2.6,.01,.2,0]}.items():anchors[i]=c2w(p)
times=sorted(anchors);rots=Rotation.from_matrix([anchors[i][:3,:3] for i in times]);slerp=Slerp(times,rots)
frames=[]
for f in packet['frames']:
 i=f['sample_index'];T=np.eye(4);T[:3,:3]=slerp(i).as_matrix()
 for a in range(3):T[a,3]=np.interp(i,times,[anchors[t][a,3] for t in times])
 fixed=i in obs
 frames.append({'sample_index':i,'source_index':f['source_index'],'timestamp_ns':f['timestamp_ns'],'camera_to_world':T.tolist(),'intrinsics':packet['intrinsics'],'valid':False,'check_render_usable':fixed,'confidence':'low' if fixed else 'very_low','pose_provenance':'manual RGB landmarks conditional on approximate geometry' if fixed else 'manual sweep anchor or interpolated illustrative pose; not measured'})
(R/'cameras.json').write_text(json.dumps({'frames':frames,'coordinate_frame':'model','pose_convention':'OpenCV RDF camera-to-world','metric_scale_observable':False,'validity_note':'All poses are invalid for metric evaluation. Five fixed samples have manually fitted illustrative poses for image checks; fitting is conditional on assumed geometry.'},indent=2))
(R/'analysis/camera_checks.json').write_text(json.dumps({'checks':checks,'units':'pixels in original 1280x960 RGB','validation':'input agreement only, not GT accuracy; landmarks and model are jointly inferred','render_convention':'OpenCV camera_to_world right multiplied by diag(1,-1,-1,1)'},indent=2))
(R/'analysis/measurements.json').write_text(json.dumps({'method':'Manual object and architecture ratios in calibrated RGB images; no geometry/depth/trajectory inputs','assumed_dimensions':[{'quantity':'typical round lounge cushion diameter','value_m':.8,'uncertainty_m':.2,'evidence':[0,45,62,90,135,179]},{'quantity':'internal door height','value_m':2.05,'uncertainty_m':.35,'evidence':[45,62,80]},{'quantity':'ceiling height','value_m':5.2,'uncertainty_m':1.2,'evidence':[0,45,90,104,135,179]},{'quantity':'room length','value_m':18.,'uncertainty_m':4.,'evidence':[0,45,90,135,179]},{'quantity':'room width main zone','value_m':7.35,'uncertainty_m':1.5,'evidence':[62,80,90,104]}],'conflicts':['Furniture modular offsets and projected sizes cannot all be aligned by a single rigid camera; inferred geometry and camera errors are coupled.','Exact chandelier count and longitudinal spacing are uncertain due to repeated forms and occlusion.','Door scale and chair scale are assumed priors, not independent physical measurements.'],'global_scale':'unobservable; any uniform rescaling of all objects and camera translations preserves projection','manually_picked_landmarks':P},indent=2))
print(json.dumps([{k:c[k] for k in ['sample_index','pose_parameters','median_residual_pixels','rms_residual_pixels']} for c in checks],indent=2))
