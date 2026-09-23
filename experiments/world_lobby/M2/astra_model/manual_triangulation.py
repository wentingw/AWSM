"""Reproduce hand-inspected RGB correspondences; never rescale pose geometry."""
import json,cv2,numpy as np
from pathlib import Path
O=Path(__file__).parent;packet=json.load(open(O.parents[3]/'data/packets/M2/packet.json'));g=json.load(open(O/'geometry_analysis.json'));T=np.array(g.get('initial_near_depth_transform',g['T_input_model']));m=json.load(open(O/'manual_measurements.json'));Ps=[]
for i in m['frames']:
 a=np.load(packet['frames'][i]['geometry']);Ps.append(a['intrinsics']@np.linalg.inv(T@a['camera_to_world'])[:3])
for item in m['manual_correspondences'].values():
 a,b=np.array(item['points_1000x750'])*1.28;h=cv2.triangulatePoints(*Ps,a[:,None],b[:,None])[:,0];q=h[:3]/h[3];item['model_position']=q.tolist();item['initial_position']=q.tolist();item['reprojection_error']=[]
 for P,w in zip(Ps,[a,b]):z=P@np.r_[q,1];item['reprojection_error'].append(float(np.linalg.norm(z[:2]/z[2]-w)))
json.dump(m,open(O/'manual_measurements.json','w'),indent=2)
