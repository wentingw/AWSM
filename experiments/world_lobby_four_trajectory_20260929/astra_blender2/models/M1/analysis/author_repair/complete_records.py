"""Complete author-only evidence bookkeeping; no geometry changes."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];J=lambda n:json.loads((R/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(R/n).write_text(json.dumps(d,indent=2)+'\n')
# ASCII spelling for machine-readable validation key.
p=R/'analysis/author_repair/verify_candidate.py';p.write_text(p.read_text().replace('GLΒ','GLB'))
d=J('checks/author/technical_verification.json');d['curved_back_GLB_meshes']=d.pop('curved_back_GLΒ_meshes');save('checks/author/technical_verification.json',d)
log=J('input_access_log.json');s=log['revision_author_session']
s['commands'] += [
 {'action':'v2 visualizations','command':'OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=M1/.mpl TMPDIR=M1/.tmp python3 exact_tools/visualize_checks.py --method-dir M1 --packet inputs/M1/packet.json --version2','result':'checks/visualize_v2.log; ten saved comparisons, all viewed'},
 {'action':'v2 actual image inspection','command':'view_image all10 checks/v2/NNNN_comparison.jpg','result':'Each RGB pair and model-depth panel actually viewed; no new renders'},
 {'action':'author evaluated geometry/projection audit','command':'blender -b --factory-startup --threads2 --python-exit-code1 --python analysis/author_repair/audit_blender.py > checks/author/audit_v2.log','result':'M1 initial-review audit adapted to author output path; no independent review claim, no render or full180 BVH pass'},
 {'action':'generic artifact inspection','command':'blender -b --factory-startup --threads2 --python-exit-code1 --python exact_tools/inspect_scene.py -- --model M1/scene.blend --out M1/checks/artifact_inspection.json','result':'PASS, output retained also under checks/v2; prior v1 root report preserved under versions/v1/checks'},
 {'action':'generic GLB validation','command':'reconstruction/.venv/bin/python exact_tools/validate_artifacts.py --method-dir M1 > checks/validate_v2.log','result':'PASS; generic executable used, no reconstruction data read'},
 {'action':'author technical assertions','command':'reconstruction/.venv/bin/python analysis/author_repair/verify_candidate.py > checks/author/technical_verification.log','result':'PASS; cameras, component mapping, GLB winding, physical seat clearance, all enabled portal proxies, supports and hashes checked'},
 {'action':'own depth evidence and reports','command':'python3 heredoc computes10 saved v1/v2 model-depth statistics; python3 analysis/author_repair/finalize.py','result':'Author notes, per-view observations, before/after parameter and object delta evidence, iteration/manifest updated; depth reference N/A'},
 {'action':'metadata completion','command':'python3 analysis/author_repair/complete_records.py','result':'Access records, final hashes and schema/budget assertions. No scene mutation or rerender'},
 {'action':'own progress monitoring','command':'tail checks/paired_v2.log, tail build_v2.log, cat checks/author/audit_v2.log, checks/validate_v2.log, checks/author/technical_verification.log; own exec sessions only','result':'No process enumeration, /proc, root logs, web, outside-method inputs or agents'}]
s['tool_implicit_and_output_reads']=[str(R/n) for n in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json','cameras.json','modelling_manifest.json','versions/v1/scene.blend','versions/v1/scene.glb','versions/v1/layout.json','versions/v1/objects.json','versions/v1/cameras.json','versions/v2/scene.blend','checks/paired_ledger.json','checks/artifact_inspection.json','checks/glb_load.json','checks/author/geometry_audit.json','checks/author/technical_verification.json','analysis/author_repair/rgb_ray_plane_measurements.json']]
s['tool_implicit_and_output_reads'] += [str(R/f'checks/v{v}/{i:04d}_{suffix}') for v in [1,2] for i in [33,61,74,82,91,100,108,118,129,155] for suffix in ['depth.npz','rgb.png','comparison.jpg']]
s['tool_implicit_and_output_reads'] += [str(R/f'checks/v{v}/paired_report.json') for v in [1,2]]
s['tool_implicit_and_output_reads'] += [str(R.parents[1]/f'inputs/M1/rgb/{i:04d}.png') for i in [33,61,74,82,91,100,108,118,129,155]]
s['read_scope_note']='Application/library/executable loading is generic runtime access, not experiment evidence. All task-data reads stay within authorized M1 paths, contract and six generic tool sources. Contact sheets are thumbnails of all180, not a claim of opening180 originals.'
s['completed_versions_this_author_session']=[2];s['actual_paired_views_this_author_session']=10;s['full180_passes_this_author_session']=0;s['final_geometry_unchanged_after_checks']=True
save('input_access_log.json',log)
m=J('modelling_manifest.json');m['artifact_sha256']={n:sha(R/n) for n in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json','cameras.json']};save('modelling_manifest.json',m)
for n in ['input_access_log.json','iteration_log.json','author_repair_notes.json','author_repair_notes.md','colliders.json']:
 shutil.copyfile(R/n,R/'versions/v2'/n)
shutil.copyfile(R/'modelling_manifest.json',R/'versions/v2/modelling_manifest_final.json')
# Required outputs and no self-freeze, counts derived from actual completed paired ledger.
for n in ['build_scene.py','layout.json','scene.blend','scene.glb','objects.json','colliders.json','cameras.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json','author_repair_notes.md','author_repair_notes.json']:assert (R/n).is_file(),n
assert m['status']=='ready_for_independent_review' and m['quality_status']=='LIMITED'
assert m['revisions']==2 and m['checking_render_count']==20 and m['input_bvh_pass_count']==0
assert len(J('iteration_log.json')['versions'])==2
for n in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','cameras.json']:assert sha(R/n)==sha(R/'versions/v2'/n),n
assert J('checks/glb_load.json')['model_sha256']==sha(R/'scene.blend')
# No recursive traversal outside method; checksum list covers the reviewable required deliverables.
files=['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json','cameras.json','modelling_manifest.json','input_access_log.json','iteration_log.json','author_repair_notes.md','author_repair_notes.json','analysis/paired_visual_inspection_v2.json','checks/author/technical_verification.json']
(R/'final_candidate_sha256.txt').write_text(''.join(f'{sha(R/n)}  {n}\n' for n in files))
print('FINAL_BOOKKEEPING_PASS')
print((R/'final_candidate_sha256.txt').read_text())
