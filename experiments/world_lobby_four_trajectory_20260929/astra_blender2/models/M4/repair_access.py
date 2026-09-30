import json,datetime
from pathlib import Path
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4';T=R.parent.parent/'tools'
p=R/'input_access_log.json';d=json.load(open(p))
if 'revision_author' not in d:
 d['revision_author']={'scope':'M4 ONLY, same explicit user allowlist; no subagents/web/global process inspection','reads':[],'commands':[],'notes':['Initial file-name enumeration covered only inputs/M4 and models/M4; no parent or root provenance log read.','Source/library runtime reads by authorized Blender/Python are normal tool runtime, not experiment data.']}
r=d['revision_author'];seen={x['path'] for x in r['reads']}
def add(path,purpose):
 if str(path) not in seen:r['reads'].append({'path':str(path),'purpose':purpose});seen.add(str(path))
add(R.parent.parent/'configs/modelling_contract.md','User-directed contract')
for name in ['packet.json']+[f'contact_sheets/{a}.jpg' for a in ['000_029','030_059','060_089','090_119','120_149','150_179']]:add(I/name,'Revision author actual read/visual inspection')
for name in ['paired_check_blender.py','visualize_checks.py','raycast_scene.py','depth_math.py','inspect_scene.py','validate_artifacts.py']:add(T/name,'Allowed generic source read and execution')
for name in ['independent_review/initial_review.md','independent_review/geometry_camera_audit.json','INITIAL_HANDOFF.md','modelling_manifest.json','layout.json','build_scene.py','record_access.py','triangulate.py','measure_scene.py','iteration_log.json','analysis/measurement_decisions.json','analysis/measurements.json','analysis/triangulation.json','analyze_checks.py']:add(R/name,'Current v1 construction, evidence or independent initial review read')
for i in [33,61,74,82,91,100,108,129,155]:add(I/f'rgb/{i:04d}.png','Original source RGB visually inspected')
for i in [33,61,74,82,91,100,108,118,129,155]:add(R/f'checks/v1/{i:04d}_comparison.jpg','Actual v1 RGB/depth/error/edge comparison visually inspected')
for path in (R/'analysis').glob('pendant_projection_v1_*.jpg'):add(path,'M4 source image with old point projections, no scene render')
for i in [61,129]:add(I/f'geometry/{i:04d}.npz','Own DA3 backprojection using NPZ intrinsics and packet cameras')
r['commands'] += ['Contract/source reads by cat/sed; rg filename listing only scoped directories; tools.view_image contact sheets, comparisons and original images','OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 repair_measure.py; inline measurement trials from repair_measure (no rendering)'] if not r['commands'] else []
d['revision_author']=r;p.write_text(json.dumps(d,indent=2)+'\n')
