#!/usr/bin/env python3
import argparse,csv,json,hashlib,os,subprocess
from pathlib import Path
import numpy as np, mujoco, cv2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--episode',type=Path,required=True); ap.add_argument('--world-xml',type=Path); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--poster',type=Path,required=True); ap.add_argument('--fps',type=int,default=20,choices=[20]); ap.add_argument('--speed',type=float,default=1.0,choices=[1.0]); a=ap.parse_args()
    ep=a.episode.resolve(); out=a.out.resolve(); out.parent.mkdir(parents=True,exist_ok=True); a.poster.parent.mkdir(parents=True,exist_ok=True)
    traj_path=ep/'trajectory_full.csv'; xml_path=(a.world_xml or (ep/'episode_world.xml')).resolve(); model=mujoco.MjModel.from_xml_path(str(xml_path)); data=mujoco.MjData(model); rows=list(csv.DictReader(traj_path.open())); qnames=[f'qpos_{i}' for i in range(model.nq)]
    width,height=960,640; renderer=mujoco.Renderer(model,height=height,width=width)
    cam=mujoco.MjvCamera(); cam.type=mujoco.mjtCamera.mjCAMERA_FREE; cam.distance=4.8; cam.azimuth=135; cam.elevation=-28
    raw=ep.parent.parent/'presentation_20260924'/'g1_raw.mp4'; raw.parent.mkdir(parents=True,exist_ok=True)
    writer=cv2.VideoWriter(str(raw),cv2.VideoWriter_fourcc(*'mp4v'),a.fps,(width,height)); poster=None
    for j,row in enumerate(rows):
        data.qpos[:]=[float(row[n]) for n in qnames]; mujoco.mj_forward(model,data)
        p=data.qpos[:3].copy(); cam.lookat[:]=p+np.array([0,0,.4]); cam.distance=4.8; cam.azimuth=135; cam.elevation=-28
        renderer.update_scene(data,camera=cam); frame=renderer.render()[:,:,::-1].copy()
        cv2.rectangle(frame,(0,0),(960,90),(28,43,38),-1)
        t=float(row['time_s']); cv2.putText(frame,'M4 reconstruction | G1 language navigation | replay %.1fx'%a.speed,(22,38),cv2.FONT_HERSHEY_SIMPLEX,.8,(245,245,245),2,cv2.LINE_AA)
        cv2.putText(frame,'t=%.2fs   target: low foliage / pale-grey ceramic pot'%t,(22,72),cv2.FONT_HERSHEY_SIMPLEX,.7,(235,235,235),2,cv2.LINE_AA)
        if poster is None or j==len(rows)//2: poster=frame.copy()
        writer.write(frame)
    writer.release(); renderer.close(); cv2.imwrite(str(a.poster),poster)
    subprocess.run([os.environ.get('FFMPEG','ffmpeg'),'-y','-v','error','-i',str(raw),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
    meta={'source_episode':str(ep),'source_trajectory':str(traj_path),'source_trajectory_sha256':hashlib.sha256(traj_path.read_bytes()).hexdigest(),'world_xml':str(xml_path),'source_world_xml_sha256':hashlib.sha256(xml_path.read_bytes()).hexdigest(),'policy_rerun':False,'teleport':False,'render_mode':'MuJoCo replay of saved qpos; display XML with non-colliding M4 material meshes and hidden collision AABBs','fps':a.fps,'speed_label':1.0}
    meta.update(display_metadata=str(xml_path.parent/'display_metadata.json'),display_manifest_sha256=hashlib.sha256((xml_path.parent/'material_manifest.json').read_bytes()).hexdigest(),source_physics_xml_sha256=hashlib.sha256((ep/'episode_world.xml').read_bytes()).hexdigest(),codec='H.264 yuv420p faststart')
    out.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
if __name__=='__main__': main()
