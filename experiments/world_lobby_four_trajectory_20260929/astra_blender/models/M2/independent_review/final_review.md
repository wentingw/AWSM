# M2 independent final review — LIMITED

Reviewer: `gpt-6-astra`  
Scene SHA256: `c19f33ec434bbcf89137e67d81c283b9adfd48f42e993d8b29d63e08318f79a6`

Major construction repairs verified, but prominent multi-view appearance and projection defects remain. Technically reviewable for honest limited-quality evaluation.

No technical corruption, absent required artifact or evidence of unauthorized input was found. Review is complete. Candidate can proceed to limited-quality evaluation after the coordinator checks the exact hash; this is not a high-fidelity approval.

## Initial issue resolution

| Issue | Resolution | Evidence |
|---|---|---|
| M2-I01 | FIXED | Backing moved behind the near-end panels. Frame 90 now shows pale jointed panels. Repeated ray hits wall_near_end__panel_016 at y=-2.444999933 rather than backing. |
| M2-I02 | FIXED_WITH_LIMITATION | Unsupported door leaf removed; door_side_0 is an open_passage with jamb/header/threshold component colliders. Repeated centre ray is unobstructed over 1.2 m; other closed door remains present. Original frame 75 confirms an aperture. Final frame 90 opening has weak visual contrast. No full passage-connectivity or clearance certification. |
| M2-I03 | FIXED | Clipped modular cushion boundaries replace overlapping disks. Repeated evaluated-mesh surface intersection checks find no padded-seat intersections; black overlap seams are absent in the fixed final comparisons. Remaining silhouette fit is tracked in I04. |
| M2-I04 | PARTIALLY_FIXED | Frame 135 now includes the foreground table at lower left and a seat at the bottom edge. Far seating/table remain too broad and displaced, particularly frames 0,45,135; table_far remains too far left relative to source in frame 135. Backrests and spacing still differ. Cameras remain supplied native poses under the declared rigid transform. |
| M2-I05 | FIXED_WITH_LIMITATION | Mirror cap normals are planar within 0.028 degrees in repeated check. Final frames 45/135 no longer show the original severe segmented cap warping. Cluster projection and reflected content still differ from source; planar shading repair does not verify exact placement or reflection fidelity. |
| M2-I06 | UNRESOLVED | Material/exposure changes are present, but every fixed final view still loses the source structured warm floor reflections. Broad smooth pale rings dominate the inset, particularly frame 90. Walls/glazing retain weak contrast and different grain/light response. Individual physical causes have not been isolated. |
| M2-I07 | PARTIALLY_FIXED | Topiary crowns are now dense; yellow stems are narrower and grass geometry arches. Final yellow planting is still sparse, tall and twig-like compared with dense branching flowers, especially frames 45/90/135; grass envelopes and pot proportions remain mismatched, especially grass_wall_mid at frame 135. |
| M2-I08 | PARTIALLY_FIXED | Explicit relief cells were added and several pendant positions changed, but the source constellation is not recovered. Frame 45 still has a clipped upper-left model pendant versus a fully visible source pendant; frames 0/135/179 show different size, spacing and overlap. Relief reads much flatter than source. |
| M2-I09 | FIXED | Seat, coffee-table and specified grass-pot support gaps are below 3e-9 m in current bounds, which independently match evaluated geometry within 4e-9 m. Yellow planter bottoms penetrate inset by about 0.015 m; this is a minor residual overlap, not a remaining floating-support gap. |

## Residual findings

- **M2-I04 (medium) — table_far, seat_far_01, seat_near_01, seat_near_02, seat_near_03, table_near**, frames [0, 45, 135, 179]: Frame 135 now includes the foreground table at lower left and a seat at the bottom edge. Far seating/table remain too broad and displaced, particularly frames 0,45,135; table_far remains too far left relative to source in frame 135. Backrests and spacing still differ. Cameras remain supplied native poses under the declared rigid transform. Action: Fit table dimensions and seating centres/backrest orientations to several source views jointly, especially 45 and 135, retaining native metric scale and supplied cameras. Use the existing measured landmarks with their uncertainty; do not globally rescale the scene or tune only the stationary endpoint. Check these silhouettes again after the intersection repair.
- **M2-I06 (high) — floor_inset, floor_stone, wall_mirror, wall_reception, glass_facade**, frames [0, 45, 90, 135, 179]: Material/exposure changes are present, but every fixed final view still loses the source structured warm floor reflections. Broad smooth pale rings dominate the inset, particularly frame 90. Walls/glazing retain weak contrast and different grain/light response. Individual physical causes have not been isolated. Action: Tune reflection roughness/normal relief and lighting/exposure against the existing fixed comparisons. Restore the observed floor reflection structure through material and lighting behavior, retaining honest uncertainty about its exact cause. Preserve wall grain and dark architectural accents. Do not bake source-view imagery into the geometry or use camera-dependent fixes.
- **M2-I07 (medium) — planter_yellow_left, planter_yellow_right, tree_reception_left, tree_reception_right, grass_window_mid, grass_wall_mid**, frames [0, 45, 90, 135, 179]: Topiary crowns are now dense; yellow stems are narrower and grass geometry arches. Final yellow planting is still sparse, tall and twig-like compared with dense branching flowers, especially frames 45/90/135; grass envelopes and pot proportions remain mismatched, especially grass_wall_mid at frame 135. Action: Prioritize overall canopy height, width, density and occlusion before species-level detail: reduce yellow leaf width and tune branching envelopes, densify rounded topiary crowns, and add arch/variation to grass blades. Keep foliage colliders conservative but document their approximation.
- **M2-I08 (medium) — pendant_00 through pendant_20**, frames [0, 45, 90, 135, 179]: Explicit relief cells were added and several pendant positions changed, but the source constellation is not recovered. Frame 45 still has a clipped upper-left model pendant versus a fully visible source pendant; frames 0/135/179 show different size, spacing and overlap. Relief reads much flatter than source. Action: First reconcile pendant centre projections, diameter and suspension heights across fixed views; then improve woven relief within budget. Preserve stable pendant IDs and distinguish measured placement constraints from inferred details. If fine weave is deferred, retain it explicitly in final limitations.
- **M2-F01 (low) — iteration_log.json, input_access_log.json, analysis/camera_checks.json**, frames records: iteration_log declares one input-consistency pass, but current checks/input_v2/report.json is a second 180-frame pass tied to final hash. Access log script hash for build_scene.py is stale after repair and does not list all v2 review/repair activity. camera_checks visual assessment still describes the repaired dark-wall defect. Manifest status ready_for_final_review is appropriate to the stage but differs from the generic literal ready_for_independent_review convention. Action: Reconcile final provenance/budget records with both completed passes and current script hash; mark old visual assessment as initial-only. This review records two observed passes; no budget violation found.
- **M2-F02 (low) — planter_yellow_left, planter_yellow_right**, frames [0, 45, 90, 135, 179]: Yellow planter bases extend approximately 0.015 m into floor_inset. Not assessed as a severe visible defect. Action: Retain as an explicit minor intersection limitation or align base/floor if further author work is undertaken.

## Verification and scope

- Directly inspected six original contact sheets, six original RGBs including all fixed views, and five actual final author comparisons.
- Generic Blender inspection PASS: 1664 mesh objects, 301090 triangles, finite mesh coordinates, no missing image dependencies.
- 70 semantic objects cover all 1664 meshes exactly once; evaluated bounds agree within 3.73e-9 m. Read associated colliders and provenance/evidence records.
- 180 camera transforms agree with supplied packet under rigid unit-scale model transform within 1.15e-6; intrinsics, indices and timestamps match.
- Repeated actual artifact wall/door rays, evaluated padded-seat intersection tests and mirror cap normal measurements; support record bounds independently agree with evaluated meshes.
- Actual scene uses CPU Cycles, 12 samples, 640x480, four threads, unit scale 1. GLB import PASS and component names match semantic records.
- Packet and all five fixed RGB/NPZ hashes match. Checked depth metadata and current existing input-only consistency report tied to exact candidate hash; no additional full-input pass.
- Read final repair code/notes and build log; observed two versions, ten checking renders and two input-only passes (iteration log pass count stale).
- Recomputed actual scene hash after checks and before writing review; no geometry/build changes.

Zero additional renders and zero additional full-input passes. Observed totals: 2 versions, 10 renders, 2 input-consistency passes; all below limits. The stale declared pass count is recorded above.

Current input-only fixed-view MAE in metres: 0: 0.646, 45: 0.561, 90: 0.428, 135: 0.521, 179: 5.917. These compare the model with supplied predicted depth, not GT.

## Limitations

- Final review of this exact M2 hash only; no GT, held-out, other-method, parent-plan or historical scene access. No subagents.
- No extra renders. Existing author comparisons were inspected and matched numerically to source RGB and final render PNGs within ordinary JPEG differences (mean absolute byte differences 1.15–1.76). Build logs and matching candidate checks support association; renders were not independently reproduced.
- Targeted checks reuse inspected author verification logic executed by the reviewer on the actual current artifact. They test padded-seat surface intersections, selected rays and cap normals; they do not establish exhaustive collisions, duplicates, topology, watertightness or passage connectivity.
- GLB imported successfully with all expected mesh names; material/render parity with Blender was not independently rendered.
- No evidence of unauthorized input found in scoped declarations/current code. This is not an OS-level forensic proof of author access.
- Supplied depth is predicted input and conflicts with stable RGB: independently read frame 179 median 0.778 m versus roughly 5.6–5.8 m in the other fixed frames. Current input-only MAEs are recorded without treating them as GT accuracy or using them to excuse visual defects.
- Hidden backs, thickness, materials, lighting, fine plant/pendant structure and physical coefficients are inferred. Furniture/foliage AABB colliders remain approximations.
- Author repair intent is documented in analysis/patch_v2.py, build_scene.py and checks/repair_verification_v2.json; no separate comprehensive issue-by-issue repair narrative was present in the discovered files. Final resolution above is the reviewer assessment.

Exact paths read and command purposes: [final_input_access_log.json](final_input_access_log.json). Evidence: [artifact inspection](final_artifact_inspection.json), [targeted geometry checks](final_targeted_checks.json), [record and input checks](final_record_checks.json). Full machine-readable result: [final_review.json](final_review.json).
