# M2 independent initial review

**Status: REQUIRES_FIXES**

Reviewer: `gpt-6-astra`  
Scene SHA256: `81c5104ef79673bbd778ef5c5fcc9145f82ce8545d6e6c09c8d1625f73fdf8c6`

The candidate is readable and semantically organized, but three high-priority construction defects need repair: the near-end wall backing masks its panels, an observed open passage is closed by a door/collider, and far seating cushions substantially intersect. No technical corruption or evidence of unauthorized inputs was found. This is an initial review, not authorization to freeze; the repaired candidate requires final review.

No additional renders or full-input BVH passes were performed. Existing records show one scene version, five completed renders and one input-consistency pass.

[Matched visual evidence crops](evidence_crops.jpg) · [Measured audit](review_audit.json) · [Actual Blender inspection](artifact_inspection.json) · [Mirror normals](mirror_normals.json)

## Actionable findings

### M2-I01 — HIGH — wall_near_end

Evidence frames: 90. Evidence type: `observed_visual_defect_and_measured_geometry`.

The upper near-end wall is a large dark rectangle instead of the pale jointed panels visible in RGB frame 90. A ray from (0,0,3) toward -Y hits wall_near_end__joint_backing at y=-2.425. Its interior face projects 0.020 m in front of the panel interior face at y=-2.445, masking the panels.

**Repair:** Place the backing behind the panels on the exterior side of this wall, accounting for wall orientation rather than applying a fixed positive offset. Preserve the panel joints and recheck frame 90. Update the exported scene and matching bounds/colliders.

### M2-I02 — HIGH — door_side_0

Evidence frames: 66, 75, 90. Evidence type: `observed_source_aperture_and_measured_blockage`.

The opening at the near end of the mirror wall is visibly open in original frames 66 and 75 and appears as a dark opening in frame 90. The model instead supplies a closed brushed-metal door leaf and a solid bounds-box collider. A ray from (3,-0.42,1) toward +X hits door_side_0__door_leaf at x=3.5825. The leaf spans y=-0.875 to 0.035 and z=0 to 1.970 m. The wall itself has a bay, but the inserted door and collider close it.

**Repair:** Represent the observed open passage, remove the unsupported closed leaf, and replace its solid collider with jamb/header components that leave the opening traversable. Infer only the minimum necessary return surfaces and mark unseen passage extent uncertain. Keep the other observed closed metal doors distinct.

### M2-I03 — HIGH — seat_far_03, seat_far_04, seat_far_05, seat_far_06

Evidence frames: 0, 45, 135, 179. Evidence type: `observed_visual_defect_and_measured_mesh_intersections`.

The far seating has black seam patches and merged circular cushion tops absent from the source modular seating. Evaluated world-space mesh overlap checks confirm intersections: seat_far_03/04 have 0.302 m circular penetration, seat_far_04/05 0.341 m, and seat_far_05/06 0.170 m. Smaller cushion intersections also occur in far, near and end groups; all seven measured pairs are in review_audit.json. These are mesh intersections, not merely conservative collider overlaps.

**Repair:** Reconstruct the touching modular cushion outlines with compatible boundaries, or adjust radii/centres to remove interpenetration while matching source silhouettes. Check cushion cap shading and eliminate the black seam patches. Recompute component bounds and colliders after repair; validate the repaired group in all four cited existing views.

### M2-I04 — MEDIUM — table_far, seat_far_01, seat_near_01, seat_near_02, seat_near_03, table_near

Evidence frames: 0, 45, 135, 179. Evidence type: `observed_projection_mismatch`.

Furniture silhouette size and placement remain visibly wrong under the supplied cameras. In frames 0 and 45, the far coffee table and front ottoman occupy noticeably more image width than their source counterparts. Frame 135 is particularly diagnostic: the source foreground contains a table entering from lower left and only the top of a seat near the lower edge, whereas the model places a large chair much higher in the lower centre and loses the table from the corresponding crop. The verified camera transform does not justify a per-frame camera correction.

**Repair:** Fit table dimensions and seating centres/backrest orientations to several source views jointly, especially 45 and 135, retaining native metric scale and supplied cameras. Use the existing measured landmarks with their uncertainty; do not globally rescale the scene or tune only the stationary endpoint. Check these silhouettes again after the intersection repair.

### M2-I05 — MEDIUM — mirror_cluster

Evidence frames: 45, 66, 75, 90, 135. Evidence type: `observed_visual_defect_and_measured_shading_normals`.

The modeled mirrors produce segmented, strongly warped reflections in frames 45, 90 and 135, unlike the coherent planar reflections in the source, especially original frames 66 and 75. Actual mirror mesh caps are smooth-shaded together with their cylindrical sides: cap corner normals deviate approximately 45.875 degrees from the flat face normal. Reflective material is present and no additional reflected room was modeled, but the optical surface shading is incorrect.

**Repair:** Use a flat reflective front face or split/custom normals so all front-face shading normals match the planar mirror normal. Smooth only the rim, retain the reflective material, and verify continuous straight reflected mullions. Recheck the cluster placement as well as its reflection after the normal repair.

### M2-I06 — MEDIUM — floor_inset, floor_stone, wall_mirror, wall_reception, glass_facade

Evidence frames: 0, 45, 90, 135, 179. Evidence type: `observed_appearance_mismatch_with_causal_uncertainty`.

Across every fixed view the model is much paler and flatter than the source. The black inset loses the crisp, structured warm pendant/slat reflections and instead has broad blurred highlights; oak panels lose much of their visible grain and contrast; glazing bars have weak contrast. These are prominent image differences rather than small texture omissions. Material roughness, procedural relief, lighting and exposure may all contribute; their individual effects were not isolated by additional renders.

**Repair:** Tune reflection roughness/normal relief and lighting/exposure against the existing fixed comparisons. Restore the observed floor reflection structure through material and lighting behavior, retaining honest uncertainty about its exact cause. Preserve wall grain and dark architectural accents. Do not bake source-view imagery into the geometry or use camera-dependent fixes.

### M2-I07 — MEDIUM — planter_yellow_left, planter_yellow_right, tree_reception_left, tree_reception_right, grass_window_mid, grass_wall_mid

Evidence frames: 0, 45, 90, 135, 179. Evidence type: `observed_silhouette_and_density_mismatch`.

The yellow plantings are broad leaf-like sprays rather than the fine branching yellow stems in RGB; they are too visually bulky and obscure more seating/reception detail, especially in frame 90. Conversely, the two reception topiary crowns are sparse and translucent instead of the dense rounded crowns visible in frames 0, 45 and 135. Grass clumps read as coarse upright spikes rather than dense arching foliage.

**Repair:** Prioritize overall canopy height, width, density and occlusion before species-level detail: reduce yellow leaf width and tune branching envelopes, densify rounded topiary crowns, and add arch/variation to grass blades. Keep foliage colliders conservative but document their approximation.

### M2-I08 — MEDIUM — pendant_00 through pendant_20

Evidence frames: 0, 45, 90, 135, 179. Evidence type: `observed_projection_and_form_mismatch`.

Pendant centres, apparent sizes and overlaps do not reproduce the source constellation. In frame 45 the prominent source pendant near the upper left is fully visible, while the model substitutes a clipped near pendant and a differently spaced arrangement. Similar differences persist in frames 0 and 135. The smooth concentric-ring dish treatment also misses the visible woven relief. The author explicitly marks pendant placement/suspension/detail as inferred, so this is a fidelity limitation rather than undeclared measured accuracy.

**Repair:** First reconcile pendant centre projections, diameter and suspension heights across fixed views; then improve woven relief within budget. Preserve stable pendant IDs and distinguish measured placement constraints from inferred details. If fine weave is deferred, retain it explicitly in final limitations.

### M2-I09 — LOW — seat_far_01 through seat_far_06, seat_near_01 through seat_near_04, seat_end_01, seat_end_02, table_far, table_near, table_end, grass_window_mid, grass_wall_mid, grass_window_near, grass_reception_corner

Evidence frames: 0, 45, 90, 135, 179. Evidence type: `measured_support_gap_not_claimed_as_severe_visual_failure`.

Objects declared supported by the floor do not quite contact it. All 12 seat records have their lowest geometry 0.025 m above floor_inset; the three coffee tables have 0.015 m gaps. The measured grass-pot gaps above floor_stone are 0.015–0.025 m. These are actual component-bound separations, although their visual severity is limited at checking resolution.

**Repair:** Extend feet/bases or adjust vertical placement to make the declared support relations physically true without disturbing fitted seat/table top heights. Recompute collider bounds and support records.

## Fixed-view observations

| Frame | Concrete observations |
|---|---|
| 0 | Far seating/table silhouettes too large; black cushion seam artifacts; bulky yellow foliage; sparse reception tree crowns; weak structured floor reflections. |
| 45 | Far seating/table mismatch; fragmented mirror reflections; pendant arrangement differs, including a clipped near pendant; foreground furniture occupies too much of the image. |
| 90 | Dark upper near-end wall; source passage replaced with closed metal leaf; bulky yellow sprays and simplified floor reflections; reverse-view arrangement remains recognizable. |
| 135 | Large misplaced foreground chair replaces the source table/seat crop; cushion seam artifacts; coarse grass and yellow foliage; mirror and pendant mismatches. |
| 179 | Same furniture, foliage, pendant and material defects as forward views; anomalous supplied depth must not be used to justify global rescaling. |

Original frames 66 and 75 additionally establish the open passage and coherent planar mirror reflections. Frame numbers are M2 sample indices. All six contact sheets were viewed.

## Verification and input limitations

- Read only the two generic contracts, assigned M2 inputs/current outputs and generic inspect_scene.py; no GT, held-out, other-method or historical scene access.
- Directly viewed all six contact sheets and original RGB 0,45,66,75,90,135,179; directly viewed all five fixed author comparison JPEGs and corresponding original render PNGs.
- Opened the actual scene.blend with Blender --factory-startup --disable-autoexec and generic inspect_scene.py: PASS, 1809 meshes, 228378 triangles, finite mesh coordinates, no missing image dependencies. Independent report equals the pre-existing artifact report.
- Verified 70 semantic records map all 1809 mesh components exactly once, with matching semantic properties and evaluated bounds, valid evidence frame IDs, and no identical world-space vertex-set duplicates.
- Verified all 180 camera records, intrinsics, source indices and timestamps; maximum rigid-transform matrix error 1.1475301917585057e-06, determinant 1.0000000000000002, orthogonality error 2.220446049250313e-16. Actual stored Blender frame-0 camera conversion error 4.470348358154297e-08.
- Verified actual Cycles CPU settings: 12 samples, 640x480 at 100%, 4 threads, metric unit scale 1; inspected build script without running or modifying it.
- Measured targeted wall/door rays, evaluated cushion mesh intersections, support gaps, collider mappings and mirror cap normals. These targeted checks are not an exhaustive collision/topology audit.
- Read existing input-only BVH report tied to this scene hash; independently inspected nine supplied NPZs and verified their hashes, native camera matrices, 294x392 depth grid and distinct depth intrinsics. No new full-input BVH pass.
- Verified packet hash, seven viewed RGB hashes, GLB container length/version and absence of external GLB URIs. GLB was not independently rendered.
- Checked declared access paths, manifest, iteration log and build completion log. One version, five completed checking renders, one input-consistency pass; no reviewer renders or added scene versions.
- Computed and rechecked actual scene.blend SHA256 before writing the initial review. Derived evidence crops use existing images only.

The scene has 70 semantic objects, 1,809 mesh components and 228,378 evaluated triangles. All components map to records, evaluated bounds match, and no missing image dependencies or identical world-space vertex sets were found. Actual camera/settings verification passed; the scene uses reflective mirror surfaces rather than an extra reflected room.

Nearly unchanged stationary-window RGB has major depth scale swings: frame 15 median 0.563 m versus frame 21 19.673 m; frame 167 18.738 m versus 175 0.372 m and 179 0.778 m. These conflicts limit depth-based fit and explain why endpoint disagreement alone cannot diagnose model scale. Preserve native metric scale and cameras; document robust cross-view choices. Fixed baseline views still reveal repairable visual and construction defects.

Existing input-only MAE by fixed frame is 0: 0.720 m; 45: 0.634 m; 90: 0.486 m; 135: 0.595 m; 179: 5.797 m. These values describe agreement with predicted input depth, not GT or independently known scene accuracy.

## Scope, blockers and limits

- Initial review only. This does not freeze or approve a repaired candidate; later final review must inspect current repairs and comparison renders and recompute its scene hash.
- No GT feedback. Supplied depth is predicted input, not ground truth. No claim of recovered absolute scene accuracy follows from input agreement.
- Targeted mesh intersections, ray checks, bounds and duplicate vertex signatures were measured; exhaustive collision clearance, manifoldness, watertightness and all passage connectivity were not verified.
- Existing comparison renders were inspected; no new render independently reproduces them. The build log, script, image correspondence, unchanged candidate hash and identical artifact inspection support their association with this candidate.
- Author access declarations contain no out-of-scope paths. This is a declaration/code-and-record review, not an OS-level forensic audit of all author activity.
- Fine unseen geometry, material properties, lights and physics coefficients remain inferred. Conservative furniture/foliage AABBs are approximations.
- No technical artifact corruption or evidence of unauthorized input was found. Geometric defects and input depth inconsistency are quality limitations, not unreadable/corrupted inputs.

## Paths read

Only the following content paths were intentionally read. File-name listings were limited to `inputs/M2/` and `models/M2/`; listed files were not all opened. Standard Python/Blender runtime loading is distinct from project-data access.

- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/modelling_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/review_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/000_029.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/030_059.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/060_089.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/090_119.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/120_149.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/contact_sheets/150_179.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0000.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0015.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0021.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0045.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0090.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0135.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0167.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0175.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/geometry/0179.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/packet.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0000.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0045.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0066.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0075.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0090.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0135.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M2/rgb/0179.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/analysis/camera_checks.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/analysis/measurements.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/analysis/object_inventory.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/analysis/transform.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/build_scene.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/cameras.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/artifact_inspection.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/build_v1.log`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/comparison_v1_0000.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/comparison_v1_0045.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/comparison_v1_0090.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/comparison_v1_0135.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/comparison_v1_0179.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/input_v1/report.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/v1_0000.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/v1_0045.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/v1_0090.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/v1_0135.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/checks/v1_0179.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/colliders.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/artifact_inspection.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/evidence_crops.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/make_evidence.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/mirror_normals.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/request.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/review_audit.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/independent_review/review_audit.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/input_access_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/iteration_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/layout.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/modelling_manifest.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/objects.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/scene.blend`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M2/scene.glb`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/tools/inspect_scene.py`

The read-only measurement scripts and their outputs are retained in this directory. Geometry, build script, author records and scene artifacts were not modified. Repair priority is wall backing, passage/collider, cushion intersections, planar mirror normals, furniture projection, support contact, then appearance/foliage/pendant refinements.
