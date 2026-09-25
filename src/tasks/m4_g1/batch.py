"""Execute a frozen M4 language/spawn protocol; hidden intended IDs are not read."""
from pathlib import Path
import json,subprocess,os,sys,time,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'experiments/tasks/g1_M4/replay_20260924';SCENE=ROOT/'experiments/world_lobby/M4/astra_model'
def main():
 protocol=json.loads((OUT/'execution_protocol.json').read_text());records=[]
 env=os.environ.copy();env['MUJOCO_GL']='osmesa';env['LD_LIBRARY_PATH']=str(ROOT/'runtime/osmesa/extracted/usr/lib/x86_64-linux-gnu')+':'+env.get('LD_LIBRARY_PATH','');env['OMP_NUM_THREADS']='1'
 for r in protocol['requests']:
  request=ROOT/r['request'];q=json.loads(request.read_text());ep=request.parent
  if not (ep/'summary.json').exists():
   command=[str(ROOT/'.venv-tasks/bin/python'),'-m','src.tasks.m4_g1.episode','--scene',str(SCENE),'--request',str(request),'--out',str(ep),'--floor-z',str(q['floor_z']),'--seconds',str(protocol['controller']['timeout_s'])]
   with (ep/'run.log').open('w') as log:result=subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
   if result.returncode and not (ep/'summary.json').exists():(ep/'summary.json').write_text(json.dumps({'status':'runner_error','returncode':result.returncode,'instruction':q['instruction'],'scene_method':'M4'})+'\n')
  s=json.loads((ep/'summary.json').read_text());records.append({'episode_id':q['episode_id'],'status':s['status'],'target_id':s.get('target_id'),'path_length_m':s.get('path_length_m'),'simulated_seconds':s.get('simulated_seconds'),'obstacle_contact_steps':s.get('obstacle_contact_steps'),'fallen':s.get('fallen')});print(json.dumps(records[-1]),flush=True)
 counts={k:sum(r['status']==k for r in records) for k in sorted({r['status'] for r in records})}
 (OUT/'batch_summary.json').write_text(json.dumps({'scene_method':'M4','counts':counts,'episodes':records,'total':len(records),'protocol_sha256':hashlib.sha256((OUT/'execution_protocol.json').read_bytes()).hexdigest(),'scope':'Navigation outcomes; task identity and visibility require independent post-execution evaluation'},indent=2)+'\n');print('BATCH_COMPLETE',counts,flush=True)
if __name__=='__main__':main()
