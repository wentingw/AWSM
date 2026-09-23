"""Frozen photographic queries -> DINO retrieval -> MuJoCo flight; no GT read."""
import sys,json,hashlib,subprocess,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import torch
from transformers import Dinov2Model
from src.tasks.image_retrieval import descriptor
from src.tasks.scene_io import load_scene,floor_and_obstacles,bounds_of,navigation_constraints
from src.tasks.navigation import inflate_boxes,inside

def main():
 scene=ROOT/'experiments/world_lobby/M3/astra_model';out=ROOT/'experiments/tasks/drone_M3/photographic_20';out.mkdir(parents=True,exist_ok=True)
 protocol=ROOT/'experiments/tasks/frozen_inputs/photographic_mapping_queries/protocol.json';p=json.loads(protocol.read_text());cache=ROOT/'experiments/tasks/drone_M3/view_cache/manifest.json';views=json.loads(cache.read_text())['views'];objects,colliders=load_scene(scene);floor,obstacles=floor_and_obstacles(colliders);unknown,bounds=navigation_constraints(scene);boxes=inflate_boxes([bounds_of(c) for c in obstacles+unknown],.45)
 packet=json.loads((ROOT/'data/packets/M3/packet.json').read_text());byid={f['keyframe_index']:f for f in packet['frames']};spawn=None
 for k in [12,30,60,90,120,150]:
  C=np.load(byid[k]['geometry'])['camera_to_world'];xyz=C[:3,3]
  supported=any(bounds_of(c)[0,0]<=xyz[0]<=bounds_of(c)[1,0] and bounds_of(c)[0,1]<=xyz[1]<=bounds_of(c)[1,1] and abs(bounds_of(c)[1,2]-floor)<.05 for c in colliders)
  if supported and not inside(xyz,boxes) and np.all(xyz>=bounds[0]) and np.all(xyz<=bounds[1]):spawn={'keyframe_index':k,'start_xyz':xyz.tolist(),'floor_z':floor};break
 if spawn is None:raise RuntimeError('No valid predefined spawn')
 (out/'execution_protocol.json').write_text(json.dumps({'source_protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),'spawn':spawn,'drone_inflation_m':.45,'candidate_topk':5,'no_query_pose_or_GT_access':True,'refinement':'none; coarse retrieval and ideal stabilized gimbal'},indent=2)+'\n')
 torch.set_num_threads(4);model=Dinov2Model.from_pretrained(str(ROOT/'runtime/visual_features/dinov2-small'),local_files_only=True).eval();hashes=[hashlib.sha256(Path(v['rgb']).read_bytes()).hexdigest() for v in views];feature_path=cache.parent/'dinov2_features.npz'
 if feature_path.exists():
  old=np.load(feature_path);assert old['image_sha256'].tolist()==hashes;features=old['features']
 else:
  features=np.array([descriptor(model,v['rgb']) for v in views]);np.savez_compressed(feature_path,features=features,image_sha256=np.array(hashes))
 weights=json.loads((ROOT/'runtime/visual_features/dinov2-small/provenance.json').read_text())['sha256']
 for q in p['drone']['references']:
  ep=out/f"episode_{q['query_id']:02d}";ep.mkdir(exist_ok=True);query=Path(q['reference_rgb']);assert hashlib.sha256(query.read_bytes()).hexdigest()==q['sha256'];scores=features@descriptor(model,query);order=np.argsort(-scores)
  ranking={'query_id':q['query_id'],'query_rgb':str(query),'query_rgb_sha256':q['sha256'],'model':'official facebook/dinov2-small','model_weight_sha256':weights,'query_pose_input':False,'GT_access':False,'ranking':[dict(view_id=views[i]['view_id'],score=float(scores[i]),rgb=views[i]['rgb'],camera_to_world=views[i]['camera_to_world']) for i in order]}
  (ep/'retrieval.json').write_text(json.dumps(ranking,indent=2)+'\n');(ep/'request.json').write_text(json.dumps(dict(query_id=q['query_id'],reference_rgb=str(query),**spawn),indent=2)+'\n')
  print('RETRIEVED',q['query_id'],ranking['ranking'][0]['view_id'],flush=True)
 del model
 reports=[]
 for q in p['drone']['references']:
  ep=out/f"episode_{q['query_id']:02d}"
  if not (ep/'summary.json').exists():
   with (ep/'run.log').open('w') as log:
    subprocess.run([str(ROOT/'.venv-tasks/bin/python'),'-m','src.tasks.drone_episode','--scene',str(scene),'--request',str(ep/'request.json'),'--retrieval',str(ep/'retrieval.json'),'--out',str(ep)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
  report=json.loads((ep/'summary.json').read_text());reports.append({'query_id':q['query_id'],'status':report['status'],'selected_view_id':report.get('selected_view_id'),'planning_seconds':report['planning_seconds'],'goal_error_m':report.get('dynamics',{}).get('goal_error_m')});print('EPISODE',reports[-1],flush=True)
 statuses={k:sum(r['status']==k for r in reports) for k in sorted({r['status'] for r in reports})};(out/'batch_summary.json').write_text(json.dumps({'condition':p['drone']['reference_condition'],'episodes':reports,'counts':statuses,'note':'success is flight arrival to retrieved candidate, not target photo pose success; separate evaluator required'},indent=2)+'\n');print('BATCH_COMPLETE',statuses,flush=True)
if __name__=='__main__':main()
