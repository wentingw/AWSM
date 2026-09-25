"""Offline M4 endpoint evaluation; query target pose is never passed to planner."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from PIL import Image,ImageDraw,ImageFont
from skimage.metrics import structural_similarity
ROOT=Path(__file__).resolve().parents[1]; batch=ROOT/'experiments/tasks/drone_M4/replay_20260924'; out=ROOT/'results/evaluation/tasks/drone_M4_20260924'; out.mkdir(parents=True,exist_ok=True)
truth={x['query_id']:x for x in json.loads((ROOT/'results/evaluation/tasks/photographic_reference_truth_private.json').read_text())}; T=np.asarray(json.loads((ROOT/'results/M4/render_manifest.json').read_text())['T_gt_model']); assert np.allclose(T,np.eye(4)); rows=[]
for ep in sorted(batch.glob('episode_*')):
 d=json.loads((ep/'summary.json').read_text()); q=d['request']['query_id']; r={'query_id':q,'flight_status':d['status'],'strict_rephotography_success':False,'relaxed_rephotography_success':False}
 if 'final_camera_to_model' in d:
  C=T@np.asarray(d['final_camera_to_model']); t=np.asarray(truth[q]['camera_tum']); R=Rotation.from_quat(t[4:8]).as_matrix(); te=float(np.linalg.norm(C[:3,3]-t[1:4])); re=float(np.degrees(Rotation.from_matrix(C[:3,:3].T@R).magnitude())); r.update(translation_error_m=te,rotation_error_deg=re,selected_view_id=d['selected_view_id'],candidate_arrival_error_m=d['dynamics']['goal_error_m'],simulated_seconds=d['dynamics']['simulated_seconds'],contact_steps=d['dynamics']['collision_steps'],strict_rephotography_success=d['status']=='success' and te<=.1 and re<=5,relaxed_rephotography_success=d['status']=='success' and te<=.25 and re<=10)
  p=ep/'final_rgb.png'
  if p.exists():
   target=np.asarray(Image.open(d['request']['reference_rgb']).convert('RGB').resize((640,480),Image.Resampling.LANCZOS)); pred=np.asarray(Image.open(p).convert('RGB')); mse=float(np.mean(((pred.astype(float)-target)/255)**2)); r['psnr_db']=float(-10*np.log10(max(mse,1e-12))); r['ssim']=float(structural_similarity(target,pred,data_range=255,channel_axis=2))
 rows.append(r)
counts={'episodes':len(rows),'collision_free_candidate_arrivals':sum(r['flight_status']=='success' for r in rows),'collisions':sum(r['flight_status']=='collision' for r in rows),'planning_failed':sum(r['flight_status']=='planning_failed' for r in rows),'strict_rephotography_successes':sum(r['strict_rephotography_success'] for r in rows),'relaxed_rephotography_successes':sum(r['relaxed_rephotography_success'] for r in rows)}
result={'condition':'20 original mapping photographs; M4 frozen scene; target poses withheld during execution','model':'M4','scene_blend_sha256':hashlib.sha256((ROOT/'experiments/world_lobby/M4/astra_model/scene.blend').read_bytes()).hexdigest(),'packet_sha256':hashlib.sha256((ROOT/'data/packets/M4/packet.json').read_bytes()).hexdigest(),'success_definition':{'strict':'collision-free, position <=0.10m and rotation <=5deg','relaxed':'collision-free, position <=0.25m and rotation <=10deg'},'counts':counts,'means':{k:float(np.mean([r[k] for r in rows if k in r])) for k in ['translation_error_m','rotation_error_deg','psnr_db','ssim'] if any(k in r for r in rows)},'episodes':rows,'limitations':['DINOv2 coarse retrieval over 30 M4 renders, top5 reachable candidates','no continuous image-based refinement','simulator self-state oracle','ideal stabilized gimbal','conservative reconstructed collision boxes','query poses used only after execution for evaluation','known-scene input views, not held-out generalization']}
result['source_hashes']={key:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for key,path in {'scene_blend':'experiments/world_lobby/M4/astra_model/scene.blend','m4_packet':'data/packets/M4/packet.json','m4_modelling_manifest':'experiments/world_lobby/M4/astra_model/modelling_manifest.json','query_protocol':'experiments/tasks/frozen_inputs/photographic_mapping_queries/protocol.json','cache_manifest':'experiments/tasks/drone_M4/view_cache/manifest.json'}.items()}
result['artifacts']={'batch_dir':str(batch.relative_to(ROOT)),'video':'assets/m4_tasks/drone_episode.mp4','video_query_id':13,'reference_endpoint_figure':'figures/m4_tasks/drone_comparison.jpg','endpoint_rgb_dir':'results/evaluation/tasks/drone_M4_20260924/endpoint_rgb'}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n'); (out/'README.md').write_text('# M4 drone photographic replay (2026-09-24)\n\nIndependent M4 frozen-scene run. Query poses are evaluator-only. See `report.json`.\n')
print(json.dumps({'counts':counts,'means':result['means']},indent=2))
