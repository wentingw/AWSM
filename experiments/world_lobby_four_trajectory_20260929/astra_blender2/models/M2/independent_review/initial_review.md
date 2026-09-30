# M2 independent initial review

**Status: BLOCKED** — four technical geometry blockers; visual quality LIMITED. Review complete.

Reviewer: `gpt-6-astra`; independent fresh context. Initial v1, not final certification.

Blend SHA256: `00be0f90eff6faa1de71317206e9922f5396a9de5291f9e8fca7960bc8c24b2c`
GLB SHA256: `e660a8f6013441b904ef4089305cff6770027d3422e2df2a7b18b4d83b5ed05a`

Inspected all six contact sheets covering 180 frames, all ten existing fixed paired comparison sheets, full-resolution source RGB 74/108/129, ten model/input depth and residual arrays, the existing 180-frame input pass, actual Blender/GLB geometry, and the author evidence records. No new render or input raycast; only this review directory was written.

## Verified

- One version, exactly 10/50 paired views. All fixed samples and current/snapshot model hashes match; RGB/depth hashes, resampled inputs, masks and residual arrays verify.
- All 180 cameras exactly equal rigid `X @ packet pose`; scale 1, determinant 1 and original intrinsics unchanged. Saved Blender projection error below 0.00004 px; units are meters.
- Both artifacts are readable and finite: 65 semantic IDs,1414 meshes,151218 triangles. Every mesh is accounted for; GLB/Blender bounds agree within 0.5 micrometers.
- One complete180-frame input pass matches the current model. The manifest now correctly reports 1. All required initial evidence records arrived and were read before closing; the earlier missing-record concern is resolved.
- All 374 declared author read paths are within allowed scope. No leak was found in inspected records; historical completeness of self-reported logs is not independently provable.

## Findings

### M2-I01 — INFO: Required author records and initial-pass accounting completed during review

Objects: author evidence records, modelling_manifest. Samples: 33, 61, 74, 82, 91, 100, 108, 118, 129, 155.

All five previously absent records arrived before review completion and were read. Inventory, plane/region/light records match the inspected artifacts; the camera checks list all ten comparisons and spatial residuals; iteration records acknowledge major initial faults. The corrected manifest now says1 full input pass. The374 declared access paths are within allowed scope. Logs are author declarations, not an independently witnessed historical trace.

**Action:** Retain these records and log each subsequent repair/version. Reuse the existing initial pass; complete exactly two further full 180-frame passes in the major-repair and final phases.

Evidence: `input_access_log.json`, `iteration_log.json`, `analysis/object_inventory.json`, `analysis/measurements.json`, `analysis/camera_checks.json`, `modelling_manifest.json`, `independent_review/late_author_records_audit.json`.

### M2-I02 — BLOCKER: Rod construction discards the requested orientation

Objects: pendant_00..14 radial ribs, plant stems, coffee-table ribs, floor-lamp legs, wall_emblem horn_horizontal. Samples: 33, 74, 82, 100, 108, 118, 129, 155.

pendant_00__radial_0 is vertical instead of the endpoint direction; angular error 62.5226 degrees. Paired images show hanging vertical spikes, vertical plant stems disconnected from the intended leaf paths, and absent horizontal emblem segments.
rod() assigns rotation_quaternion before switching rotation_mode to QUATERNION; actual saved transforms are vertical.

**Action:** Set rotation_mode before assigning the endpoint quaternion. Verify world-space cylinder endpoints equal requested endpoints for one radial rib, stem, table rib and emblem segment; rebuild and use the next budgeted ten-view set.

Evidence: `build_scene.py`, `independent_review/blender_geometry_audit.json`, `checks/v1/0082_comparison.jpg`, `checks/v1/0129_comparison.jpg`.

### M2-I03 — BLOCKER: Seven closed mesh components have inward winding

Objects: lounge_seat_01__curved_back, lounge_seat_02__curved_back, lounge_seat_05__curved_back, lounge_seat_07__curved_back, lounge_seat_08__curved_back, lounge_seat_10__curved_back, reception_desk__faceted_body. Samples: 33, 61, 74, 100, 108, 129, 155.

All seven are closed with negative signed volume: chair backs about -0.02789/-0.03215 m^3 and desk body -2.48302 m^3. The same signs survive GLB export. Six beveled backs also contain 1-2 near-zero-area faces. Open foliage and bowl surfaces were excluded from the closed-volume diagnosis.

**Action:** Correct custom face winding outward for the chair backs and desk; remove bevel degeneracies. Confirm positive volume and outward normals on closed components in both artifacts. Finite unit-length normals alone do not establish orientation.

Evidence: `independent_review/blender_geometry_audit.json`, `independent_review/glb_mesh_audit.json`.

### M2-I04 — BLOCKER: Wall joints leak through the shell and portal proxies cover openings

Objects: end_wall, near_wall, mirror_wall, recess_wall, service_door_1, glazed_facade collision proxy. Samples: 33, 61, 74, 82, 108, 129.

Panelwall leaves 22 mm vertical and 25 mm horizontal gaps with no backing, visible as black optical-Z lines. Sample61 has 4,508 invalid-domain pixels; sample74 has 2,325, including the doorway slit and wall gaps. RGB74 right edge (roughly x1160:1280,y315:540 at 1280x960) shows an open dark passage; service_door_1 projects into that region as a flat door/slit. The single mirror_wall AABB spans both nominal door openings; glazed_facade is likewise one continuous pane and box behind entrance frames. Closed entrance glazing itself is consistent with the source closed-door state.

**Action:** Back panel seams with semantic wall geometry and define apertures independently of panel-center rounding. Reconstruct the observed open service passage with bounded returns; split the wall collision proxy around it. Keep closed entrance leaves explicitly closed and do not claim traversability through their continuous proxy. Record a passage-clearance check.

Evidence: `build_scene.py`, `colliders.json`, `checks/v1/0061_comparison.jpg`, `checks/v1/0074_comparison.jpg`, `independent_review/support_portal_input_audit.json`.

### M2-I05 — BLOCKER: Independent solid seat bases substantially interpenetrate

Objects: lounge_seat_01/02, lounge_seat_02/03, lounge_seat_04/05, lounge_seat_06/07, lounge_seat_07/08, lounge_seat_09/10. Samples: 33, 61, 74, 129, 155.

Equal-height solid cylindrical bases overlap radially by 0.132 m (01/02), 0.174 m (02/03), 0.210 m (04/05), 0.110 m (06/07), 0.107 m (07/08), and 0.189 m (09/10). This follows actual base radii and center distances, not only conservative AABB overlap. Small foot/inset penetrations of about 1.75 cm were not treated as major support defects.

**Action:** Use source33/129 for the far cluster and61/155 for the near cluster to set touching or separated contours. If seats are a joined modular assembly, model the shared boundaries explicitly; preserve semantic IDs and regenerate colliders.

Evidence: `layout.json`, `independent_review/scene_inspection.json`, `independent_review/support_portal_input_audit.json`.

### M2-I06 — HIGH: Pendant placement fits one view poorly across other fixed views

Objects: pendant_00..14. Samples: 33, 82, 100, 108, 118, 129.

Centers are measured from sample33 only despite evidence_frames [33,129]. Sample129 RGB region [597,83,724,120] at the large foreground lamp has model-minus-input median +3.382 m; the render places its dominant foreground lamp farther right. Sample82/108 show different silhouettes and ordering. Rod corruption is a separate defect.

**Action:** After fixing rods, establish actual matching lamp silhouettes in33/82/108/129, measure centers/diameters from multiple views, and log signed residuals and conflicting predictions. Keep native cameras/scale fixed and label any unresolved lamp correspondences inferred.

Evidence: `layout.json`, `make_layout.py`, `checks/v1/0082_comparison.jpg`, `checks/v1/0108_comparison.jpg`, `checks/v1/0129_comparison.jpg`, `independent_review/records_depth_audit.json`.

### M2-I07 — HIGH: Reception and end-wall placement has visible errors and conflicting depth evidence

Objects: end_wall, reception_desk. Samples: 33, 100, 108, 118, 129, 155.

At sample100 the desk occupies floor area left of the source desk: RGB box [920,580,1080,780] has median signed residual -2.129 m. Desk measurement regions disagree: sample33 -2.380 m versus129 +0.943 m. End wall [450,250,900,340] in33 is -2.627 m versus129 end-wall region +0.923 m. The author already labels the selected wall y=15.15 as a compromise; DA3 is prediction, not truth.

**Action:** Constrain desk silhouette and end-wall/recess boundaries jointly in100/108/118/129 and33. Record region-specific alternatives and preserve the opposite residual signs; do not translate the whole shell simply to lower aggregate depth error.

Evidence: `checks/v1/0033_comparison.jpg`, `checks/v1/0100_comparison.jpg`, `checks/v1/0129_comparison.jpg`, `analysis/plane_observations.json`, `analysis/object_depth_regions.json`, `independent_review/additional_fixed_region_audit.json`.

### M2-I08 — MEDIUM: Distinctive appearance and some object silhouettes remain simplified

Objects: mirror_installation, entrance_doors_0/1, floor_inset, planter_west/east, materials and lighting. Samples: 33, 61, 74, 91, 100, 108, 129, 155.

The mirror grouping is too compact/high relative to the wall in61/74, entrance frames are much thinner in108, source patterned dark floor is replaced by uniform noisy gloss, wood walls are washed out, and branching greenery is sparse. Source reflections were correctly not duplicated as furniture.

**Action:** Prioritize mirror outline/location and door-frame thickness from RGB; then approximate the floor pattern, wood tone, light balance and foliage fullness. Keep shader, hidden form and plant detail explicitly inferred. Remaining appearance differences can be LIMITED after technical blockers are resolved. Flatten cylinder cap shading on mirror discs and table tops; the source objects have planar reflecting faces, while the paired render gives curved reflections.

Evidence: `checks/v1/0061_comparison.jpg`, `checks/v1/0074_comparison.jpg`, `checks/v1/0108_comparison.jpg`, `inputs/M2/rgb/0074.png`, `inputs/M2/rgb/0108.png`, `inputs/M2/rgb/0129.png`.

### M2-I09 — HIGH: Full-input outliers need an uncertainty record

Objects: native input trajectory and predicted depth consistency. Samples: 21, 22, 167, 168, 175.

The existing full pass has mean absolute input residual 1.501 m, versus0.747 m in the ten paired views. Per-frame MAE reaches12.329/12.331 m at21/22 and11.634/11.628 m at167/168, while contact-sheet RGB remains a similar lobby view. This establishes input/model inconsistency, not its cause. No new raycast or render was run to investigate it.

**Action:** Review these existing per-frame arrays and packet pose/depth metadata and document whether the outliers arise from native input discontinuities, predictions, or geometry. Do not repair them by moving per-frame cameras, rescaling depth, or trimming validity masks; retain unresolved conflicts in the manifest.

Evidence: `checks/input_v1/report.json`, `checks/input_v1/depth.npz`, `independent_review/full_input_array_audit.json`, `inputs/M2/contact_sheets/000_029.jpg`, `inputs/M2/contact_sheets/150_179.jpg`.

## Limits and final review requirements

Residuals mean model minus own predicted DA3 optical Z, never truth. Regional boxes use original 1280x960 RGB coordinates. Mirror/floor reflections were correctly not duplicated as objects. Hidden geometry, plant detail, material and physics remain inferred. Contact/support and collision proxies were inspected statically; no navigation or physics simulation was run.

This is the first independent review; author records describe initial limitations, not completed repairs. A later final review must explicitly revisit **M2-I01 through M2-I09**, read the repair evidence, independently inspect the final candidate, verify exactly three full 180-frame passes (initial/major repair/final), and recheck unchanged cameras/scale and the 5-version/50-view limit. One pass is appropriate at this initial stage.

Full paths read and findings: `initial_review.json`. Reviewer access/actions: `input_access_log.json`. Supporting geometry, GLB, residual, projection, contact and late-record audits are retained alongside them.
