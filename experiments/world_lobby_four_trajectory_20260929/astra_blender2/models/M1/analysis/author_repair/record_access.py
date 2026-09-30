"""Maintain explicit current-author access ledger, preserving inherited v1 claims."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];B=R.parents[1];P=B/'inputs/M1'
p=R/'input_access_log.json';d=json.loads(p.read_text())
paths=[B/'configs/modelling_contract.md',P/'packet.json']
paths += [P/'contact_sheets'/f'{i:03d}_{i+29:03d}.jpg' for i in range(0,180,30)]
paths += [B/'tools'/n for n in ['paired_check_blender.py','visualize_checks.py','raycast_scene.py','depth_math.py','inspect_scene.py','validate_artifacts.py']]
paths += [R/n for n in ['build_scene.py','layout.json','objects.json','cameras.json','modelling_manifest.json','input_access_log.json','iteration_log.json','coordinator_tool_note.json','analysis/measurements.json','analysis/paired_visual_inspection_v1.json','independent_review/initial_review.md','independent_review/initial_review.json','independent_review/author_handoff.md','independent_review/audit_blender.py']]
paths += [R/'checks/v1'/f'{i:04d}_comparison.jpg' for i in [33,61,74,82,91,100,108,118,129,155]]
paths += [P/'rgb'/f'{i:04d}.png' for i in [61,74,82,108,129,155]]
commands=[
 {'action':'initial scope discovery','command':'cat exact modelling_contract.md; pwd && rg --files -g AGENTS.md -g * . exact_inputs_M1','detail':'Only listed M1 input/model trees; no ancestor AGENTS search or root provenance logs.'},
 {'action':'read evidence and generic scripts','command':'cat/sed named paths in read_paths','detail':'One overlarge batch output was truncated; build_scene.py and operative records were reread in smaller outputs. Inherited history is not current-author first-hand evidence.'},
 {'action':'visual input inspection','command':'view_image six contact sheets, all ten v1 actual comparisons, six full-resolution source RGB images','detail':'All six sheets and ten comparisons actually viewed; optical-Z panel inspected for each. No depth reference exists.'},
 {'action':'conditional RGB measurements','command':'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 python3 analysis/author_repair/measure_rgb.py','detail':'Manual pixel landmarks and ray-plane intersections using unchanged v1 cameras; scipy robust fit retains conflict.'},
 {'action':'inline arithmetic probes','command':'python3 heredocs reading M1 packet/cameras/measurements, projecting manually supplied pixels onto assumed horizontal planes','detail':'No external SfM, SLAM, depth, GT, evaluation, or web.'},
 {'action':'prepare v2','command':'python3 author_prepare_v2.py','detail':'Preserves v1 records and applies recorded M1 repairs; no renders.'},
 {'action':'build v2','command':'blender -b --factory-startup --threads 2 --python-exit-code 1 --python build_scene.py > build_v2.log 2>&1','detail':'CPU libraries limited to2; TMPDIR is M1/.tmp. Completed from empty scene, no .blend input.'},
 {'action':'ten paired checks v2','command':'blender -b --factory-startup --threads 2 --python-exit-code 1 --python exact_tools/paired_check_blender.py -- --method-dir M1 --packet inputs/M1/packet.json > checks/paired_v2.log 2>&1','detail':'CPU Cycles12samples, fixed10; includes model opticalZ. Raycast_scene/depth_math imported generic dependencies, not a full180 pass.'}
]
d['revision_author_session']={'role':'revision AUTHOR, not independent reviewer','method_id':'M1','read_paths':[str(x) for x in paths],'method_directory_discovery_only':True,'commands':commands,'inherited_history':'Top-level pre-existing log preserved as inherited author claims. Review missing-record finding predates current ready manifest/logs; unavailable earlier session history remains unknown to this fresh author. Coordinator history only from local coordinator_tool_note.json and retained checks.','write_scope':str(R),'no_camera_or_mask_changes':True,'input_da3':'N/A; packet geometry_frames=0; no depth prediction/reference supplied','input_full180_bvh_passes':0,'no_subagents':True,'no_forbidden_access':True}
p.write_text(json.dumps(d,indent=2)+'\n')
print('Current author access ledger saved')
