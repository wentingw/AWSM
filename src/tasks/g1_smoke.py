#!/usr/bin/env python3
"""Headless CPU smoke for the official Unitree G1 12-DOF locomotion policy."""
import argparse, csv, json, time
from pathlib import Path
import mujoco
import numpy as np
import torch
import yaml

def gravity_orientation(quat_wxyz):
    qw,qx,qy,qz = quat_wxyz
    return np.array([2*(-qz*qx+qw*qy), -2*(qz*qy+qw*qx), 1-2*(qw*qw+qz*qz)], dtype=np.float32)

def run_segment(model, policy, cfg, name, command, seconds, dt, decimation, seed=0):
    data = mujoco.MjData(model); mujoco.mj_resetData(model, data)
    default = np.asarray(cfg['default_angles'], np.float32); kp=np.asarray(cfg['kps'],np.float32); kd=np.asarray(cfg['kds'],np.float32)
    action=np.zeros(12,np.float32); target=default.copy(); obs=np.zeros(47,np.float32); cmd=np.asarray(command,np.float32)
    rows=[]; fallen_at=None; steps=int(round(seconds/dt)); model.opt.timestep=dt
    for i in range(steps):
        qj=data.qpos[7:19]; dq=data.qvel[6:18]
        data.ctrl[:] = (target-qj)*kp - dq*kd
        mujoco.mj_step(model,data)
        if (i+1)%decimation==0:
            qj=(data.qpos[7:19]-default); dq=data.qvel[6:18]
            obs[:3]=data.qvel[3:6]*cfg['ang_vel_scale']; obs[3:6]=gravity_orientation(data.qpos[3:7])
            obs[6:9]=cmd*np.asarray(cfg['cmd_scale'],np.float32); obs[9:21]=qj*cfg['dof_pos_scale']; obs[21:33]=dq*cfg['dof_vel_scale']; obs[33:45]=action
            phase=((i+1)*dt)%0.8/0.8; obs[45:47]=[np.sin(2*np.pi*phase),np.cos(2*np.pi*phase)]
            with torch.no_grad(): action=policy(torch.from_numpy(obs).unsqueeze(0)).cpu().numpy().reshape(-1).astype(np.float32)
            target=action*cfg['action_scale']+default
        z=float(data.qpos[2]); tilt=float(np.linalg.norm(gravity_orientation(data.qpos[3:7])[:2])); speed=float(np.linalg.norm(data.qvel[:3]));
        if fallen_at is None and (z < 0.45 or tilt > 0.75): fallen_at=(i+1)*dt
        if i % max(1,int(0.1/dt)) == 0: rows.append([i*dt,z,tilt,speed,float(data.qvel[0]),float(data.qvel[1]),float(data.qvel[5])])
    arr=np.asarray(rows); return {'name':name,'command':list(map(float,command)),'seconds':seconds,'fallen_at_s':fallen_at,'final_base_z_m':float(data.qpos[2]),'final_tilt_proxy':float(np.linalg.norm(gravity_orientation(data.qpos[3:7])[:2])),'max_speed_mps':float(arr[:,3].max()),'final_velocity_mps':arr[-1,4:7].tolist(),'samples':int(len(arr))}, arr

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--seconds',type=float,default=10); a=ap.parse_args()
    torch.set_num_threads(1); root=a.root.resolve(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    with (root/'deploy/deploy_mujoco/configs/g1.yaml').open() as f: cfg=yaml.safe_load(f)
    cfg['policy_path']=str(root/'deploy/pre_train/g1/motion.pt'); cfg['xml_path']=str(root/'resources/robots/g1_description/scene.xml')
    model=mujoco.MjModel.from_xml_path(cfg['xml_path']); policy=torch.jit.load(cfg['policy_path'],map_location='cpu').eval()
    tests=[('standing',[0,0,0]),('forward',[0.5,0,0]),('yaw',[0,0,0.25])]; results=[]
    for name,cmd in tests:
        result,arr=run_segment(model,policy,cfg,name,cmd,a.seconds,cfg['simulation_dt'],cfg['control_decimation']); results.append(result)
        with (out/(name+'.csv')).open('w',newline='') as f:
            w=csv.writer(f); w.writerow(['time_s','base_z_m','tilt_proxy','speed_mps','vx_mps','vy_mps','yaw_rate_rps']); w.writerows(arr)
    report={'status':'completed','robot':'Unitree G1 12DOF','policy':'official deploy/pre_train/g1/motion.pt','physics':'MuJoCo headless CPU','tests':results,'interface':{'command_xyz_yaw':["vx","vy","yaw_rate"],'future_goal_hook':'set command from language-navigation planner; no teleportation'},'limitations':['flat scene only','no World Lobby scene attached','tilt_proxy is gravity-vector horizontal norm','policy is official locomotion policy, not language navigation']}
    (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
