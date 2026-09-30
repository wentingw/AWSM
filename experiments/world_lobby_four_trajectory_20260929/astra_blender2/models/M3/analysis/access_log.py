import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R.parents[1];I=B/'inputs/M3';P=json.loads((I/'packet.json').read_text())
reads=[dict(path=str(B/'configs/modelling_contract.md'),purpose='Mandatory modelling scope/schema',mechanism='cat'),dict(path=str(I/'packet.json'),purpose='native poses, paths, intrinsics and provenance',mechanism='python json')]
reads += [dict(path=str(p),purpose='All180 RGB survey',mechanism='view_image',inspected=True) for p in sorted((I/'contact_sheets').glob('*.jpg'))]
originals=[33,61,74,82,91,100,108,118,129,155]
reads += [dict(path=P['frames'][i]['rgb'],purpose='Original full-resolution semantic inspection; comparison source',mechanism='view_image and visualize_checks',inspected=True) for i in originals]
geo=[0,33,61,82,108,129,155,91,74]
reads += [dict(path=P['frames'][i]['geometry'],purpose='NPZ schema or selected-region backprojection, plane fitting, triangulation depth conflict',mechanism='numpy.load',inspected_numeric=True) for i in geo]
for name in ['paired_check_blender.py','visualize_checks.py','raycast_scene.py','depth_math.py','inspect_scene.py','validate_artifacts.py']:
 reads.append(dict(path=str(B/'tools'/name),purpose='Authorized generic checks',mechanism='source read and/or dependency import; execution recorded in commands'))
commands=[
 'cat CONFIG/modelling_contract.md',
 'ls -la INPUT; ls -la OUTPUT; sed paired_check_blender.py',
 'python packet/NPZ schema inspection',
 'view_image all six INPUT/contact_sheets/*.jpg',
 'view_image INPUT/rgb/{0033,0061,0074,0082,0091,0100,0108,0118,0129,0155}.png',
 'sed raycast_scene.py',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 analysis/measure.py',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 analysis/derive.py',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 analysis/anchors.py (first failed RecursionError; corrected and rerun)',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 analysis/additional.py',
 'cat visualize_checks.py inspect_scene.py validate_artifacts.py',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 analysis/prepare.py',
 'OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 BLENDER -b --factory-startup --threads 2 --python-exit-code 1 --python OUTPUT/build_scene.py > OUTPUT/logs/build_v1.log 2>&1',
 'tail OUTPUT/logs/build_v1.log',
 'python3 OUTPUT/analysis/access_log.py']
log=dict(scope=dict(allowed_input=str(I),allowed_output=str(R),contract=str(B/'configs/modelling_contract.md'),generic_tools=str(B/'tools'),blender='/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender',runtime='Standard Python/Blender installed packages and libraries only; no external assets'),prohibited_accesses=[],scope_breaches=[],read_records=reads,commands=commands,write_scope='All authored scripts, JSON, model and logs under OUTPUT only. mkdir and shell heredocs used for own numeric and semantic authoring scripts; scripts then read their own outputs.',directory_listings=[str(I),str(R),str(I/'contact_sheets')],agents_spawned=0,network_accesses=0,inspection_policy='Contact sheets cover all180; only listed original RGB viewed individually. Full-input BVH pass reads all180 predicted NPZ and packet poses without further RGB render. Tool and Python runtime files are generic dependencies, not scene inputs.')
(R/'input_access_log.json').write_text(json.dumps(log,indent=2)+'\n')
