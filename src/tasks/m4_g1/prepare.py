"""Freeze 5 distinct language goals × 4 model-derived initial locations."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.tasks.scene_io import load_scene,bounds_of,floor_and_obstacles,planning_boxes
from src.tasks.navigation import inside
from src.tasks.m4_g1.language import query_scene
SCENE=ROOT/'experiments/world_lobby/M4/astra_model';OUT=ROOT/'experiments/tasks/g1_M4/replay_20260924';EVAL=ROOT/'results/evaluation/tasks/g1_M4_20260924'
# Evaluator-only intended instances were independently identified from M4 metadata.
GOALS=[('找到浅灰色陶瓷盆中长着低矮绿植的花盆，走过去面对它。','ceramic_plant_0'),('找到北侧长着金黄色花枝的长方形花盆，走过去面对它。','flower_planter_0'),('找到南侧长着金黄色花枝的长方形花盆，走过去面对它。','flower_planter_1'),('找到北侧种着鹤望兰的花盆，走过去面对它。','tropical_front_1'),('找到南侧种着鹤望兰的花盆，走过去面对它。','tropical_front_0')]
def main():
 OUT.mkdir(parents=True,exist_ok=True);EVAL.mkdir(parents=True,exist_ok=True)
 objects,colliders=load_scene(SCENE);floors=[c for c in colliders if c.get('role')=='floor'];_,obstacles=floor_and_obstacles(colliders);boxes=planning_boxes(obstacles,.041,radius=.47)
 bounds=bounds_of(next(c for c in floors if c['object_id']=='floor_stone'));packet=json.loads((ROOT/'data/packets/M4/packet.json').read_text());spawns=[]
 for f in packet['frames'][::3]:
  C=np.load(f['geometry'])['camera_to_world'];xy=C[:2,3]
  if np.any(xy<bounds[0,:2]+.6) or np.any(xy>bounds[1,:2]-.6):continue
  supporting=[bounds_of(c)[1,2] for c in floors if np.all(xy>=bounds_of(c)[0,:2]) and np.all(xy<=bounds_of(c)[1,:2])]
  if not supporting:continue
  z=float(max(supporting))
  if inside(np.r_[xy,z+.8],boxes) or any(np.linalg.norm(xy-np.array(s['start_xy']))<2 for s in spawns):continue
  spawns.append({'start_xy':xy.tolist(),'floor_z':z,'start_yaw':0.0,'source_mapping_frame':f['keyframe_index']})
  if len(spawns)==4:break
 assert len(spawns)==4,spawns
 requests=[];expected=[]
 for g,(text,target) in enumerate(GOALS):
  grounded=query_scene(text,objects);assert grounded['status']=='matched' and grounded['candidates'][0]['object_id']==target,(text,grounded)
  for s,spawn in enumerate(spawns):
   i=g*4+s;request={'episode_id':i,'goal_family':g,'instruction':text,**spawn,'north_convention':'map +Y','goal_pose_supplied':False};ep=OUT/f'episode_{i:02d}';ep.mkdir(exist_ok=True);(ep/'request.json').write_text(json.dumps(request,indent=2,ensure_ascii=False)+'\n');requests.append({'episode_id':i,'request':str((ep/'request.json').relative_to(ROOT))});expected.append({'episode_id':i,'expected_target_id':target,'goal_family':g})
 protocol={'scene_method':'M4','episodes':20,'independent_target_instances':5,'initial_locations':4,'requests':requests,'spawns':spawns,'language_scope':'five Chinese attribute/direction instructions, each executed from four initial locations; north=map +Y','localization':'simulator-state-oracle','version':'fixed original M4 geometry; conservative AABB obstacles and two original floor slabs','success_criteria':{'navigation':'collision-free, upright, approach error <=0.30 m, target bearing <=15deg, dwell >=1.5s','visibility':'post-execution M4 mesh first-hit rays; target covers at least 0.1% of a 640x480 camera image','identity':'selected target matches evaluator-only intended instance'},'controller':{'policy':'official G1 12DOF motion.pt','physics':'MuJoCo','timeout_s':90,'planning_radius_m':.47},'frozen_source_hashes':{n:hashlib.sha256((SCENE/n).read_bytes()).hexdigest() for n in ['scene.blend','objects.json','colliders.json']},'expected_target_file_not_read_by_controller':True}
 (OUT/'execution_protocol.json').write_text(json.dumps(protocol,indent=2,ensure_ascii=False)+'\n');(EVAL/'expected_targets.json').write_text(json.dumps(expected,indent=2)+'\n');print(json.dumps({'spawns':spawns,'episodes':20},indent=2))
if __name__=='__main__':main()
