"""Independent post-execution validation; never imported by retrieval or control."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image
from skimage.metrics import structural_similarity
ROOT=Path(__file__).resolve().parents[2];REV=Path(__file__).resolve().parent
BATCH=ROOT/'experiments/tasks/drone_M4/replay_20260924'
TRUTH=ROOT/'results/evaluation/tasks/photographic_reference_truth_private.json'
truth={r['query_id']:r for r in json.loads(TRUTH.read_text())}
T=np.array(json.loads((ROOT/'results/M4/render_manifest.json').read_text())['T_gt_model'])
assert np.allclose(T,np.eye(4)), 'Revisit M4 coordinate conventions before evaluation'
rows=[]
for i in range(20):
 ep=BATCH/f'episode_{i:02d}';d=json.loads((ep/'summary.json').read_text())
 assert d['request']['query_id']==i and d['query_pose_input'] is False and d['GT_access'] is False
 row={'query_id':i,'flight_status':d['status'],'strict_rephotography_success':False,'relaxed_rephotography_success':False}
 if 'final_camera_to_model' in d:
  C=T@np.asarray(d['final_camera_to_model']);target=np.asarray(truth[i]['camera_tum']);R=Rotation.from_quat(target[4:8]).as_matrix()
  translation=float(np.linalg.norm(C[:3,3]-target[1:4]));angle=float(np.degrees(Rotation.from_matrix(C[:3,:3].T@R).magnitude()))
  contacts=d['dynamics']['collision_steps'];arrived=d['status']=='success'
  assert not arrived or contacts==0
  row.update(translation_error_m=translation,rotation_error_deg=angle,contact_steps=contacts,strict_rephotography_success=arrived and translation<=.10 and angle<=5,relaxed_rephotography_success=arrived and translation<=.25 and angle<=10)
  path=np.loadtxt(ep/'drone_trajectory.csv',delimiter=',',skiprows=1)
  residual=float(np.linalg.norm(path[-1,1:4]-C[:3,3]));assert residual<.05,(i,residual)
  row['final_camera_vs_last_logged_position_m']=residual
  a=np.asarray(Image.open(ep/'final_rgb.png').convert('RGB'),dtype=np.float64)/255
  b=np.asarray(Image.open(d['request']['reference_rgb']).convert('RGB').resize((640,480),Image.Resampling.LANCZOS),dtype=np.float64)/255
  assert a.shape==b.shape==(480,640,3)
  mse=float(np.mean((a-b)**2));row['psnr_db']=float(-10*np.log10(max(mse,1e-12)));row['ssim']=float(structural_similarity(a,b,data_range=1,channel_axis=2))
 rows.append(row)
counts={'episodes':len(rows),'collision_free_candidate_arrivals':sum(r['flight_status']=='success' for r in rows),'collisions':sum(r['flight_status']=='collision' for r in rows),'planning_failed':sum(r['flight_status']=='planning_failed' for r in rows),'strict_rephotography_successes':sum(r['strict_rephotography_success'] for r in rows),'relaxed_rephotography_successes':sum(r['relaxed_rephotography_success'] for r in rows)}
report={'status':'pass','scope':'Independent post-execution recalculation; not a controller input','registration':T.tolist(),'counts':counts,'means':{k:float(np.mean([r[k] for r in rows if k in r])) for k in ['translation_error_m','rotation_error_deg','psnr_db','ssim']},'episodes':rows,'truth_sha256':hashlib.sha256(TRUTH.read_bytes()).hexdigest()}
(REV/'independent_drone_check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counts':counts,'means':report['means']},indent=2))
