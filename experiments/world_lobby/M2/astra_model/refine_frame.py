import json,numpy as np
from pathlib import Path
O=Path(__file__).parent;g=json.load(open(O/'geometry_analysis.json'));old=np.array(g.get('initial_near_depth_transform',g['T_input_model']));slope=(1.045-.003)/(15.882-3.125);intercept=-.003+slope*3.125;ang=np.arctan(slope);c=np.cos(ang);s=np.sin(ang);A=np.eye(4);A[:3,:3]=[[1,0,0],[0,c,-s],[0,s,c]];A[2,3]=-intercept*c;T=A@old
g['initial_near_depth_transform']=old.tolist();g['T_input_model']=T.tolist();g['floor_normalization_refinement']={'reason':'Long-baseline RGB triangulation showed local ViPE depth plane normal biased: far floor ~1.04 below initial plane and ceiling fell similarly. Fit longitudinal floor direction between frame0 near floor and manually triangulated frames0/130 rear window-floor corner. Rigid rotation only.','slope_old_z_per_y':-slope,'intercept_old_z':intercept,'old_to_final':A.tolist(),'uncertainty_m':.22};json.dump(g,open(O/'geometry_analysis.json','w'),indent=2)
a=np.load(O/'measurements_input.npz');np.savez_compressed(O/'measurements_model.npz',points=a['points']@T[:3,:3].T+T[:3,3],colors=a['colors'],frame_ids=a['frame_ids'])
a=np.load(O/'triangulated_measurements.npz');np.savez_compressed(O/'triangulated_measurements_final.npz',points=a['points']@A[:3,:3].T+A[:3,3],colors=a['colors'],frame_pairs=a['frame_pairs'],reprojection_error=a['reprojection_error']);cs=json.load(open(O/'cameras_input.json'));cs['T_input_model']=T.tolist();cs['coordinate_frame']='Z-up via exact rigid floor normalization, scale=1'
for cam in cs['cameras']:cam['c2w_model']=(T@np.array(cam['c2w_input'])).tolist()
json.dump(cs,open(O/'cameras.json','w'),indent=2)
m=json.load(open(O/'manual_measurements.json'))
for item in m['manual_correspondences'].values():item['initial_position']=item.get('initial_position',item['model_position']);item['model_position']=(A[:3,:3]@item['initial_position']+A[:3,3]).tolist()
json.dump(m,open(O/'manual_measurements.json','w'),indent=2);print('T',T.tolist());print({k:np.round(v['model_position'],3).tolist() for k,v in m['manual_correspondences'].items()})
