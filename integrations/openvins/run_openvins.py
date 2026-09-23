#!/usr/bin/env python3
"""Validate and launch the real OpenVINS ROS2 pipeline."""
import argparse, hashlib, json, os, shutil, signal, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('dataset',type=Path); ap.add_argument('--out',type=Path,default=Path('vio-output')); ap.add_argument('--config',type=Path,default=ROOT/'config/openvins_fixed_mono.yaml'); ap.add_argument('--rate',type=float,default=1.0); ap.add_argument('--ros-domain-id',type=int,default=None); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
 a.dataset=a.dataset.resolve(); a.config=a.config.resolve(); a.out=a.out.resolve()
 if not a.config.is_file(): print(f'INVALID: config not found: {a.config}',file=sys.stderr); return 2
 if a.out.exists() and any(a.out.iterdir()) and not a.dry_run: print(f'REFUSING overwrite of non-empty output: {a.out}',file=sys.stderr); return 2
 if subprocess.run([sys.executable,str(ROOT/'scripts/validate_dataset.py'),str(a.dataset)]).returncode: return 2
 ros=shutil.which('ros2'); launch=os.environ.get('OPENVINS_LAUNCH','ov_msckf subscribe.launch.py')
 if not ros and not a.dry_run: print('BLOCKED: ros2 is not installed; install ROS2 and OpenVINS first',file=sys.stderr); return 3
 env=os.environ.copy()
 prefix=os.environ.get('OPENVINS_PREFIX')
 if prefix:
  env['AMENT_PREFIX_PATH']=prefix+os.pathsep+env.get('AMENT_PREFIX_PATH','')
  env['CMAKE_PREFIX_PATH']=prefix+os.pathsep+env.get('CMAKE_PREFIX_PATH','')
  env['LD_LIBRARY_PATH']=str(Path(prefix)/'lib')+os.pathsep+env.get('LD_LIBRARY_PATH','')
 if a.ros_domain_id is not None: env['ROS_DOMAIN_ID']=str(a.ros_domain_id)
 replay=[sys.executable,str(ROOT/'scripts/replay_ros2.py'),str(a.dataset),'--rate',str(a.rate)]
 ov=[ros,'launch']+launch.split()+['config_path:='+str(a.config),'max_cameras:=1','use_stereo:=false'] if ros else ['ros2','launch']+launch.split()
 collector=[sys.executable,str(ROOT/'scripts/collect_odom.py'),str(a.out)]
 print('replay:',*replay); print('openvins:',*ov); print('collector:',*collector)
 if a.dry_run:
  print('config:',a.config); print('provenance: no ground truth is read by this runner'); return 0
 a.out.mkdir(parents=True,exist_ok=True)
 shutil.copy2(a.config,a.out/'openvins_config_used.yaml')
 refs = {}
 for key in ('relative_config_imu:', 'relative_config_imucam:'):
  for line in a.config.read_text().splitlines():
   if line.strip().startswith(key):
    ref = (a.config.parent / line.split(':',1)[1].strip().strip('\"')).resolve()
    if ref.is_file(): refs[str(ref)] = hashlib.sha256(ref.read_bytes()).hexdigest()
 (a.out/'run_provenance.json').write_text(json.dumps({'dataset':str(a.dataset),'config':str(a.config),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'referenced_configs':refs,'ground_truth_read':False},indent=2)+'\n')
 logs=[(a.out/'openvins.log').open('w'),(a.out/'collector.log').open('w'),(a.out/'replay.log').open('w')]
 procs=[]
 try:
  for cmd,log in zip((ov,collector),logs[:2]): procs.append(subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT))
  time.sleep(3.0)
  procs.append(subprocess.Popen(replay,env=env,stdout=logs[2],stderr=subprocess.STDOUT))
  replay_rc=procs[2].wait()
  time.sleep(2.0)
  if procs[0].poll() is None: procs[0].send_signal(signal.SIGINT)
  if procs[1].poll() is None: procs[1].send_signal(signal.SIGINT)
  for proc in procs[:2]: proc.wait(timeout=15)
  pose=a.out/'pose_imu.tum'
  count=sum(1 for line in pose.read_text().splitlines() if line.strip() and not line.startswith('#')) if pose.exists() else 0
  if replay_rc != 0 or count == 0:
   print(f'FAILED: replay_rc={replay_rc}, pose_imu_samples={count}',file=sys.stderr); return 4
  return 0
 except KeyboardInterrupt:return 130
 except subprocess.TimeoutExpired:return 5
 finally:
  for proc in procs:
   if proc.poll() is None: proc.terminate()
  for log in logs: log.close()
if __name__=='__main__':raise SystemExit(main())
