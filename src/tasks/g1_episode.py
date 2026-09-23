#!/usr/bin/env python3
"""G1 in a reconstructed scene's declared box collision layer.

Uses true MuJoCo articulated dynamics and the official CPU locomotion policy.
Localization is simulator-state-oracle. Language grounding is a constrained
category/attribute/near parser, explicitly not an open-vocabulary LLM benchmark.
No ground-truth scene, goal coordinates, or target labels are read.
"""
import argparse,csv,json,math,sys,time,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import mujoco,torch,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.tasks.navigation import astar,query_scene,inside
from src.tasks.scene_io import load_scene,floor_and_obstacles,planning_boxes,bounds_of,navigation_constraints
from src.tasks.g1_smoke import gravity_orientation
ROOT=Path(__file__).resolve().parents[2]

def yaw(q):
    w,x,y,z=q;return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
def wrap(x):return (x+math.pi)%(2*math.pi)-math.pi

def make_model(asset_root,obstacles,floor_z,out,visual_scene=None):
    robot=asset_root/'resources/robots/g1_description'
    tree=ET.parse(robot/'g1_12dof.xml');root=tree.getroot();root.find('compiler').set('meshdir',str(robot/'meshes'))
    visual=root.find('visual')
    if visual is None:visual=ET.SubElement(root,'visual')
    ET.SubElement(visual,'global',{'offwidth':'960','offheight':'720'})
    if visual_scene is not None:
        asset=root.find('asset')
        ET.SubElement(asset,'mesh',{'name':'m3_visual_mesh','file':str(Path(visual_scene).resolve())})
    body=root.find('worldbody')
    ET.SubElement(body,'light',{'pos':'0 0 12','dir':'0 0 -1','directional':'true','diffuse':'0.8 0.8 0.8'})
    ET.SubElement(body,'geom',{'name':'world_floor','type':'plane','pos':f'0 0 {floor_z}','size':'0 0 .05','rgba':'.75 .75 .71 1','friction':'.9 .02 .002'})
    for i,c in enumerate(obstacles):
        b=bounds_of(c);center=b.mean(0);size=np.maximum((b[1]-b[0])/2,.005)
        ET.SubElement(body,'geom',{'name':f'world_obstacle_{i}','type':'box','pos':' '.join(map(str,center)),'size':' '.join(map(str,size)),'rgba':'.40 .48 .45 .12','friction':'.8 .02 .002'})
    if visual_scene is not None:
        ET.SubElement(body,'geom',{'name':'m3_visual_only','type':'mesh','mesh':'m3_visual_mesh','contype':'0','conaffinity':'0','group':'2','rgba':'1 1 1 1'})
    path=out/'episode_world.xml';tree.write(path);return mujoco.MjModel.from_xml_path(str(path))

def plan_approach(start,target,boxes,objects,floor_z,known_bounds=None):
    allb=np.array([o['bounds'] for o in objects]);bounds=np.array([allb[:,0].min(0),allb[:,1].max(0)]);bounds[:,2]=[floor_z+.8,floor_z+.8]
    if known_bounds is not None:bounds[:,:2]=known_bounds[:,:2]
    center=np.asarray(target['center'],float);b=bounds_of(target);half=(b[1,:2]-b[0,:2])/2
    candidates=[]
    for theta in np.linspace(-np.pi,np.pi,24,endpoint=False):
        direction=np.array([np.cos(theta),np.sin(theta)])
        edge=min([half[k]/abs(direction[k]) for k in range(2) if abs(direction[k])>1e-6])
        point=np.r_[center[:2]+direction*(edge+.7),floor_z+.8]
        if inside(point,boxes):continue
        candidates.append(point)
    candidates.sort(key=lambda p:np.linalg.norm(p-start))
    for goal in candidates:
        p=astar(start,goal,boxes,bounds,resolution=.2,planar=True,max_expansions=80000)
        if p['status']=='success':return p,goal
    return {'status':'no_reachable_approach','path':[]},None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scene',type=Path,required=True);ap.add_argument('--request',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--floor-z',type=float);ap.add_argument('--seconds',type=float,default=90);ap.add_argument('--video',action='store_true');ap.add_argument('--visual-scene',type=Path);a=ap.parse_args()
    torch.set_num_threads(1);out=a.out.resolve();assert out.is_relative_to(ROOT/'experiments');out.mkdir(parents=True,exist_ok=True)
    request=json.loads(a.request.read_text());objects,colliders=load_scene(a.scene);floor_z,obstacles=floor_and_obstacles(colliders,a.floor_z);unknown,known_bounds=navigation_constraints(a.scene);boxes=planning_boxes(obstacles+unknown,floor_z,radius=.47)
    query=query_scene(request['instruction'],objects)
    base={'task':'G1 language-goal navigation','scene':str(a.scene.resolve()),'instruction':request['instruction'],'query':query,'localization':'simulator-state-oracle','geometry':'frozen reconstructed conservative AABB collision layer','language_scope':'constrained English category/attribute/near queries','robot':'official Unitree G1 12DOF CPU policy','goal_pose_supplied':False,'GT_access':False,'status':'running'}
    if query['status']!='matched':base['status']='grounding_failed';(out/'summary.json').write_text(json.dumps(base,indent=2));return
    target=next(o for o in objects if o['object_id']==query['candidates'][0]['object_id']);start=np.array([*request['start_xy'],floor_z+.8]);t=time.monotonic();plan,goal=plan_approach(start,target,boxes,objects,floor_z,known_bounds);base.update(target_id=target['object_id'],plan=plan,planning_seconds=time.monotonic()-t)
    if goal is None:base['status']='planning_failed';(out/'summary.json').write_text(json.dumps(base,indent=2));return
    assets=ROOT/'runtime/unitree_rl_gym';cfg=yaml.safe_load((assets/'deploy/deploy_mujoco/configs/g1.yaml').read_text());model=make_model(assets,obstacles,floor_z,out,a.visual_scene);data=mujoco.MjData(model)
    mujoco.mj_resetData(model,data);data.qpos[:3]=start;ang=float(request.get('start_yaw',0));data.qpos[3:7]=[np.cos(ang/2),0,0,np.sin(ang/2)];default=np.asarray(cfg['default_angles'],np.float32);data.qpos[7:19]=default;mujoco.mj_forward(model,data)
    policy=torch.jit.load(str(assets/'deploy/pre_train/g1/motion.pt'),map_location='cpu').eval();dt=cfg['simulation_dt'];dec=cfg['control_decimation'];model.opt.timestep=dt
    kp=np.array(cfg['kps']);kd=np.array(cfg['kds']);action=np.zeros(12,np.float32);target_q=default.copy();obs=np.zeros(47,np.float32);path=np.array(plan['path']);wp=1;rows=[];full_rows=[];fell=False;obstacle_contacts=0;contact_steps=0;arrived_at=None;stationary_since=None
    renderer=None;writer=None
    if a.video:
        import cv2
        renderer=mujoco.Renderer(model,height=480,width=640);cam=mujoco.MjvCamera();cam.distance=2.5;cam.azimuth=0;cam.elevation=-15
        writer=cv2.VideoWriter(str(out/'episode.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),20,(640,480))
    for i in range(int(a.seconds/dt)):
        data.ctrl[:]=(target_q-data.qpos[7:19])*kp-data.qvel[6:18]*kd;mujoco.mj_step(model,data);tt=(i+1)*dt
        if i%dec==0:
            xy=data.qpos[:2];heading=yaw(data.qpos[3:7])
            while wp<len(path)-1 and np.linalg.norm(xy-path[wp,:2])<.25:wp+=1
            delta=path[wp,:2]-xy;dist=np.linalg.norm(delta);desired=math.atan2(delta[1],delta[0]);err=wrap(desired-heading)
            cmd=np.array([min(.45,.8*dist)*max(0,math.cos(err)),0,np.clip(1.4*err,-.65,.65)],np.float32)
            if tt<1.5:cmd[:]=0
            close=np.linalg.norm(xy-goal[:2])<.3
            if close:
                target_delta=np.asarray(target['center'])[:2]-xy;end_err=wrap(math.atan2(target_delta[1],target_delta[0])-heading);cmd=np.array([0,0,np.clip(end_err,-.4,.4)],np.float32)
                if abs(end_err)<np.deg2rad(15):
                    if stationary_since is None:stationary_since=tt
                    if tt-stationary_since>=1.5:arrived_at=tt
                else:stationary_since=None
            else:stationary_since=None
            obs[:3]=data.qvel[3:6]*cfg['ang_vel_scale'];obs[3:6]=gravity_orientation(data.qpos[3:7]);obs[6:9]=cmd*np.asarray(cfg['cmd_scale']);obs[9:21]=(data.qpos[7:19]-default)*cfg['dof_pos_scale'];obs[21:33]=data.qvel[6:18]*cfg['dof_vel_scale'];obs[33:45]=action;phase=tt%.8/.8;obs[45:47]=[np.sin(2*np.pi*phase),np.cos(2*np.pi*phase)]
            with torch.no_grad():action=policy(torch.from_numpy(obs)[None]).numpy().reshape(-1).astype(np.float32)
            target_q=action*cfg['action_scale']+default
        collided=False
        for contact in data.contact:
            names=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or '' for g in (contact.geom1,contact.geom2)]
            if any(n.startswith('world_obstacle_') for n in names):obstacle_contacts+=1;collided=True
        contact_steps+=int(collided)
        tilt=np.linalg.norm(gravity_orientation(data.qpos[3:7])[:2]);fell=data.qpos[2]<floor_z+.45 or tilt>.75
        if i%max(1,int(.05/dt))==0:
            rows.append([tt,*data.qpos[:7],*data.qvel[:3],int(collided)]);full_rows.append([tt,*data.qpos.tolist(),*data.qvel.tolist()])
            if renderer:
                cam.lookat[:]=data.qpos[:3];cam.azimuth=0;cam.elevation=-15;cam.distance=2.5;renderer.update_scene(data,camera=cam);writer.write(renderer.render()[:,:,::-1])
        if fell or arrived_at:break
    if renderer:renderer.close();writer.release()
    arr=np.array(rows);distance=float(np.linalg.norm(np.diff(arr[:,1:3],axis=0),axis=1).sum()) if len(arr)>1 else 0
    with (out/'trajectory.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['time_s','x','y','z','qw','qx','qy','qz','vx','vy','vz','obstacle_contact']);w.writerows(rows)
    with (out/'trajectory_full.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['time_s']+[f'qpos_{i}' for i in range(model.nq)]+[f'qvel_{i}' for i in range(model.nv)]);w.writerows(full_rows)
    base.update(status='success' if arrived_at and not contact_steps and not fell else 'fall' if fell else 'collision' if contact_steps else 'timeout',arrived_at_s=arrived_at,simulated_seconds=tt,final_position=data.qpos[:3].tolist(),final_goal_distance_m=float(np.linalg.norm(data.qpos[:2]-goal[:2])),path_length_m=distance,obstacle_contact_steps=contact_steps,obstacle_contacts=obstacle_contacts,fallen=bool(fell),planned_goal=goal.tolist(),target=target,limitations=['constrained language matching','simulator-state-oracle localization','conservative AABB world, not original triangle mesh','collision materials assumed, not measured','no GT-world transfer in this result'])
    (out/'summary.json').write_text(json.dumps(base,indent=2)+'\n');print(json.dumps({k:v for k,v in base.items() if k not in ('plan','target','query')}))
if __name__=='__main__':main()
