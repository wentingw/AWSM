"""Check frozen G1 requests, identity and logged kinematics independently of batch counts."""
from pathlib import Path
import csv,hashlib,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];REV=Path(__file__).resolve().parent
BASE=ROOT/'experiments/tasks/g1_M4/replay_20260924'
def read(p):return json.loads(p.read_text())
def yaw(q):
 w,x,y,z=q;return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
def wrap(x):return (x+math.pi)%(2*math.pi)-math.pi
protocol=read(BASE/'execution_protocol.json');expected={r['episode_id']:r['expected_target_id'] for r in read(ROOT/'results/evaluation/tasks/g1_M4_20260924/expected_targets.json')}
records=[]
for r in protocol['requests']:
 req=ROOT/r['request'];folder=req.parent;s=read(folder/'summary.json');q=read(req)
 assert s['scene_method']=='M4' and q['episode_id']==r['episode_id']
 assert not any('expected' in k or 'target_id' in k for k in q)
 a=np.genfromtxt(folder/'trajectory_full.csv',delimiter=',',names=True);b=np.genfromtxt(folder/'trajectory.csv',delimiter=',',names=True)
 pos=np.array([a[k][-1] for k in ['qpos_0','qpos_1','qpos_2']]);quat=np.array([a[f'qpos_{i}'][-1] for i in range(3,7)])
 path=float(np.hypot(np.diff(a['qpos_0']),np.diff(a['qpos_1'])).sum());assert abs(path-s['path_length_m'])<1e-8
 terminal_delta=s['simulated_seconds']-float(a['time_s'][-1]);assert 0<=terminal_delta<.051
 goal=np.array(s['planned_goal']);target=np.array(s['target']['center']);d=target[:2]-pos[:2];bearing=abs(wrap(math.atan2(d[1],d[0])-yaw(quat)))*180/math.pi
 err=float(np.linalg.norm(pos[:2]-goal[:2]));assert abs(np.linalg.norm(np.array(s['final_position'])[:2]-goal[:2])-s['final_goal_distance_m'])<1e-9
 correct=s['target_id']==expected[r['episode_id']]
 assert np.all(b['obstacle_contact']==0) if s['obstacle_contact_steps']==0 else True
 nav=s['status']=='success' and s['obstacle_contact_steps']==0 and not s['fallen'] and err<.30 and bearing<15
 records.append({'episode_id':r['episode_id'],'instruction':q['instruction'],'selected_target':s['target_id'],'expected_target':expected[r['episode_id']],'correct_identity':correct,'navigation_verified':bool(nav),'logged_final_approach_error_m':err,'logged_final_bearing_deg':bearing,'simulated_seconds':s['simulated_seconds'],'path_length_m':path,'last_state_before_stop_s':terminal_delta,'reported_full_rate_obstacle_contacts':s['obstacle_contacts'],'sampled_contact_rows':int(b['obstacle_contact'].sum()),'summary_sha256':hashlib.sha256((folder/'summary.json').read_bytes()).hexdigest(),'trajectory_full_sha256':hashlib.sha256((folder/'trajectory_full.csv').read_bytes()).hexdigest()})
report={'status':'pass','episodes':records,'counts':{'episodes':len(records),'correct_target_identity':sum(r['correct_identity'] for r in records),'navigation_verified':sum(r['navigation_verified'] for r in records)},'means':{k:float(np.mean([r[k] for r in records])) for k in ['logged_final_approach_error_m','logged_final_bearing_deg','simulated_seconds','path_length_m']},'scope':'Identity checked against evaluator-only intended targets; kinematics recalculated from 20 Hz recorded qpos. Full-rate contact/fall/dwell outcomes are runner logs, corroborated where possible by sampled trajectory, not a fresh physics replay.'}
(REV/'independent_g1_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='episodes'},indent=2))
