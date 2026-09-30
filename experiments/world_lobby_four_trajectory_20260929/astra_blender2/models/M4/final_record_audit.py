"""Final author record audit, hashing and evidence-only verification. No BVH/render."""
import json,hashlib,numpy as np,shutil
from pathlib import Path
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4';T=R.parent.parent/'tools';keys=[33,61,74,82,91,100,108,118,129,155]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();load=lambda n:json.load(open(R/n));save=lambda p,x:Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
m=load('modelling_manifest.json');assert m['status']=='ready_for_independent_review' and m['revisions']==2 and m['input_bvh_pass_count']==3
assert m['model_sha256']==sha(R/'scene.blend') and m['scene_glb_sha256']==sha(R/'scene.glb')
ledger=load('checks/paired_ledger.json');assert len(ledger)==20 and all(x['status']=='COMPLETE' for x in ledger)
versions=[]
for v in [1,2]:
 report=load(f'checks/v{v}/paired_report.json');assert report['indices']==keys and report['status']=='COMPLETE';assert report['model_sha256']==sha(R/f'versions/v{v}/scene.blend')
 for i in keys:
  r=load(f'checks/v{v}/{i:04d}_report.json');assert r['rgb_sha256']==sha(R/f'checks/v{v}/{i:04d}_rgb.png');assert r['depth_sha256']==sha(R/f'checks/v{v}/{i:04d}_depth.npz');assert r['model_sha256']==report['model_sha256'];assert (R/f'checks/v{v}/{i:04d}_comparison.jpg').exists()
  a=np.load(R/f'checks/v1/{i:04d}_depth.npz');b=np.load(R/f'checks/v2/{i:04d}_depth.npz');assert np.array_equal(a['input_valid_domain'],b['input_valid_domain']);assert np.array_equal(a['input_da3_z_m'],b['input_da3_z_m'],equal_nan=True);assert np.array_equal(a['camera_to_world'],b['camera_to_world'])
 versions.append(dict(version=v,model_sha256=report['model_sha256'],paired_views=10,all_output_hashes_match=True))
passes=[]
assert len(list((R/'checks').glob('input*/report.json')))==3
for name in ['input_v1','input_v2','input_final']:
 r=load(f'checks/{name}/report.json');assert r['frames']==180;passes.append(dict(path='checks/'+name,frames=180,model_sha256=r['model_sha256'],seconds=r['seconds']))
assert passes[1]['model_sha256']==passes[2]['model_sha256']==m['model_sha256']
a=np.load(R/'checks/input_v2/depth.npz');b=np.load(R/'checks/input_final/depth.npz');assert np.array_equal(a['prediction_z_m'],b['prediction_z_m'],equal_nan=True)
assert all(load(p)['model_sha256']==m['model_sha256'] for p in ['checks/artifact_inspection.json','checks/glb_load.json','checks/saved_mesh_validation.json','checks/author_candidate_audit.json'])
# Validate every required camera field, timestamp, source index and K exactly.
p=json.load(open(I/'packet.json'));cams=load('cameras.json');assert cams['coordinate_frame']=='model' and len(cams['frames'])==180
for a,b in zip(cams['frames'],p['frames']):
 for key in ['sample_index','source_index','timestamp_ns','camera_to_world','intrinsics']:assert a[key]==b[key],key
 assert a['valid'] and 'confidence' in a
# Hash all concrete handoff artifacts and sources (hash manifest excludes itself).
names=['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json','cameras.json','repair_colliders.py','repair_mesh_audit.py','author_repair_notes.md','author_repair_notes.json','modelling_manifest.json','iteration_log.json']
hashes={n:sha(R/n) for n in names};save(R/'artifact_hashes.json',dict(method='M4',version=2,algorithm='SHA256',files=hashes,role='author candidate hash inventory; not freeze'))
# Complete the honest revision access record while preserving original v1 record.
a=load('input_access_log.json');rev=a['revision_author'];seen={x['path'] for x in rev['reads']}
def add(path,purpose):
 path=str(path)
 if path not in seen:rev['reads'].append(dict(path=path,purpose=purpose));seen.add(path)
for f in p['frames']:add(f['geometry'],'Generic full180 input_v2 and input_final each read own DA3; ten paired checks and selected measurement script reads also use these same allowed inputs')
for i in keys:
 add(p['frames'][i]['rgb'],'Original RGB actually viewed by revision author and consumed by visualization')
 for v in [1,2]:
  for suffix in ['comparison.jpg','errors.npz','depth.npz','report.json','rgb.png']:add(R/f'checks/v{v}/{i:04d}_{suffix}','Comparison visually inspected, saved arrays/reports analyzed or hashes validated; RGB data visualization input, no new render in record audit')
for name in ['independent_review/scene_inspection.json','checks/validate_v1.log','checks/input_v1/depth.npz','checks/input_v1/report.json','checks/input_v2/depth.npz','checks/input_v2/report.json','checks/input_final/depth.npz','checks/input_final/report.json','analysis/spatial_residuals_v1.json','checks/v1/paired_report.json','checks/v2/paired_report.json','checks/paired_ledger.json','objects.json','colliders.json','cameras.json','checks/artifact_inspection.json','checks/glb_load.json','checks/author_mesh_audit_v2.json','checks/saved_mesh_validation.json','checks/author_candidate_audit.json','analysis/camera_checks.json','input_access_log.json']:add(R/name,'Revision author numeric/record/geometry evidence read')
rev['commands'] += [
 'python3 repair_access.py; generated revision-specific read/command record preserving v1 record',
 'OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python3 prepare_repair.py; actual selected input DA3, v1 saved errors and RGB correspondences; no render',
 'python3 edit_builder_v2.py; direct source edits only under models/M4',
 'python3 run_repair_checks.py build: first attempt failed before save/export on degenerate chair bevel; log and audit retained; no render or full pass',
 'python3 run_repair_checks.py build: corrected same pre-export v2 draft, exit0; wrote v2 artifacts from scratch',
 'python3 run_repair_checks.py paired:10 exact standard views then visualize, all exit0',
 'view_image all10 actual v2 comparison sheets (plus all10 v1 earlier); original118 viewed to complete original10',
 'python3 run_repair_checks.py input_v2: actual second full180 pass',
 'python3 run_repair_checks.py validate: generic inspect and GLB validation, both exit0',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 author_candidate_audit.py: analytic shape/portal/support and exact camera audit, no raycast/render',
 'OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 python3 analyze_repair.py: existing arrays/metadata, before-after spatial residuals and component bounds, no raycast/render',
 'Saved-scene Blender author read-only BMesh audit via run_repair_checks.run on saved_mesh_validate.py; no scene write/render/BVH',
 'python3 run_repair_checks.py input_final: actual third full180 pass on unchanged v2; arrays independently recomputed and equal',
 'Inline Python metadata/evidence additions to repair_changes_v2.json; one observation-record attempt raised NameError keys after changes JSON saved; reran only observation record successfully. No model changes.',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 finalize_repair.py; final notes/manifests/version snapshots',
 'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 final_record_audit.py; exact hash/domain/camera/budget checks, no new render/BVH',
 'Own checks/build_v2.log and checks/paired_v2.log tails and own tool-session polling only; no process enumeration'
]
rev['exact_check_commands']=load('checks/revision_command_history.json');rev['normal_runtime_write_control']='Numerical/check subprocesses2threads, CPU only; PYTHONDONTWRITEBYTECODE=1 for generic tools; MPLCONFIGDIR is method-local checks/mplconfig. Authored data/program/check outputs only models/M4.'
rev['scope_exceptions']=[];rev['agents_spawned']=0;rev['web_access']=False;rev['final_author_role']='No independent review or freeze claimed';save(R/'input_access_log.json',a)
report=dict(status='PASS',role='AUTHOR final record validation',versions=versions,paired_views=20,supplemental_views=0,input_bvh_passes=passes,exact_camera_frames=180,unchanged_input_domains=True,matching_scene_snapshot_report_hashes=True,same_geometry_main_final_pass=True,model_sha256=m['model_sha256'],scene_glb_sha256=m['scene_glb_sha256'],independent_final_review='pending',freeze=False)
save(R/'checks/final_record_audit.json',report)
for name in ['input_access_log.json','artifact_hashes.json','final_record_audit.py']:shutil.copyfile(R/name,R/'versions/v2'/name)
shutil.copyfile(R/'checks/final_record_audit.json',R/'versions/v2/checks/final_record_audit.json')
print(json.dumps(report,indent=2))
