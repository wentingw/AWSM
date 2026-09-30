"""Author evidence report for repaired M1 candidate; never grants independent approval."""
import json,hashlib,math,shutil
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];J=lambda n:json.loads((R/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
fixed=[33,61,74,82,91,100,108,118,129,155]
regions={33:[180,540,1100,950],61:[630,620,1230,950],74:[420,540,1278,950],82:[500,620,1278,950],91:[250,400,1100,950],100:[400,550,1180,950],108:[0,0,1280,960],118:[200,600,1200,950],129:[200,690,1080,950],155:[180,520,1100,950]}
texts={33:'False near divider removed; north lounge and side chairs visible. North furniture still too large/right, mirror disks too exposed; materials and ceiling differ.',61:'Moved side seats now occupy observed right-side seating region and no longer penetrate. North group creates excessive furniture across lower left/centre; mirror landmark/door proportions remain wrong.',74:'Divider now left, consistent direction, but too central/close. Excess north seats cover source open black floor. Metal door remains an overly sharp mirror.',82:'Single planter pair now foreground and side seating to right; shell/door proportions and table depth order still disagree. The inferred single-pair layout is more coherent across directions.',91:'Large near duplicate pair gone. Open floor extends to a single pair, with lower furniture behind it; pair still too wide/near, floor dot density and column differ.',100:'Right half is now open circulation floor. Spurious foreground lamp remains and black floor pattern/door width differ; camera is unchanged.',108:'Severe near partition obstruction unchanged. Source facade is open; median model opticalZ remains0.791m,91.43percent below1m. No camera move or geometry visibility masking used.',118:'Room opens beyond divider and seating shifted left; divider still too far right/near. Source shows broader open floor. Unvalidated trajectory prevents a common fit.',129:'Near false foliage removed; north furniture now at foreground depth but too far right. Conditional table ray-plane fit disagrees by over300px horizontally in this view.',155:'False near divider gone; table/chairs are visible again. Side seating is too far up/right and north lounge somewhat oversized; mirrors too visible.'}
views=[]
for i in fixed:
 a=np.load(R/f'checks/v1/{i:04d}_depth.npz')['model_z_m'];b=np.load(R/f'checks/v2/{i:04d}_depth.npz')['model_z_m'];x0,y0,x1,y1=regions[i];aa=a[y0//2:(y1+1)//2,x0//2:(x1+1)//2];bb=b[y0//2:(y1+1)//2,x0//2:(x1+1)//2];mask=np.isfinite(aa)&np.isfinite(bb)
 stats={'pixel_region_source_1280x960':regions[i],'before_model_z_median_m':float(np.nanmedian(aa)),'after_model_z_median_m':float(np.nanmedian(bb)),'median_signed_model_change_v2_minus_v1_m':float(np.median((bb-aa)[mask])),'interpretation':'Signed change between two model predictions only; NOT residual against measured or predicted input depth','input_signed_depth_residual_m':None,'depth_reference':'N/A: M1 RGB only'}
 views.append({'sample_index':i,'comparison_path':f'checks/v2/{i:04d}_comparison.jpg','comparison_sha256':sha(R/f'checks/v2/{i:04d}_comparison.jpg'),'actually_visually_inspected':True,'model_depth_panel_inspected':True,'saved_depth_array_inspected':True,'observations':texts[i],'regional_self_depth_evidence':stats,'global_model_z_median_m':float(np.nanmedian(b)),'model_z_below1m_fraction':float(np.mean(b<1))})
save('analysis/paired_visual_inspection_v2.json',{'role':'revision author inspection; not independent review','version':2,'quality_status':'LIMITED','views':views})
measure=J('analysis/author_repair/rgb_ray_plane_measurements.json')
changes=[]
def change(id,before,after,frames,why,provenance='inferred; conditional on RGB-only scale and unchanged estimated cameras'):
 changes.append({'id':id,'before':before,'after':after,'evidence_frames':frames,'pixel_regions_source_1280x960':{str(i):regions[i] for i in frames},'rationale':why,'provenance':provenance,'signed_input_depth_residual_m':None,'depth_reason':'N/A for M1; no input DA3 or measured depth','self_depth_evidence':[f'analysis/paired_visual_inspection_v2.json:sample{i}' for i in frames]})
change('north_group_center_m',[3.,10.5],[3.1,7.9],[33,129,155,118],'Move group -2.6m alongY toward foreground in33/129/155 and out of118 open floor; ray-plane table estimates[3.718,7.458],[3.376,7.899],[1.640,6.799] conflict. Joint robust fit table[3.321,7.553] still has379px horizontal error in129; chosen group gives table[3.1,7.3].')
old_offsets=[[-1.05,-.15],[-.85,.72],[0,1.02],[.90,.75],[1.18,-.1]];new_offsets=J('layout.json')['seat_offsets']
change('seat_offsets_both_groups_m',old_offsets,new_offsets,[33,61,74,82,129,155],'Small local spacing corrections avoid interpenetration of retained .47m-radius bodies; shape/count approximate.')
for group,sign in [('north',-1),('south',1)]:
 for j in [1,2,4]:
  old=math.degrees(math.atan2(old_offsets[j][1]*(-sign),old_offsets[j][0]));new=math.degrees(math.atan2(new_offsets[j][1]*(-sign),new_offsets[j][0]));change(f'{group}_seat_{j+1}_back_orientation_degrees',old,new,[33,61,74,82,129,155],'Back follows changed radial seat offset; inferred orientation.')
change('curved_back_caps_and_bevel',{'end_caps':[[0,17,34,51],[16,33,50,67]],'bevel_width_m':.055,'bevel_segments':3},{'end_caps':[[51,34,17,0],[16,33,50,67]],'bevel_removed':True,'normals':'recalculated outward'},[33,61,74,82,129,155],'Fix initial-review inconsistent winding and collapsed evaluated polygon; no smoothing workaround. All8 current curved backs are watertight consistently wound positive-volume GLB meshes.','technical repair; no dimensional evidence needed for winding')
change('divider_rows_y_m',[12.4,5.7],[9.8],[33,82,91,100,108,118,129,155],'Treat opposite-direction pair as one physical pair. Measured conditional front-topY spans8.726–9.688m; chosen near/far faces9.51/10.09 retain two1.95x.58x.66m containers. Four redundant planter/plant IDs removed; retained row0 IDs. ExactY remains uncertain byabout.8m.')
change('south_side_seat_centres_xy_m',[[4.9,3.5],[5.5,3.8],[5.4,2.6]],[[5.5,7.1],[5.5,6.14],[5.2,5.23]],[33,61,74,82,155],'Retain3 observed side seats and resolve nearly coincident bodies by ray-plane measurements in61: seat centres[5.341,6.985],[5.344,6.277],[4.997,5.649].74 supports a seat near[6.034,5.057];82 conflicts, so coordinates remain inferred.')
change('side_seat_supports',None,{'four_legs_each':{'radius_m':.017,'height_m':.13,'center_z_m':.065,'xy_offsets_m':[[-.24,-.24],[-.24,.24],[.24,-.24],[.24,.24]]}},[61,74,82],'Bridge unsupported .10m base to floor; feet overlap insert by.016m as intended contact. Hidden legs are inferred.')
change('side_backrests',None,{'seat_ids':[1,2],'cross_section_z_radius_m':[[.48,.43],[.83,.42],[.85,.35],[.5,.36]],'azimuth_range_radians':[-.85,.85]},[33,61,74,155],'Two side seats show curved backs in61; add closed mesh backs with inferred thickness and exact orientation.')
change('mirror_side_coffee_table',None,{'center_xy_m':[4.2,5.8],'top_radius_m':.60,'top_center_z_m':.43,'top_thickness_m':.048,'support_radius_m':.25,'support_center_z_m':.225,'support_height_m':.42},[33,61,155],'Table visible beside side seats: conditional centres from33/155 approximately[4.686,4.90]/[4.383,4.886], versus61[4.088,6.557]; choose compromise. Third logical table, not mirror reflection.')
change('reception_desk_support',{'base_min_z_m':.10,'support':None},{'plinth_center_m':[4.1,15.15,.055],'plinth_dimensions_m':[2.8,.55,.11],'supported_by':'floor'},[33,108,118,129,155],'Inferred hidden plinth bridges floating counter body; desk body remains unchanged.')
change('floor_inlay_square_halfwidth_m',.032,{'base':.012,'deterministic_multiplier_range':[.75,1.25],'spacing_unchanged_m':[.116,.117]},[33,91,100,118,129,155],'Reduce overly dominant v1 gold squares and restore black floor; exact motif/reflection density remains approximate.')
change('mirror_partition_collision',{'type':'single_AABB','min':[6.7725,3.435,0],'max':[8.,11.065,4.6]},{'type':'COMPOUND','parts':'one tight box per real mesh component','enterable_clear_prism_min':[6.2,3.55,.02],'enterable_clear_prism_max':[7.85,4.3,2.55]},[61,74,82,91],'Keep opening clear while keeping separate north closed door proxy. Finite recess ends at inferred back wall; onward path unobserved. Entire prism and original reviewer probe tested clear against all enabled proxies.','technical proxy repair; existing geometry retained')
change('lathe_mesh_cleanup',{'duplicate_pole_vertices':True},{'weld_tolerance_m':1e-6,'degenerate_edge_tolerance_m':1e-8,'normals':'consistent'},[33,61,74,82,91,129,155],'Weld pole vertices and dissolve numerical degenerate edges without intentionally changing the profiles.','technical mesh repair')
change('appearance',{'world_strength':.45,'exposure':0,'facade_area_watts':450,'ceiling_fill_watts':120,'slat_material':'wall_oak'},{'world_strength':.18,'exposure':-.5,'facade_area_watts':260,'ceiling_fill_watts':65,'slat_material':'slat_wood','wall_oak_RGB':[.30,.275,.225],'wall_gray_RGB':[.25,.255,.245],'ceiling_RGB':[.43,.415,.37],'shade_weave_RGB':[.17,.135,.085],'shade_RGB':[.50,.47,.39],'metal_dark_RGB':[.035,.038,.034],'brass_RGB':[.30,.225,.085],'wall_grain_scale':[2,2,.045]},[33,61,82,100,129,155],'Reduce washed-out walls/fixtures, increase dark slat contrast. Inferred appearance, no calibrated materials/lighting; weave remains too smooth.')
# Every changed logical-object bound/dimension, including incidental seeded plant variation.
old={o['id']:o for o in J('versions/v1/objects.json')['objects']};new={o['id']:o for o in J('objects.json')['objects']};deltas=[]
for oid in sorted(old.keys()|new.keys()):
 a=old.get(oid);b=new.get(oid)
 def compact(o):
  if o is None:return None
  return {k:o[k] for k in ['dimensions','bbox_min','bbox_max','component_names']}
 if a is None or b is None or compact(a)!=compact(b):
  fs=sorted(set((a or b)['evidence_frames'])&set(fixed));deltas.append({'object_id':oid,'before':compact(a),'after':compact(b),'evidence_frames':fs,'pixel_regions':{str(i):regions[i] for i in fs},'provenance':'inferred shape/placement; see named parameter adjustments. Seeded downstream foliage changes after redundant planter removal are incidental inferred plant detail. Tiny differences may be numerical mesh cleanup.','signed_input_depth_residual_m':None})
save('analysis/author_repair/object_parameter_deltas_v1_v2.json',{'version_before':1,'version_after':2,'depth_reference':'N/A for M1','changes':deltas})
save('analysis/author_repair/parameter_changes_v2.json',{'changes':changes,'ray_plane_evidence':'analysis/author_repair/rgb_ray_plane_measurements.json','per_object_before_after':'analysis/author_repair/object_parameter_deltas_v1_v2.json'})
issues=[
 {'id':'M1-I01','author_disposition':'addressed','details':'Pre-existing records were already present at revision-author entry, although absent when initial review was written. Preserved inherited logs and added current access/commands, complete version counts and final ready manifest. Unavailable historical claims remain inherited, not reconstructed as first-hand.'},
 {'id':'M1-I02','author_disposition':'addressed','details':'Corrected cap winding, removed collapsing bevel; all scene evaluated meshes have0 winding errors and0 degenerate faces; all8 curved backs pass GLB closure/winding/volume.'},
 {'id':'M1-I03','author_disposition':'addressed','details':'Repositioned retained side seats and widened local seat offsets; minimum exact radial body clearance across all13 seats is0.051413m. Multi-view pose disagreement remains visual limitation.'},
 {'id':'M1-I04','author_disposition':'addressed','details':'Compound partition proxies preserve opening; full clear prism and[6.85,3.925,1] pass. North metal door remains closed. Recess is finite with no claimed onward route.'},
 {'id':'M1-I05','author_disposition':'unresolved visual limitation','details':'All cameras byte-identical.108 remains91.43percent opticalZ below1m. Moving/removing the common wall solely to clear this incompatible pose is unsupported by61/74/82; no such change made.'},
 {'id':'M1-I06','author_disposition':'partially addressed, LIMITED','details':'Consolidated planters and moved north/side furniture using conditional measurements;33/91/100/155 improve obstruction.61/74 excessive seating and129 horizontal placement conflict remain.'},
 {'id':'M1-I07','author_disposition':'addressed with inferred supports','details':'Added side-seat legs and desk plinth with valid support relations and semantic ownership.'},
 {'id':'M1-I08','author_disposition':'partially addressed, LIMITED','details':'Darker walls/slats and finer floor motif; weave/vegetation/reflections approximate. Scale2.6±.35m door assumption, all180 poses unvalidated.'}]
manifest=J('modelling_manifest.json');manifest.update(status='ready_for_independent_review',revisions=2,checking_render_count=20,input_bvh_pass_count=0,quality_status='LIMITED',final_candidate_version=2,unresolved_issues=[x['id']+': '+x['details'] for x in issues if 'LIMITED' in x['author_disposition'] or 'unresolved' in x['author_disposition']]+['Assumed metric scale, hidden surfaces/thickness/materials/lighting/physics inferred.','South portal leads into an inferred finite recess; onward connectivity unobserved.'],author_repair_notes='author_repair_notes.json',independent_final_review='pending; author does not certify or freeze',input_bvh_requirement='N/A for RGB-only M1; exactly-three-pass rule applies to M2–M4 only')
save('modelling_manifest.json',manifest)
it=J('iteration_log.json');it['versions'][0]['independent_review']='independent_review/initial_review.json; initial BLOCKED';it['versions'].append({'version':2,'stage':'repaired candidate for separate independent review','model_sha256':sha(R/'scene.blend'),'glb_sha256':sha(R/'scene.glb'),'build_from_scratch':True,'build_log':'build_v2.log','parameter_snapshot':'versions/v2/layout.json','parameter_changes':'analysis/author_repair/parameter_changes_v2.json','paired_check_indices':fixed,'paired_check_count':10,'supplemental_check_count':0,'input_bvh_pass_count':0,'self_inspection':'analysis/paired_visual_inspection_v2.json','technical_validation':'checks/author/technical_verification.json','independent_review':'pending','geometry_changes_after_checks':False});it['historical_note']='v1 records inherited; current author did not witness initial failed build or coordinator rendering. Existing local logs/notes preserved. No additional hidden builds/renders in this repair session.';save('iteration_log.json',it)
notes={'method_id':'M1','role':'revision AUTHOR only','final_candidate_version':2,'status':'ready_for_independent_review','quality_status':'LIMITED','scene_blend_sha256':sha(R/'scene.blend'),'scene_glb_sha256':sha(R/'scene.glb'),'camera_sha256':sha(R/'cameras.json'),'camera_file_unchanged_from_v1':True,'input_depth_residuals':'N/A; packet supplies RGB only; no DA3 accessed or invented','input_bvh_passes':0,'total_versions':2,'total_paired_checks':20,'supplemental_checks':0,'issues':issues,'parameter_changes':changes,'object_deltas':'analysis/author_repair/object_parameter_deltas_v1_v2.json','ray_plane_measurements':measure,'actual_comparison_inspection':'analysis/paired_visual_inspection_v2.json','technical_validation':['checks/artifact_inspection.json','checks/glb_load.json','checks/author/geometry_audit.json','checks/author/technical_verification.json'],'no_independent_approval_claim':True,'no_freeze':True}
save('author_repair_notes.json',notes)
md=f'''# M1 repaired candidate v2 — author handoff

Status: ready for independent review. Quality: **LIMITED**. This is an author repair report, not independent approval or freeze.

Rebuilt `scene.blend` and `scene.glb` from empty Blender using `build_scene.py` and `layout.json`. Current scene has85 semantic objects and582 mesh components, with complete unique component_names mapping in both exports. Cameras are byte-identical to v1; all180 retain valid=false/unvalidated status and public intrinsics. No input mask was changed.

## Repairs and verification

- M1-I01: retained inherited v1 records and added the current author access/iteration history; unknown earlier history remains explicitly inherited. Manifest is ready_for_independent_review.
- M1-I02: corrected chair cap winding and removed the collapsing bevel. Evaluated scene has0 inconsistent-winding meshes and0 degenerate-face meshes. All8 current curved backs pass GLB watertightness, winding and positive volume.
- M1-I03: retained3 visually observed side seats, repositioned them and separated all13 seat bodies. Minimum radial body clearance is0.051413m. Exact placements remain inferred from incompatible multi-view camera estimates.
- M1-I04: split partition collision into component boxes. Original reviewer probe and full prism x=[6.2,7.85],y=[3.55,4.30],z=[.02,2.55] are clear of enabled proxies. North door is closed. South recess ends at an inferred back wall; no onward route is claimed.
- M1-I07: added inferred side-seat legs and reception plinth, with support relations and semantic names.
- M1-I06/I08: consolidated4 dividers into2, moved north seating and side seats, added the observed side table, reduced the floor motif and adjusted inferred materials/light levels. Every parameter and actual object-bound delta is recorded in the linked JSON files.

## Actual evidence and limitations

Read all6 contact sheets covering180 input frames; viewed original RGB61/74/82/108/129/155 and all10 actual v1 comparisons before repair. Ran and visualized **all10 exact paired checks for v2**:33,61,74,82,91,100,108,118,129,155. All10 v2 comparison images and saved depth arrays were inspected; see `analysis/paired_visual_inspection_v2.json`. Rendering used CPU2threads,12samples,640x480; no supplemental or unlogged render.

M1 has no DA3/input depth. Signed input-depth residuals are null/N/A. Recorded ray-plane distances depend on assumed camera/height; recorded signed v2-minus-v1 optical-Z changes are model self-comparisons, never reference errors. Three full180 BVH passes apply only to M2–M4: M1 count remains0.

M1-I05 remains severe: sample108 median opticalZ is0.791m and91.43% of pixels are below1m; its preserved estimated camera lies behind the modeled partition.61/74/82 constrain that shared partition, so it was not moved/hidden to clear one incompatible camera. Furniture remains too dense in61/74 and shifted right in129. Planter consolidation improves foreground obstruction in33/91/100/155; no claim of globally accurate reconstruction. All180 poses and2.6±.35m door scale remain unvalidated. Weave, vegetation, materials, lighting, thickness and physics are inferred.

## Review artifacts

- `author_repair_notes.json`: issue-by-issue disposition, parameters, frame/pixel evidence and hashes.
- `analysis/author_repair/parameter_changes_v2.json`: before/after values and measurement rationale.
- `analysis/author_repair/object_parameter_deltas_v1_v2.json`: every changed logical object's bounds, dimensions and components, including incidental seeded plant detail.
- `analysis/author_repair/rgb_ray_plane_measurements.json`: conditional measurements, signed pixel residuals and retained disagreements.
- `checks/author/technical_verification.json`: topology/export, seat clearance, portal, camera/identity and budget assertions.
- `checks/glb_load.json` and `checks/artifact_inspection.json`: provided generic validators both PASS.

Two full versions and20 actual paired views total; snapshots and all prior checks retained. No geometry change after v2 checks. Separate final independent review remains required.

SHA256 scene.blend: `{sha(R/'scene.blend')}`

SHA256 scene.glb: `{sha(R/'scene.glb')}`
'''
(R/'author_repair_notes.md').write_text(md)
# Manifest snapshot originally captured building state; preserve it and retain a separate final metadata snapshot.
D=R/'versions/v2'
for name in ['colliders.json','author_repair_notes.md','author_repair_notes.json','input_access_log.json','iteration_log.json']:
 shutil.copyfile(R/name,D/name)
shutil.copyfile(R/'modelling_manifest.json',D/'modelling_manifest_final.json')
for name in ['artifact_inspection.json','glb_load.json']:
 shutil.copyfile(R/'checks'/name,R/'checks/v2'/name)
print('AUTHOR_NOTES_FINALIZED',notes['scene_blend_sha256'],notes['scene_glb_sha256'])
