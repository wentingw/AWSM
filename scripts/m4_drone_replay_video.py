"""Replay a recorded M4 drone episode in display-only M4 meshes; no re-simulation."""
from pathlib import Path
import argparse,csv,json,hashlib,os,subprocess,xml.etree.ElementTree as ET
import numpy as np,mujoco,cv2
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--query',type=int,default=13);ap.add_argument('--display-manifest',type=Path,required=True);args=ap.parse_args()
 ep=ROOT/f'experiments/tasks/drone_M4/replay_20260924/episode_{args.query:02d}';out=ROOT/'blog/assets/m4_tasks';tmp=ROOT/'experiments/tasks/drone_M4/presentation_20260924';tmp.mkdir(parents=True,exist_ok=True)
 manifest=json.loads(args.display_manifest.read_text());tree=ET.parse(ep/'drone_world.xml');r=tree.getroot();world=r.find('worldbody');asset=r.find('asset')
 if asset is None:asset=ET.SubElement(r,'asset')
 for g in list(world.findall('geom')):world.remove(g)
 for light in list(world.findall('light')):world.remove(light)
 ET.SubElement(world,'light',{'pos':'17 22 9','dir':'0 0 -1','directional':'true','diffuse':'.75 .75 .75','ambient':'.35 .35 .35','castshadow':'false'})
 visual=r.find('visual');ET.SubElement(visual,'global',{'offwidth':'960','offheight':'640'});ET.SubElement(visual,'headlight',{'ambient':'.3 .3 .3','diffuse':'.5 .5 .5','specular':'.1 .1 .1'})
 for i,m in enumerate(manifest.get('meshes',manifest.get('groups',[]))):
  meshname=f'm4_visual_{i}';f=Path(m.get('file',m.get('obj')));f=f if f.is_absolute() else args.display_manifest.parent/f
  ET.SubElement(asset,'mesh',{'name':meshname,'file':str(f.resolve()),'inertia':'shell'})
  ET.SubElement(world,'geom',{'name':meshname,'type':'mesh','mesh':meshname,'contype':'0','conaffinity':'0','rgba':' '.join(map(str,m['rgba']))})
 display=tmp/'episode_13_display.xml';tree.write(display)
 model=mujoco.MjModel.from_xml_path(str(display));data=mujoco.MjData(model);assert model.nq==7
 src=ep/'drone_trajectory.csv';a=np.genfromtxt(src,delimiter=',',names=True);states=np.column_stack([a[n] for n in ['x','y','z','qw','qx','qy','qz']]);times=a['time_s'];fps=20;render_times=np.arange(0,float(times[-1])+.025,1/fps)
 renderer=mujoco.Renderer(model,height=640,width=960);cam=mujoco.MjvCamera();cam.type=mujoco.mjtCamera.mjCAMERA_FREE;cam.distance=6.2;cam.azimuth=135;cam.elevation=-28
 raw=tmp/'episode_13_raw.mp4';writer=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),fps,(960,640));poster=None
 for ti,t in enumerate(render_times):
  j=int(np.argmin(abs(times-t)));data.qpos[:]=states[j];mujoco.mj_forward(model,data);cam.lookat[:]=states[j,:3]+[0,0,-.2];renderer.update_scene(data,camera=cam);frame=renderer.render()[:,:,::-1].copy()
  cv2.rectangle(frame,(0,0),(960,87),(28,43,38),-1);cv2.putText(frame,f'M4 | Drone reference-view search | Query {args.query:02d}',(20,34),cv2.FONT_HERSHEY_SIMPLEX,.8,(243,246,241),2,cv2.LINE_AA);cv2.putText(frame,f'Physical trajectory replay | t={t:.2f}s | 1x | display cutaway',(20,68),cv2.FONT_HERSHEY_SIMPLEX,.65,(220,232,225),1,cv2.LINE_AA)
  writer.write(frame)
  if ti==len(render_times)//2:poster=frame.copy()
 writer.release();renderer.close();target=out/'drone_episode.mp4';subprocess.run([os.environ.get('FFMPEG','ffmpeg'),'-y','-v','error','-i',str(raw),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True);cv2.imwrite(str(out/'drone_poster.jpg'),poster)
 meta={'query_id':args.query,'source_trajectory':str(src),'source_trajectory_sha256':sha(src),'source_world_xml_sha256':sha(ep/'drone_world.xml'),'display_manifest_sha256':sha(args.display_manifest),'display_only':True,'simulation_rerun':False,'timing':'20 fps nearest recorded state, original timestamps, 1x speed','recorded_duration_s':float(times[-1]),'frame_count':len(render_times),'omitted_display_objects':manifest.get('omitted_objects',[]),'codec':'H.264 yuv420p faststart'};(out/'drone_episode.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
