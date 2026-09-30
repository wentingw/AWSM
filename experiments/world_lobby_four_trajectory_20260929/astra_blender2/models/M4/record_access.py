"""Write auditable scope/access record from this independent session's actual operations."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4';T=R.parent.parent/'tools';C=R.parent.parent/'configs/modelling_contract.md'
p=json.load(open(I/'packet.json'));keys=[33,61,74,82,91,100,108,118,129,155]
reads=[dict(path=str(C),purpose='User-directed contract read'),dict(path=str(I/'packet.json'),purpose='All180 allowed camera matrices, intrinsics, RGB/DA3 paths and metadata')]
for f in sorted((I/'contact_sheets').glob('*.jpg')):reads.append(dict(path=str(f),purpose='Viewed real contact sheet covering assigned180 RGB'))
for i in keys:reads.append(dict(path=p['frames'][i]['rgb'],purpose='Original keyframe visually inspected; hand-picked pixels for measurements; comparison source'))
for i in keys:reads.append(dict(path=p['frames'][i]['geometry'],purpose='Numeric original predicted DA3 plane/point backprojection; NPZ K and packet camera'))
for f in ['paired_check_blender.py','visualize_checks.py','raycast_scene.py','depth_math.py','inspect_scene.py','validate_artifacts.py']:reads.append(dict(path=str(T/f),purpose='Permitted generic tool source read; selected tools executed and may import other tools in this same allowlist'))
checks=[]
for path in sorted((R/'checks').rglob('report.json')):
 if path.parent.name.startswith('input'):
  for f in p['frames']:reads.append(dict(path=f['geometry'],purpose='Generic full180 input BVH check predicted-depth read',pass_path=str(path.parent)))
for path in sorted((R/'checks').glob('v*/paired_report.json')):
 checks.append(str(path))
 for i in keys:
  reads.append(dict(path=p['frames'][i]['geometry'],purpose='Generic paired same-grid predicted-depth check',pass_path=str(path.parent)))
# Operational command descriptions reflect executed groups, not an assertion that every listed file was visually read.
commands=[
'cat exact modelling_contract.md',
'ls -la inputs (nonexistent path within own M4 output; failed, no data read)',
'ls -la allowed inputs/M4; pwd and ls -la own output',
'Python packet schema/metadata inspection and recursive filename listing of allowed inputs/M4 only',
'cat six explicitly permitted generic tool sources',
'view_image six contact sheets, ten original RGB keyframes',
'Python inspect NPZ0061 schema and ten sampled camera origins',
'python3 measure_scene.py > analysis/measurement_console.txt',
'python3 triangulate.py > analysis/triangulation_console.txt (initial correspondences then added end wall/tree/emblem observations; no renders)',
'python3 prepare_layout.py (initial parameter draft then corrected inferred far lamp heights before first build)',
'BLENDER -b --factory-startup --threads 2 --python-exit-code 1 --python build_scene.py > checks/build_v1.log',
'All native numerical/render invocations set OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2; no GPU',
'Own log tails/session monitoring; local scripts authored under models/M4 only',
'write_stdin Ctrl-C sent once to own build session72776 while build appeared slow; delayed internal break after successful exports, exit1',
'Listed available tool metadata searching for own-session termination capability; no external connector called, no process list read',
'python3 run_initial_checks.py (sequential generic helpers, each exit0)',
'view_image all10 checks/v1/*_comparison.jpg actual saved comparison sheets',
'python3 analyze_checks.py reads only saved check arrays for spatial residuals and full-input diagnostics; no additional raycast/render',
'python3 finalize_initial.py; python3 record_access.py; local record/schema/hash audit and snapshot copies'
]
if checks:commands.append('Generic paired_check_blender.py --method-dir models/M4 --packet inputs/M4/packet.json (full command stored checks/commands.log)')
for f in ['visualize_v1.log','input_v1.log','inspect_v1.log','validate_v1.log']:
 if (R/'checks'/f).exists():commands.append('Generic tool execution recorded in checks/'+f+' and checks/commands.log')
log=dict(method_id='M4',session='independent fresh author initial v1',scope=dict(allowed_input=str(I),allowed_output=str(R),contract=str(C),generic_tools=[str(T/f) for f in ['paired_check_blender.py','visualize_checks.py','depth_math.py','raycast_scene.py','inspect_scene.py','validate_artifacts.py']],runtime='User-specified Blender/Python binaries and normal installed libraries; not scene data'),declared_reads=reads,output_reads='Own authored scripts/layout/records/build logs; actual v1 comparison outputs and numeric reports. All within models/M4.',directory_listing='Allowed inputs/M4 filenames recursively; own output directory. No parent experiment listing.',commands=commands,prohibited_accesses=[],agents_spawned=0,web_access=False,gt_geometry_or_depth_used=False,gt_camera_matrices_used='explicitly permitted packet cameras only',record_notes=['Filename listing does not mean image/array content read.','Generic full input checker reads all180 own predicted DA3 NPZs.','Build does not load any saved blend, previous or foreign model.','No global process inspection or /proc access.'])
json.dump(log,open(R/'input_access_log.json','w'),indent=2)
