"""Rebuild own candidate from copied scripts/parameters and compare geometry, no renders."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];BLENDER='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,log):
 with log.open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--method',required=True);a=p.parse_args();d=R/'models'/a.method;dest=R/'reproductions'/a.method
 dest.mkdir(parents=True,exist_ok=False)
 # Builders may emit validation records while constructing a fresh scene.
 # Prepare empty output directories, never copy old checks or saved geometry.
 (dest/'checks').mkdir()
 before={str(f.relative_to(d)):sha(f) for f in d.rglob('*') if f.is_file() and f.suffix not in ['.pyc']}
 for f in d.rglob('*'):
  if not f.is_file() or f.suffix not in ['.py','.json','.npz','.npy']:continue
  if any(part in ['checks','versions','independent_review','__pycache__'] for part in f.relative_to(d).parts):continue
  target=dest/f.relative_to(d);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 script=(dest/'build_scene.py').read_text()
 assert str(d) not in script,'Hardcoded original output path; explicit author adapter required before rebuild'
 run([BLENDER,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(dest/'build_scene.py')],dest/'build.log')
 run([BLENDER,'-b','--factory-startup','--threads','2','--python-exit-code','1','--python',str(R/'tools/inspect_scene.py'),'--','--model',str(dest/'scene.blend'),'--out',str(dest/'inspection.json')],dest/'inspect.log')
 original=json.loads((d/'checks/artifact_inspection.json').read_text());rebuilt=json.loads((dest/'inspection.json').read_text());x={m['name']:m for m in original['meshes']};y={m['name']:m for m in rebuilt['meshes']};assert x.keys()==y.keys()
 worst=0.
 for name,m in x.items():
  n=y[name];assert m['vertices']==n['vertices'] and m['triangles']==n['triangles'] and m['materials']==n['materials'],name
  if m['bounds'] is not None:err=float(np.max(abs(np.array(m['bounds'])-np.array(n['bounds']))));worst=max(worst,err);assert err<2e-5,(name,err)
 assert all(sha(d/n)==h for n,h in before.items()),'Rebuild changed source candidate'
 result=dict(status='PASS',source_model_sha256=sha(d/'scene.blend'),rebuilt_model_sha256=sha(dest/'scene.blend'),source_glb_sha256=sha(d/'scene.glb'),rebuilt_glb_sha256=sha(dest/'scene.glb'),meshes=len(x),triangles=original['triangles'],maximum_bound_difference_m=worst,byte_identical_blend_required=False,source_files_unchanged=True,renders=0)
 (d/'checks/rebuild_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
