"""Small quadrotor with four thrust actuators and MuJoCo rigid-body dynamics."""
import math,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import mujoco
from .scene_io import bounds_of

def make_world(obstacles,floor_z):
 root=ET.Element('mujoco',{'model':'metric quadrotor world'});ET.SubElement(root,'option',{'timestep':'.004','gravity':'0 0 -9.81'});ET.SubElement(root,'visual');world=ET.SubElement(root,'worldbody')
 ET.SubElement(world,'light',{'pos':'0 0 12','dir':'0 0 -1','directional':'true'})
 ET.SubElement(world,'geom',{'name':'floor','type':'plane','pos':f'0 0 {floor_z}','size':'0 0 .1','rgba':'.75 .75 .70 1'})
 for i,c in enumerate(obstacles):
  b=bounds_of(c);ET.SubElement(world,'geom',{'name':f'obstacle_{i}','type':'box','pos':' '.join(map(str,b.mean(0))),'size':' '.join(map(str,np.maximum((b[1]-b[0])/2,.002))),'rgba':'.40 .49 .45 1'})
 body=ET.SubElement(world,'body',{'name':'quad','pos':'0 0 2'});ET.SubElement(body,'freejoint');ET.SubElement(body,'inertial',{'pos':'0 0 0','mass':'1','diaginertia':'.02 .02 .035'});ET.SubElement(body,'geom',{'name':'quad_body','type':'sphere','size':'.14','rgba':'.1 .2 .8 1'})
 rotors=np.array([[.18,.18,0],[-.18,.18,0],[-.18,-.18,0],[.18,-.18,0]]);signs=np.array([1,-1,1,-1]);act=ET.SubElement(root,'actuator')
 for i,xyz in enumerate(rotors):
  ET.SubElement(body,'geom',{'name':f'arm_{i}','type':'capsule','fromto':'0 0 0 '+' '.join(map(str,xyz)),'size':'.018','rgba':'.15 .15 .17 1'})
  ET.SubElement(body,'site',{'name':f'motor_{i}','pos':' '.join(map(str,xyz)),'size':'.04'})
  ET.SubElement(act,'general',{'name':f'thrust_{i}','site':f'motor_{i}','gear':f'0 0 1 0 0 {signs[i]*.02}','ctrllimited':'true','ctrlrange':'0 8'})
 xml=ET.tostring(root,encoding='unicode');allocation=np.vstack([np.ones(4),rotors[:,1],-rotors[:,0],signs*.02]);return mujoco.MjModel.from_xml_string(xml),xml,np.linalg.inv(allocation)

def simulate(path,obstacles,floor_z,target_yaw,out,seconds=90,video=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);path=np.asarray(path,float);model,xml,mixer=make_world(obstacles,floor_z);(out/'drone_world.xml').write_text(xml);data=mujoco.MjData(model);data.qpos[:3]=path[0];data.qpos[3]=1;mujoco.mj_forward(model,data);wp=1;rows=[];collisions=0;stable=None;success=False;dt=model.opt.timestep
 renderer=None;writer=None
 if video:
  import cv2
  renderer=mujoco.Renderer(model,height=480,width=640);camera=mujoco.MjvCamera();camera.distance=5;camera.azimuth=135;camera.elevation=-30;writer=cv2.VideoWriter(str(out/'drone.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),20,(640,480))
 for step in range(int(seconds/dt)):
  pos=data.qpos[:3];vel=data.qvel[:3]
  while wp<len(path)-1 and np.linalg.norm(pos-path[wp])<.2:wp+=1
  error=path[wp]-pos;vd=1.0*error;speed=np.linalg.norm(vd)
  if speed>.65:vd*=.65/speed
  acc=2.5*(vd-vel);acc=np.clip(acc,-2,2);force=acc+np.array([0,0,9.81]);z=force/np.linalg.norm(force);x_heading=np.array([np.cos(target_yaw),np.sin(target_yaw),0]);y=np.cross(z,x_heading);y/=np.linalg.norm(y);x=np.cross(y,z);Rd=np.column_stack([x,y,z]);R=data.xmat[1].reshape(3,3)
  e=.5*(Rd.T@R-R.T@Rd);eR=np.array([e[2,1],e[0,2],e[1,0]]);omega=data.qvel[3:6];torque=-1.4*eR-.32*omega;thrust=max(0,float(force@R[:,2]));data.ctrl[:]=np.clip(mixer@np.r_[thrust,torque],0,8)
  mujoco.mj_step(model,data);tt=(step+1)*dt
  if data.ncon:collisions+=1
  if np.linalg.norm(data.qpos[:3]-path[-1])<.1 and np.linalg.norm(data.qvel[:3])<.12:
   if stable is None:stable=tt
   if tt-stable>1.0:success=True
  else:stable=None
  if step%max(1,int(.05/dt))==0:
   rows.append([tt,*data.qpos[:7],*data.qvel[:6],int(data.ncon>0)])
   if renderer:
    camera.lookat[:]=data.qpos[:3];renderer.update_scene(data,camera=camera);writer.write(renderer.render()[:,:,::-1])
  if success or data.qpos[2]<floor_z+.12:break
 if renderer:renderer.close();writer.release()
 arr=np.array(rows);np.savetxt(out/'drone_trajectory.csv',arr,delimiter=',',header='time_s,x,y,z,qw,qx,qy,qz,vx,vy,vz,wx,wy,wz,contact',comments='')
 return {'status':'success' if success and collisions==0 else 'collision' if collisions else 'timeout','final_position':data.qpos[:3].tolist(),'goal_error_m':float(np.linalg.norm(data.qpos[:3]-path[-1])),'simulated_seconds':tt,'collision_steps':collisions,'path_length_m':float(np.linalg.norm(np.diff(arr[:,1:4],axis=0),axis=1).sum()),'physics':'MuJoCo 6DOF, 1kg body, four bounded thrust actuators','localization':'simulator-state-oracle','camera_mount':'ideal stabilized gimbal, no gimbal dynamics','world_collision':'reconstructed conservative AABB layer','GT_access':False}
