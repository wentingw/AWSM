import os,time,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;T=R.parent.parent/'tools';I=R.parent.parent/'inputs/M4/packet.json';B='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
os.environ.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
while 'BUILD_COMPLETE' not in (R/'checks/build_v1.log').read_text(errors='replace'):
 if 'Error: Python:' in (R/'checks/build_v1.log').read_text(errors='replace'):raise RuntimeError('Build failed; inspect build log')
 time.sleep(5)
commands=[('paired_v1',[B,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(T/'paired_check_blender.py'),'--','--method-dir',str(R),'--packet',str(I)]),('visualize_v1',['python3',str(T/'visualize_checks.py'),'--method-dir',str(R),'--packet',str(I),'--version','1']),('input_v1',[B,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(T/'raycast_scene.py'),'--','--model',str(R/'scene.blend'),'--input-packet',str(I),'--model-manifest',str(R/'modelling_manifest.json'),'--out',str(R/'checks/input_v1')]),('inspect_v1',[B,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(T/'inspect_scene.py'),'--','--model',str(R/'scene.blend'),'--out',str(R/'checks/artifact_inspection.json')]),('validate_v1',['/home/hchen/Documents/astraBlenderTest/reconstruction/.venv/bin/python',str(T/'validate_artifacts.py'),'--method-dir',str(R)])]
for name,cmd in commands:
 with open(R/'checks/commands.log','a') as f:f.write('\n'+' '.join(cmd)+' > checks/'+name+'.log 2>&1\n')
 with open(R/'checks'/f'{name}.log','w') as log:
  proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=R);json.dump(dict(stage=name,pid=proc.pid,command=cmd),open(R/'checks/active_command.json','w'),indent=2);code=proc.wait()
 print(name,'EXIT',code,flush=True)
 if code:raise RuntimeError(f'{name} failed {code}; no automatic extra renders')
 if name=='input_v1':
  m=json.load(open(R/'modelling_manifest.json'));m['input_bvh_pass_count']=1;json.dump(m,open(R/'modelling_manifest.json','w'),indent=2)
print('INITIAL_CHECK_PIPELINE_COMPLETE',flush=True)
