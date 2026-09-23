from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[1];blender='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender'
for method in ['B1','B2','B2p','M1']:
 source={'B1':'M2','B2':'B2','B2p':'M3'}.get(method)
 model=ROOT/'experiments/world_lobby'/method/'tsdf_20260923/scene.blend' if source else ROOT.parent/'visual-recon/scene.blend'
 transform=ROOT/'results/evaluation/pose/current'/f'{source}_registration.json' if source else ROOT/'results/M1/render_manifest.json'
 out=ROOT/'results/evaluation/geometry'/(method if source else 'M1_observed_eval');cmd=[blender,'-b','--threads','4','--python-exit-code','1','--python',str(ROOT/'scripts/evaluate_blend_surface_blender.py'),'--','--model',str(model),'--out',str(out),'--transform-json',str(transform),'--samples','100000']
 with (ROOT/'logs'/f'{method}_geometry.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 d=json.loads((out/'surface_metrics.json').read_text());print(method,d['model_to_gt']['mean_m'],d['observed_gt_to_model']['mean_m'],flush=True)
