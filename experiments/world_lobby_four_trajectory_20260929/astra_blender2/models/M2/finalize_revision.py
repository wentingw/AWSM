"""Author records only. Does not certify independent review or freeze."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,hashlib,datetime,shutil,numpy as np
from pathlib import Path
R=Path(__file__).parent;I=R.parent.parent/'inputs/M2';T=R.parent.parent/'tools';fixed=[33,61,74,82,91,100,108,118,129,155]
def read(f):return json.loads((R/f).read_text())
def save(f,d):
 p=R/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def sha(f):return hashlib.sha256((R/f).read_bytes()).hexdigest()
manifest=read('modelling_manifest.json');packet=json.loads((I/'packet.json').read_text());cameras=read('cameras.json');L=read('layout.json');ev=read('analysis/revision_evidence.json');meas=read('analysis/revision_measurements.json');audit=read('checks/author_geometry_audit.json');glb=read('checks/author_glb_geometry_audit.json');assert audit['status']==glb['status']=='PASS'
full=[]
for name,v in [('input_v1',1),('input_v2',2),('input_final',3)]:
 rep=read(f'checks/{name}/report.json');assert rep['frames']==180 and rep['mode']=='input_consistency';assert rep['model_sha256']==sha(f'versions/v{v}/scene.blend')
 with np.load(R/f'checks/{name}/depth.npz') as n:
  assert n['prediction_z_m'].shape==n['reference_z_m'].shape==(180,19200)
  ref=n['reference_z_m'];pred=n['prediction_z_m'];domain=np.isfinite(ref)&(ref>=.1)&(ref<=30);valid=domain&np.isfinite(pred)&(pred>=.1)&(pred<=30)
  row={'directory':f'checks/{name}','version':v,'frames':180,'model_sha256':rep['model_sha256'],'aggregate':rep['aggregate'],'reference_sha256':hashlib.sha256(ref.tobytes()).hexdigest(),'domain_sha256':hashlib.sha256(domain.tobytes()).hexdigest(),'outlier_signed_medians_m':{str(i):float(np.median((pred[i]-ref[i])[valid[i]])) for i in [21,22,167,168,175]}}
  full.append(row)
assert len({r['reference_sha256'] for r in full})==len({r['domain_sha256'] for r in full})==1
assert len(list((R/'checks').glob('input*/report.json')))==3
paired=[]
for v in [1,2,3]:
 p=read(f'checks/v{v}/paired_report.json');assert p['status']=='COMPLETE' and p['indices']==fixed;assert p['model_sha256']==sha(f'versions/v{v}/scene.blend')
 for i in fixed:
  with np.load(R/f'checks/v{v}/{i:04d}_depth.npz') as n, np.load(R/f'checks/v1/{i:04d}_depth.npz') as n0:
   assert np.array_equal(n['input_valid_domain'],n0['input_valid_domain']);assert np.allclose(n['input_da3_z_m'],n0['input_da3_z_m'],equal_nan=True)
  assert (R/f'checks/v{v}/{i:04d}_comparison.jpg').exists()
 paired.append({'version':v,'model_sha256':p['model_sha256'],'count':10,'indices':fixed,'all_comparisons_actually_inspected':True,'aggregate_input_consistency':p['aggregate_input_consistency']})
ledger=read('checks/paired_ledger.json');assert len(ledger)==30 and all(x['status']=='COMPLETE' for x in ledger)
# Exact bounds/dimensions changes per logical object, with original pixel-region residual context.
X=np.array(manifest['model_from_input']);bycam={x['sample_index']:x for x in cameras['frames']}
def pixbounds(i,bounds):
 lo,hi=bounds;pts=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);T=np.array(bycam[i]['camera_to_world']);q=(pts-T[:3,3])@T[:3,:3]
 if np.any(q[:,2]<=.1):return [0,0,1280,960]
 uv=q[:,:2]/q[:,2,None]*762.8+[640,480];a=np.clip(np.floor(uv.min(0)),[0,0],[1279,959]).astype(int);b=np.clip(np.ceil(uv.max(0)),[1,1],[1280,960]).astype(int)
 return [*a.tolist(),*b.tolist()]
def regional(ver,i,bb):
 n=np.load(R/f'checks/v{ver}/{i:04d}_depth.npz');x0,y0,x1,y1=np.array(bb)//2;s=np.s_[y0:y1,x0:x1];z=n['model_z_m'][s];ref=n['input_da3_z_m'][s];d=n['input_valid_domain'][s];v=d&np.isfinite(z)&(z>=.1)&(z<=30);e=(z-ref)[v]
 return {'domain_pixels':int(d.sum()),'valid_pixels':int(v.sum()),'signed_median_m':float(np.median(e)) if e.size else None,'signed_p10_p90_m':np.percentile(e,[10,90]).tolist() if e.size else None}
objects=read('objects.json')['objects'];before={r['id']:r for r in read('versions/v1/objects.json')['objects']};changes=[]
for r in objects:
 old=before[r['id']]
 if old['bounds']==r['bounds'] and old['dimensions']==r['dimensions'] and len(old['component_names'])==len(r['component_names']):continue
 evidence=[]
 for i in r['evidence_frames']:
  if i not in fixed:continue
  a=pixbounds(i,old['bounds']);b=pixbounds(i,r['bounds']);box=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]
  if box[2]-box[0]<4 or box[3]-box[1]<4:continue
  evidence.append({'frame':i,'rgb_box':box,'region_definition':'union of projected old/new semantic AABBs; context includes occluders/background, not an isolated object mask','v1':regional(1,i,box),'v2':regional(2,i,box),'v3':regional(3,i,box)})
 changes.append({'id':r['id'],'before_dimensions_m':old['dimensions'],'after_dimensions_m':r['dimensions'],'before_bounds_m':old['bounds'],'after_bounds_m':r['bounds'],'before_components':len(old['component_names']),'after_components':len(r['component_names']),'provenance':'See explicit parameter/constructor changes in revision_evidence, revision_measurements and v3_changes. Bounds changes from corrected rod rotation and inferred procedural foliage are not claimed as direct measurements.','evidence':evidence})
save('analysis/object_adjustment_ledger.json',{'meaning':'All changed logical-object bounds/dimensions, after final rebuilt artifacts. No new render/raycast. Context residuals use unchanged input masks.','objects':changes})
limitations=[
 'M2-I06 LIMITED: pendant13 foreground correction is supported in33/129 and reduces129 lamp residual from+3.382m to-0.074m. Other distant33/129 correspondences are tentative;82/108 silhouette ordering and missing/overlapping lamps remain visibly wrong. No claim of complete lamp recovery.',
 'M2-I07 LIMITED: desk RGB silhouette fit uses33/108/118/129 (<3px front-corner errors), while own DA3 desk signs conflict.129 residual worsens to about+1.81m as33 improves to about-1.48m. End-wall y15.15m retained;33 roughly-2.62m versus129 positive residual; native scale/cameras unchanged.',
 'M2-I08 LIMITED: upholstery shapes/yaws, plant morphology, bowl weave, floor dash pattern, mirror reflections, wall grain and lighting remain approximations. Packed floor texture is visibly too subdued; GLB procedural bump materials may simplify.',
 'M2-I09 input uncertainty: selected DA3 windows jump greatly at21/22 and167/168 with nearly unchanged native poses and RGB;175 predicts very short depth. These observations are retained without camera edits, depth scaling or masking. Native trajectory accuracy is not certified.',
 'Service aperture1.05x2.24m is statically clear into a bounded inferred1.5m vestibule. Hidden connectivity, physics and material/thickness parameters are inferred. Closed exterior glazing deliberately blocks both entrance door pairs; no traversal claimed in their closed state.',
 'Small feet/inset support offsets and remaining silhouette/position conflicts remain visual limitations. No full physics or navigation simulation was run.'
]
manifest.update(status='ready_for_independent_review',quality_status='LIMITED',revisions=3,checking_render_count=30,input_bvh_pass_count=3,author_phase='final_candidate',unresolved_issues=limitations,scene_sha256=sha('scene.blend'),glb_sha256=sha('scene.glb'),technical_validation='Author checks PASS; pending independent final review',input_bvh_pass_directories=[r['directory'] for r in full],author_repair_notes='author_repair_notes.md')
assert manifest['input_packet_sha256']==hashlib.sha256((I/'packet.json').read_bytes()).hexdigest();assert sha('cameras.json')==sha('versions/v1/cameras.json')
save('modelling_manifest.json',manifest)
notes={33:'Rod spikes removed; wall seams backed. Pendant foreground closer to source silhouette; far hanging-lamp arrangement and end-wall depth remain inconsistent. Far seat group too boxy; patterned floor subdued.',61:'Flat mirror discs now lower/wider with ten measured circles; source silhouette broadly reproduced. No seam or portal misses. Seat shared solids no longer intersect but backs remain too high/blocky.',74:'Mirror fit and open service aperture visible; bounded returns give real depth. Recess corner closer to source. Foreground chair shape and lamp rim/profile remain approximate.',82:'V3 restores visible recess return panels after v2 backing-side bug. Major pendant correspondence/order errors remain: some source lamps absent at matching locations. Plant shapes coarse despite fixed branching.',91:'V3 restores near-wall panels; no thin depth leaks. Planters same two assemblies; foliage and near-end lamps incomplete. Floor/lighting weaker than source.',100:'Desk intrusion largely removed while keeping source-camera projection. Window door frames thicker, still too stylized. Lamp ordering remains imperfect.',108:'Desk front-left silhouette aligns better; source planters/seat positions still differ. Floor reflections overly smooth and lamp shape/order unresolved.',118:'Desk improved but own DA3 discrepancy persists; column and plants remain approximate. No shell-gap misses.',129:'Dominant foreground pendant moved into correct source location. Far lamps remain partly mismatched; seated forms and planters simplified. Desk DA3 residual worsens despite RGB corner agreement.',155:'Forward view confirms corrected rods and supported shell; source pattern, seating backs and vegetation still approximate. End-wall prediction conflict remains pronounced.'}
inspection=[]
for v in [2,3]:
 for i in fixed:
  inspection.append({'version':v,'sample_index':i,'comparison_sheet':f'checks/v{v}/{i:04d}_comparison.jpg','actually_inspected':True,'notes':notes[i] if v==3 else ('V2: '+notes[i]+(' Backing incorrectly covered near/return panels; repaired in v3.' if i in [82,91] else ''))})
save('analysis/repair_visual_inspection.json',{'role':'author actual comparison inspection','records':inspection})
issues=[
 {'id':'M2-I01','author_status':'records_complete','response':'Initial evidence retained; two new versions and exactly two additional full180 passes; budgets verified. Final author records and snapshots retained.'},
 {'id':'M2-I02','author_status':'repaired_author_validated','response':f"All{len(audit['rod_endpoint_checks'])} requested rod endpoints checked; maximum error{audit['maximum_rod_endpoint_error_m']:.9g}m. Mode assignment fixed before quaternion."},
 {'id':'M2-I03','author_status':'repaired_author_validated','response':'All1577 closed Blender and GLB components have positive volume, no near-zero triangles. Chair bevel removed; desk counter bevel newly caught in v2 removed in v3. Open bowls and foliage are intentionally excluded from closed-volume claims.'},
 {'id':'M2-I04','author_status':'repaired_author_validated','response':'Continuous structural backings split at precise apertures; open service vestibule and split collision proxies. Static tested crossing box clear; closed facade state explicitly blocks exterior entrances.'},
 {'id':'M2-I05','author_status':'repaired_author_validated','response':'Seat center/radius/yaw preserved; explicit Voronoi shared boundaries clipped with6mm pairwise gap. Convex footprint intersection test is zero for all seat pairs; colliders use matching footprint prisms.'},
 {'id':'M2-I06','author_status':'LIMITED_after_measured_repair','response':limitations[0]},
 {'id':'M2-I07','author_status':'LIMITED_after_measured_repair','response':limitations[1]},
 {'id':'M2-I08','author_status':'LIMITED_after_appearance_repair','response':limitations[2]},
 {'id':'M2-I09','author_status':'uncertainty_documented','response':ev['outlier_interpretation']}
]
report={'role':'M2 revision AUTHOR, not independent reviewer','status':'ready_for_independent_review','quality_status':'LIMITED','final_version':3,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_hashes':{'scene.blend':sha('scene.blend'),'scene.glb':sha('scene.glb'),'build_scene.py':sha('build_scene.py'),'layout.json':sha('layout.json'),'cameras.json':sha('cameras.json'),'input_packet':manifest['input_packet_sha256']},'budget':{'full_scene_versions':3,'paired_views':30,'supplemental_paired_views':0,'full180_input_bvh_passes':3,'limit_versions':5,'limit_paired_views':50,'limit_full180_passes':3},'build':'Both v2/v3 built from scratch by build_scene.py from layout and unchanged cameras, factory startup, two CPU threads; checks CPU Cycles12samples640x480','no_geometry_change_after_final_pass':True,'full_pass_geometry_explanation':'input_v2 checks major-repair v2. input_final checks v3 after counter-bevel removal and hidden backing-side fixes. They are distinct geometries; no fourth pass.','review_issues':issues,'parameter_and_residual_evidence':['analysis/revision_measurements.json','analysis/revision_evidence.json','analysis/v3_changes.json','analysis/object_adjustment_ledger.json'],'paired_checks':paired,'full_input_checks':full,'validation_paths':['checks/author_geometry_audit.json','checks/author_glb_geometry_audit.json','checks/artifact_inspection.json','checks/glb_load.json'],'unresolved_issues':limitations,'independent_review':'Initial review retained untouched under independent_review. Final candidate must be reviewed independently. Author has not frozen or self-certified independent review.'}
save('author_repair_notes.json',report)
md=['# M2 author repair notes — final candidate v3','',f"Status: ready for independent review. Visual quality **LIMITED**. This is an author report, not independent certification or freeze.",'',f"- Blender SHA256: `{sha('scene.blend')}`",f"- GLB SHA256: `{sha('scene.glb')}`",'- Budget used: 3 versions, 30 exact paired views, 0 supplemental views, exactly 3 full 180-frame BVH passes.', '- Full passes: `checks/input_v1`, `checks/input_v2`, `checks/input_final`. The latter two check v2 and v3 respectively; no geometry changes follow the final pass.', '- All 180 camera records and rigid scale1 transform preserved. Camera file bytes equal v1; public projection validated by paired tool; original domains identical across versions.', '', '## Review responses','']
for r in issues:md += [f"**{r['id']} — {r['author_status']}**. {r['response']}",'']
md+=['## Concrete measured changes','',f"Reception center: {meas['desk']['before']['center']} → {meas['desk']['after']['center']}; dimensions {meas['desk']['before']['dimensions']} → {meas['desk']['after']['dimensions']}. Measured front corners in RGB33/108/118/129 agree within3px. This improves100 intrusion but worsens129 DA3 agreement; signs are retained below.",'',f"Recess start y:8.0 → {L['bounds']['recess_start_y']:.6f}m from RGB61/74/82 ray-plane constraints; values7.070/7.221/7.297m disagree, median used. Window/side/end planes, floor, global transform and scale unchanged.",'','All fifteen pendant centers and diameters, ten mirror discs, exact before/after layout values and each changed logical-object dimension/bound are recorded in `analysis/revision_measurements.json`, `analysis/revision_evidence.json` and `analysis/object_adjustment_ledger.json`. Shared-seat cuts, backing dimensions, inferred portal returns, frame thicknesses, foliage counts, cap shading and lighting/material changes are explicitly listed. V3 changes are in `analysis/v3_changes.json`. No unmeasured hidden dimension is presented as certain.','','## Spatial residual evidence','', 'Signed residual means model optical Z minus own predicted DA3, never ground truth. The original input domain is preserved. These boxes are diagnostics, not new validity masks.','', '| Region / frame / original RGB box | v1 signed median m | v3 signed median m |','|---|---:|---:|']
for r in ev['regions']:
 if r['name'] in ['reception_33','reception_129','desk_intrusion','light_d_129','wall_end_33','wall_end_129','open_passage','mirror_cluster']:
  md.append(f"| {r['name']} / {r['frame']} / {r['rgb_box']} | {r['v1']['signed_median_m']:.3f} | {r['v3']['signed_median_m']:.3f} |")
md+=['','All62 regional records and before/after context for every changed object are available in the JSON evidence. Technical normals/endpoint changes are construction corrections, not depth-score optimization.','','## Checks and limits','']
for r in paired:md.append(f"- v{r['version']}: all ten required comparisons produced and inspected; own-input MAE {r['aggregate_input_consistency']['mae_m']:.6f}m, valid coverage {r['aggregate_input_consistency']['valid_coverage']:.6%}.")
for r in full:md.append(f"- {r['directory']}:180frames, own-input MAE {r['aggregate']['mae_m']:.6f}m; same reference arrays/domain as the other passes.")
md+=['','Aggregate values are descriptive only. Spatial conflicts and RGB failures remain, especially far pendant correspondences in82/108, seat silhouette/yaw, sparse procedural plant form, end-wall input disagreement and floor/wall appearance. The input outlier investigation reads existing native packet poses, DA3 arrays and saved v1 model arrays; discontinuities align with DA3 selected-window changes, not large pose jumps. No camera correction, depth rescale or mask trimming was performed.','','Validation: 65semantic IDs own1602meshes in both artifacts.1577 closed components have outward positive volume; no near-zero triangles. Rod endpoints agree within1.50micrometres. Shared-seat solid footprint intersections are zero. The1.05×2.24m service aperture is statically clear into the bounded1.5m inferred vestibule. Exterior door pairs remain explicitly closed with blocking facade proxies. No claim of a full navigation/physics simulation.','','Rebuild with `build_scene.py` (factory startup, threads2) using the retained `layout.json` and `cameras.json`; the script never reads a saved blend. The generated floor texture is packed and embedded in GLB. See `revision_access_log.json` and appended `input_access_log.json` for scoped author access records. Existing independent review files were only read, never rewritten.','']
(R/'author_repair_notes.md').write_text('\n'.join(md))
iteration=read('iteration_log.json');iteration['versions']=[r for r in iteration['versions'] if r['version']==1]
for v in [2,3]:
 iteration['versions'].append({'version':v,'action':'Main measured/technical repairs' if v==2 else 'Remove counter bevel degeneracy, correct backing side, smooth seat sides and exportable floor texture','parameter_snapshot':f'versions/v{v}/layout.json','build_snapshot':f'versions/v{v}/build_scene.py','paired_check_count':10,'paired_samples':fixed,'all10_comparisons_actually_inspected':True,'visual_inspection_records':'analysis/repair_visual_inspection.json','full180_input_pass':'checks/input_v2' if v==2 else 'checks/input_final','scene_sha256':sha(f'versions/v{v}/scene.blend'),'geometry_changes_evidence':report['parameter_and_residual_evidence'],'review_status':'Author repaired candidate; independent final review pending'})
save('iteration_log.json',iteration)
inv=read('analysis/object_inventory.json');inv['semantic_objects']=objects;inv['current_version']=3;inv['revision_note']='Mirror grouping now10discs, service_door_1 now open passage; same65logical IDs. Input inventory otherwise retained.';save('analysis/object_inventory.json',inv)
measurements=read('analysis/measurements.json');measurements['revision_evidence']=report['parameter_and_residual_evidence'];measurements['current_version']=3;measurements['uncertainty']=limitations;save('analysis/measurements.json',measurements)
cc=read('analysis/camera_checks.json');cc['version']=3;cc['paired_checks_v1_retained']='versions/v1/analysis/camera_checks.json';cc['paired_checks']=[{'sample_index':i,'comparison_sheet':f'checks/v3/{i:04d}_comparison.jpg','actually_inspected':True,'notes':notes[i],'input_consistency':read(f'checks/v3/{i:04d}_report.json')['input_consistency']} for i in fixed];cc['native_camera_file_unchanged_from_v1']=True;cc['all_check_domains_unchanged']=True;save('analysis/camera_checks.json',cc)
# Final snapshot additions never overwrite generic pre-check snapshots.
for f in ['colliders.json','floor_pattern.png','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json','analysis/rod_requests.json','checks/author_geometry_audit.json','checks/author_glb_geometry_audit.json','checks/artifact_inspection.json','checks/glb_load.json']:
 dst=R/'versions/v3'/f;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/f,dst)
save('versions/v3/finalized_manifest.json',manifest)
print(json.dumps({'status':report['status'],'hashes':report['artifact_hashes'],'budget':report['budget'],'full_reports':[r['directory'] for r in full],'object_change_count':len(changes)},indent=2))
