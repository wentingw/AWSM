import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import json,hashlib,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
from scipy.optimize import least_squares
R=Path(__file__).resolve().parent
I=R.parent.parent/'inputs/M1'
P=json.loads((I/'packet.json').read_text())
K=np.array(P['intrinsics']); H=4.6
# Explicit semantic image correspondences, manually picked in original 1280x960 RGB.
pts={
 'north_glass_floor':[0,16,0],'north_glass_ceiling':[0,16,H], 'north_right_floor':[8,16,0],'north_right_ceiling':[8,16,H],
 'south_glass_floor':[0,0,0],'south_glass_ceiling':[0,0,H], 'south_right_floor':[8,0,0],'south_right_ceiling':[8,0,H],
 'north_door_near_floor':[0,12.0,0],'north_door_far_floor':[0,13.8,0], 'north_door_near_top':[0,12.0,2.6],'north_door_far_top':[0,13.8,2.6],
 'south_door_near_floor':[0,2.2,0],'south_door_far_floor':[0,4.0,0], 'south_door_near_top':[0,2.2,2.6],'south_door_far_top':[0,4.0,2.6],
 'mirror_door_north_bottom':[6.8,10.7,0],'mirror_door_south_bottom':[6.8,9.45,0],'mirror_door_north_top':[6.8,10.7,2.6],'mirror_door_south_top':[6.8,9.45,2.6],
 'mirror_main':[6.76,7.65,2.15],'mirror_second':[6.76,6.22,1.55],
 'desk_left':[2.55,15.12,.95],'desk_right':[5.65,15.12,.95],
 'column_floor':[.62,8.0,0],'column_ceiling':[.62,8.0,H],
}
obs={
33:{'north_glass_floor':[424,474],'north_glass_ceiling':[419,224],'north_right_floor':[946,487],'north_right_ceiling':[944,227],'north_door_near_floor':[349,514],'north_door_far_floor':[394,488],'north_door_near_top':[344,315],'north_door_far_top':[392,325],'desk_left':[542,437],'desk_right':[691,438]},
61:{'mirror_door_north_bottom':[368,548],'mirror_door_south_bottom':[447,564],'mirror_door_north_top':[366,343],'mirror_door_south_top':[444,345],'mirror_main':[746,420],'mirror_second':[916,486]},
74:{'mirror_door_north_bottom':[417,610],'mirror_door_south_bottom':[549,596],'mirror_door_north_top':[390,333],'mirror_door_south_top':[546,324],'mirror_main':[866,392],'mirror_second':[993,432]},
82:{'mirror_door_north_bottom':[549,678],'mirror_door_south_bottom':[621,650],'mirror_door_north_top':[549,473],'mirror_door_south_top':[621,473],'mirror_main':[788,509],'mirror_second':[851,536]},
91:{'south_glass_floor':[750,350],'south_glass_ceiling':[770,82],'south_right_floor':[349,355],'south_right_ceiling':[349,60]},
100:{'north_door_near_floor':[920,530],'north_door_far_floor':[1005,540],'north_door_near_top':[923,280],'north_door_far_top':[1026,276],'south_door_near_floor':[263,472],'south_door_far_floor':[347,490],'south_door_near_top':[256,297],'south_door_far_top':[334,293],'column_floor':[505,520],'column_ceiling':[482,80]},
108:{'north_door_near_floor':[706,562],'north_door_far_floor':[862,555],'north_door_near_top':[706,318],'north_door_far_top':[871,319],'north_glass_floor':[1081,548],'north_glass_ceiling':[1090,146]},
118:{'north_door_near_floor':[644,585],'north_door_far_floor':[793,550],'north_door_near_top':[643,274],'north_door_far_top':[800,287],'north_glass_floor':[946,517],'north_glass_ceiling':[1008,104]},
129:{'north_glass_floor':[751,574],'north_glass_ceiling':[753,306],'north_right_floor':[1275,629],'north_right_ceiling':[1275,272],'north_door_near_floor':[592,666],'north_door_far_floor':[650,627],'north_door_near_top':[588,409],'north_door_far_top':[649,413],'desk_left':[840,549],'desk_right':[1049,561]},
155:{'north_glass_floor':[460,439],'north_glass_ceiling':[459,188],'north_right_floor':[977,455],'north_right_ceiling':[982,179],'north_door_near_floor':[375,479],'north_door_far_floor':[417,455],'north_door_near_top':[369,281],'north_door_far_top':[414,291],'desk_left':[574,405],'desk_right':[723,405]}
}
def look(c,t):
 z=np.array(t)-c; z=z/np.linalg.norm(z);x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x);y=np.cross(z,x);return np.column_stack([x,y,z])
init={33:([4.8,3.3,2.5],[3.7,16,1.9]),61:([2.5,6.5,2.55],[6.8,7,1.9]),74:([3.3,10.8,2.75],[6.8,8.8,1.7]),82:([3.5,13.1,2.7],[6.8,7,2.3]),91:([3.8,13,2.6],[3.8,0,1.7]),100:([6.5,9.5,2.6],[0,8.5,2]),108:([6,11.2,2.65],[0,12.5,2]),118:([4,9.5,2.6],[0,13,1.8]),129:([1.8,6.5,2.5],[4.2,16,1.8]),155:([4.4,2.2,2.5],[4,16,1.8])}
cams={};measure=[]
for i,o in obs.items():
 world=np.array([pts[n] for n in o]); image=np.array(list(o.values()));c,t=init[i];c=np.array(c,float);r=Rotation.from_matrix(look(c,t)).as_rotvec();p0=np.r_[r,c]
 def err(p,regularize=True):
  rot=Rotation.from_rotvec(p[:3]).as_matrix();q=(world-p[3:])@rot;uv=q[:,:2]/np.maximum(q[:,2:],.1);uv=uv*762.8+[640,480];e=(uv-image).ravel()
  if regularize:e=np.r_[e,(p[3:]-c)*[10,10,45],max(0,.5-q[:,2].min())*100]
  return e
 sol=least_squares(err,p0,loss='soft_l1',f_scale=12,max_nfev=1000,bounds=([-10,-10,-10,.25,.5,1.5],[10,10,10,7.7,15.5,3.2]))
 rot=Rotation.from_rotvec(sol.x[:3]).as_matrix();T=np.eye(4);T[:3,:3]=rot;T[:3,3]=sol.x[3:];cams[i]=T
 residual=err(sol.x,False).reshape(-1,2)
 measure.append({'sample_index':i,'method':'manual semantic landmark reprojection fit, assumed common architecture','landmarks':[{'id':n,'world_xyz_assumed_m':pts[n],'pixel_uv':o[n],'residual_uv_pixels':r.tolist()} for n,r in zip(o,residual)],'rms_pixels':float(np.sqrt(np.mean(residual**2))),'camera_position':sol.x[3:].tolist(),'valid':False,'reason':'manual fit is conditional on assumed geometry; no independent pose validation'})
 print(i,np.round(sol.x[3:],2),'rms',round(measure[-1]['rms_pixels'],2))
# Entire sequence manually bracketed against contact sheets, with fixed fit anchors.
anchors={0:cams[33].copy(),33:cams[33],41:cams[33].copy(),61:cams[61],74:cams[74],82:cams[82],91:cams[91],100:cams[100],108:cams[108],118:cams[118],129:cams[129],145:cams[155].copy(),155:cams[155],179:cams[33].copy()}
anchors[0][:3,3]+=[-.5,-1,0];anchors[41][:3,3]+=[.15,.4,0];anchors[145][:3,3]+=[0,1,0];anchors[179][:3,3]+=[-.6,-.8,.05]
keys=sorted(anchors);slerp=Slerp(keys,Rotation.from_matrix(np.array([anchors[k][:3,:3] for k in keys])))
frames=[]
for f in P['frames']:
 i=f['sample_index'];T=np.eye(4);T[:3,:3]=slerp(i).as_matrix();T[:3,3]=[np.interp(i,keys,[anchors[k][a,3] for k in keys]) for a in range(3)]
 frames.append({k:f[k] for k in ['sample_index','source_index','timestamp_ns','intrinsics']}|{'camera_to_world':T.tolist(),'valid':False,'confidence':{'level':'low','pose_reliability':'unvalidated conditional estimate','method':'manual RGB semantic fit' if i in cams else 'interpolation between manually inferred RGB trajectory anchors'},'estimated':True})
def save(n,d):(R/n).write_text(json.dumps(d,indent=2)+'\n')
save('cameras.json',{'frames':frames,'coordinate_frame':'model','pose_convention':'OpenCV RDF camera-to-world','scale_assumption':'north/south glazed doorway height 2.6 m; no measured metric reference'})
save('analysis/measurements.json',{'metric_status':'assumed scale, RGB-only','intrinsics':P['intrinsics'],'scale_anchor':{'object':'glazed doors','assumed_height_m':2.6,'uncertainty_m':.35,'provenance':'inferred conventional architectural scale'},'room_dimensions_m':[8,16,4.6],'world_points':pts,'observations':measure,'conflicts':['Room and door dimensions are inferred jointly; low pixel residual does not establish metric accuracy.','Mirror appearances are reflections, not duplicated scene objects.','Camera motion between keyframes is interpolated and may not match source trajectory.']})
save('analysis/camera_checks.json',{'calibration':'K public 1280x960; fx=fy=762.8; center640,480; Blender conversion right multiply diag(1,-1,-1,1)','all180_attempted':True,'validated_pose_count':0,'check_pose_estimates':measure,'reference_depth':'N/A: M1 RGB-only','render_projection_validation':'will be asserted by generic paired checker'})
save('layout.json',{'version':1,'coordinate_system':'Z up; X glass-to-solid wall; Y south-to-reception','units':'metres, assumed RGB-only scale','room':{'width':8,'length':16,'height':4.6},'mirror_wall':{'x':6.8,'y_min':3.5,'y_max':11.0,'recess_wall_x':8},'seating_groups':[{'id':'north','center':[3.0,10.5],'facing_y':-1},{'id':'south','center':[3.8,3.3],'facing_y':1}], 'planter_dividers_y':[12.4,5.7], 'reception':{'center':[4.1,15.15,.55],'dimensions':[3.2,.85,1.1]},'provenance':'fresh visual interpretation of all180 RGB; no external geometry or cameras'})
save('modelling_manifest.json',{'method_id':'M1','model_id':'gpt-6-astra','status':'building_initial_candidate','model_from_input':None,'geometry_scale':'assumed metric scale anchored to2.6m door; not measured','revisions':1,'checking_render_count':0,'input_bvh_pass_count':0,'input_packet_sha256':hashlib.sha256((I/'packet.json').read_bytes()).hexdigest(),'unresolved_issues':['Metric scale ambiguous in RGB-only input.','All180 poses estimated; no independently validated camera.','Sparse manual correspondences constrain architecture; object depths inferred.'],'quality_status':'LIMITED'})
