"""Sequential authorized method-local checks. No hidden renders or supplemental views."""
import subprocess,json,os,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4';T=R.parent.parent/'tools'
B='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender';PY='/home/hchen/Documents/astraBlenderTest/reconstruction/.venv/bin/python'
env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(R/'checks/mplconfig'))
commands=[]
def run(label,args):
 entry=dict(label=label,args=args,started=time.time(),scope='M4 only',threads=2);commands.append(entry)
 (R/'checks/revision_commands.json').write_text(json.dumps(commands,indent=2));print('START',label,flush=True)
 with open(R/f'checks/{label}.log','w') as f:ret=subprocess.run(args,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 entry.update(returncode=ret,ended=time.time());(R/'checks/revision_commands.json').write_text(json.dumps(commands,indent=2));print('END',label,ret,flush=True)
 if ret:raise SystemExit(ret)
def blend(script,args=[]):return [B,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(script),'--']+args
if __name__=='__main__':
 mode=sys.argv[1];v=json.load(open(R/'modelling_manifest.json'))['revisions']
 if mode=='build':run(f'build_v{v}',blend(R/'build_scene.py'))
 elif mode=='paired':
  run(f'paired_v{v}',blend(T/'paired_check_blender.py',['--method-dir',str(R),'--packet',str(I/'packet.json')]))
  run(f'visualize_v{v}',['python3',str(T/'visualize_checks.py'),'--method-dir',str(R),'--packet',str(I/'packet.json'),'--version',str(v)])
 elif mode in ['input_v2','input_final']:
  run(mode,blend(T/'raycast_scene.py',['--model',str(R/'scene.blend'),'--input-packet',str(I/'packet.json'),'--model-manifest',str(R/'modelling_manifest.json'),'--out',str(R/'checks'/mode)]))
  m=json.load(open(R/'modelling_manifest.json'));m['input_bvh_pass_count']=len(list((R/'checks').glob('input*/report.json')));(R/'modelling_manifest.json').write_text(json.dumps(m,indent=2))
 elif mode=='validate':
  run(f'inspect_v{v}',blend(T/'inspect_scene.py',['--model',str(R/'scene.blend'),'--out',str(R/'checks/artifact_inspection.json')]))
  run(f'validate_v{v}',[PY,str(T/'validate_artifacts.py'),'--method-dir',str(R)])
 # append rather than erase previous mode command history
 hist=R/'checks/revision_command_history.json';history=json.load(open(hist)) if hist.exists() else [];hist.write_text(json.dumps(history+commands,indent=2))
