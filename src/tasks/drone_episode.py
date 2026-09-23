"""Image-only selected target -> collision route -> quadrotor dynamics.

Reads retrieval rankings containing only reconstructed candidate poses, never
GT target positions. State estimation is a declared simulator-state oracle.
"""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.tasks.navigation import astar,inflate_boxes
from src.tasks.scene_io import load_scene,floor_and_obstacles,bounds_of,navigation_constraints
from src.tasks.drone_dynamics import simulate

def main():
 p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--request',type=Path,required=True);p.add_argument('--retrieval',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--video',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);request=json.loads(a.request.read_text());ranking=json.loads(a.retrieval.read_text());objects,colliders=load_scene(a.scene);floor,obstacles=floor_and_obstacles(colliders,request.get('floor_z'));unknown,known_bounds=navigation_constraints(a.scene);boxes=inflate_boxes([bounds_of(c) for c in obstacles+unknown],.45);start=np.asarray(request['start_xyz']);allbounds=np.array([o['bounds'] for o in objects]);bounds=np.array([allbounds[:,0].min(0),allbounds[:,1].max(0)]);bounds=np.asarray(known_bounds) if known_bounds is not None else bounds;bounds[0,2]=max(bounds[0,2],floor+.35);records=[];t=time.monotonic();picked=None
 for c in ranking['ranking'][:5]:
  C=np.array(c['camera_to_world']);plan=astar(start,C[:3,3],boxes,bounds,resolution=.25,max_expansions=100000);records.append({'view_id':c['view_id'],'retrieval_score':c['score'],'plan_status':plan['status'],'expanded':plan.get('expanded',0)})
  if plan['status']=='success':picked=(c,C,plan);break
 report={'task':'drone reference-image search and rephotography','request':request,'retrieval_path':str(a.retrieval),'candidate_attempts':records,'planning_seconds':time.monotonic()-t,'query_pose_input':False,'GT_access':False,'localization':'simulator-state-oracle','status':'planning_failed'}
 if picked:
  c,C,plan=picked;forward=C[:3,2];heading=float(np.arctan2(forward[1],forward[0]));result=simulate(plan['path'],obstacles,floor,heading,a.out,video=a.video);final=C.copy();final[:3,3]=result['final_position'];report.update(status=result['status'],selected_view_id=c['view_id'],plan=plan,dynamics=result,final_camera_to_model=final.tolist(),camera_refinement_iterations=0,limitations=['coarse DINO retrieval; no continuous image refinement in this first-stage result','ideal stabilized gimbal','reconstructed conservative box collision world','no GT-world physical transfer tested here'])
  (a.out/'final_camera.json').write_text(json.dumps({'camera_to_world':final.tolist(),'intrinsics':[381.4,381.4,320,240],'resolution_wh':[640,480]},indent=2)+'\n')
 (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('plan','request')}))
if __name__=='__main__':main()
