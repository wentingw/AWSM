# M3 independent initial review

**REQUIRES_FIXES** — reviewer `gpt-6-astra`.

Inspected/current scene SHA256: `4104ac8cdfb302a20fedd0379af521b325d5e14ce500863cff2acc8f41007fb2`.

Reviewable semantic scene with verified supplied camera transforms; concrete cushion collisions, blocked declared doorways and substantial visual discrepancies require repair. No technical corruption or evidence of input leak was found in inspected material.

## Actionable findings

### M3-I01 — high

Objects: far_seat_0, far_seat_1, far_seat_2, far_seat_3, far_seat_4, far_seat_5, near_seat_0, near_seat_1, near_seat_2. Frames: 0, 45, 135, 179.

Rendered cushion tops have black crescent/oval artifacts and merge into one another, unlike the distinct upholstered modules in RGB. Evaluated mesh bounds and cylindrical seat definitions establish radial penetrations of 0.309 m for far_seat_2/3, 0.330 m for far_seat_3/4, 0.276 m for far_seat_4/5 and 0.227 m for near_seat_1/2; all cushion tops are at z=0.510 m. Seven cushion pairs overlap by more than 0.02 m. Coplanar overlapping caps are a plausible cause of the black artifacts; that causal diagnosis has not been isolated experimentally.

Action: Re-fit cushion radii, center spacing and module silhouettes using frames 0/45/135 and the near-group source views. Remove interpenetrating coplanar caps; verify distinct silhouettes and clean tops in the fixed comparisons. Preserve native scene scale and supplied cameras.

### M3-I02 — high

Objects: mirror_bay_wall, recess_wall, interior_door_00, interior_door_01, interior_door_02, interior_door_03, interior_door_04. Frames: 60, 90.

Door openings are not actual openings: wall_y skips some lower panel faces but retains an uninterrupted substrate. Actual mirror_bay_wall__substrate bounds are x=[0.75,10.25], y=[-0.310,-0.130], z=[0,5]; recess_wall__substrate similarly spans x=[10.25,19.25], z=[0,5]. Both wall colliders cover their entire walls. Frame 90 RGB shows a dark doorway/recess immediately right of the mirror cluster; the render substitutes a pale flush treatment. The 060_089 source contact sheet also shows the doorway obliquely. The dark RGB patch alone does not establish every door as open.

Action: Resolve the visible door states from the permitted RGB. For observed open doorways, cut the substrate and panel geometry and split wall colliders into jamb/header pieces, with a leaf placed at its observed angle if present. Document closed doors explicitly; do not declare their solid-backed facades to be open passages.

### M3-I03 — medium

Objects: pendant_00, pendant_01, pendant_02, pendant_03, pendant_04, pendant_05, pendant_06, pendant_07, pendant_08, pendant_09, pendant_10, pendant_11, pendant_12, pendant_13, pendant_14, pendant_15, pendant_16, pendant_17, pendant_18, pendant_19, ceiling. Frames: 0, 45, 90, 135, 179.

The source pendants have prominent woven undersides; all five comparisons show smooth opaque bowls with small luminous discs instead. Source ceiling margins are dark slatted bands, while the candidate bands are pale. The discrepancy is especially clear in the large near pendants at frames 45 and 135. The build script contains ribs, but their mere presence does not reproduce the visible underside.

Action: Make the weave/ribs visible on the underside and match the dark slat-band material and width. Check placement and apparent size against the five fixed views before adding fine detail.

### M3-I04 — medium

Objects: floor, ceiling, far_end_wall, mirror_bay_wall. Frames: 0, 45, 90, 135, 179.

The dark central floor loses the strong repeated grid-like highlights/reflections and pendant-disc reflections visible throughout the source sequence. It becomes a mostly smooth dark strip in the renders, most clearly across the foreground of frame 90. Pale floor and wood walls are also washed out, with weak grain and panel-reveal contrast. This changes large image regions, not only small texture details.

Action: Tune daylight direction, exposure/material response, visible slat geometry and reflection roughness together using the source comparisons. Reproduce the observed contrast and reflection structure; avoid encoding highlights as unsupported raised geometry.

### M3-I05 — medium

Objects: flower_trough_0, flower_trough_1, mirror_vase, window_bush, reception_tree_0, reception_tree_1. Frames: 0, 45, 90, 135, 179.

Yellow trough foliage is sparse exposed branching in the candidate versus dense yellow flowering masses in RGB, especially at frame 90. mirror_vase becomes a sharp, broad-leaved spiky plant instead of the fine drooping foliage visible at frames 45/135/179. Reception tree crowns are faint sparse leaves instead of compact dark masses. Procedural leaf topology is a declared assumption, but the visible mass and silhouette still disagree.

Action: Fit foliage envelope, density, leaf width and droop to the source silhouettes. Prioritize trough mass and mirror_vase shape over individual leaf topology; keep hidden growth inferred.

### M3-I06 — medium

Objects: far_coffee_table, far_seat_0, far_seat_1, far_seat_2, far_seat_3, far_seat_4, far_seat_5, flower_trough_0, flower_trough_1, round_column. Frames: 0, 45, 90, 135.

The main furniture grouping does not line up with the source: at frame 135 the rendered far coffee-table/group is noticeably farther right and its right-hand trough is more separated from the seating; at frames 0/45 the grouping appears wider and larger. At frame 90 the two trough boxes occupy a wider span than the source. The column also appears broader in the comparisons. These are visual judgments rather than an independently fitted pose/size solution; cameras were verified separately.

Action: Compare source and render landmarks in normalized per-view coordinates and re-fit object centers/extents jointly across 0/45/90/135. Resolve seat overlaps first. Use documented depth uncertainty and keep supplied camera transforms and metric scale fixed.

### M3-I07 — low

Objects: modelling_manifest, semantic_records, iteration_log. Frames: records only.

The current manifest still reports building_initial_checks instead of ready_for_independent_review despite five completed comparisons and available checks. 64 of 95 semantic records have empty spatial_relations, including many supported or mounted objects. The author access log lists early build/analysis commands but omits the completed rendering and subsequent artifact/depth checks; iteration_log does not explicitly enumerate the already completed all-frame depth pass. No forbidden input access was found in the declarations inspected.

Action: Update submission status when ready, record meaningful support/mounting/adjacency relations, and complete command and checker-pass accounting with actual elapsed times and hashes. Preserve honest unresolved input-depth and visual limitations.

## Verification and limits

- **Source and author comparisons:** Viewed all six source contact sheets, original RGB frames 0/45/90/135/179, and all five actual v1 side-by-side comparisons.
- **Actual Blender artifact:** Generic inspect_scene.py opened scene.blend successfully: 4001 finite mesh objects, 154489 triangles, no missing image dependencies. Current SHA256 matches inspection and existing input-consistency report.
- **Semantics and components:** 95 semantic records map all 4001 mesh names exactly, with no missing components or duplicate component references. Meaningful categories include structural surfaces, furniture, plants, doors, mirrors and lights. No exhaustive duplicate-geometry search was performed.
- **Camera and scale:** All 180 recorded poses equal model_from_input @ supplied camera_to_world exactly in JSON arithmetic; all RGB intrinsics match. Transform determinant 0.9999999999999997; orthogonality max error 4.44e-16; geometry_scale=1. Build/render scripts use OpenCV-to-Blender right multiplier diag(1,-1,-1,1). RGB K is 762.8 focal length at 1280x960; fixed depth NPZ K is 233.607498 at 392x294. Saved Blender camera matrix was not separately dumped.
- **Collisions, openings and mirrors:** Seven circular cushion pairs overlap by more than 0.02 m; full wall substrates and full-wall colliders block declared openings. Actual meshes and code show reflective discs on the wall, with no explicit reflected extra room in construction. No exhaustive collision, topology, support or watertightness validation is claimed.
- **Input depth:** Read five assigned NPZ files and reused existing input-only report for the inspected hash. No new raycast pass, no GT.
- **Budget and integrity:** One scene version, five completed CPU Cycles renders at 12 samples and 640x480 supported by iteration/render logs; one existing 180-frame input-consistency report observed. Reviewer extra renders=0 and extra all-frame depth passes=0. Packet hash and five geometry hashes match declarations. GLB parsing PASS is an existing author check, not independently repeated.

- Input depth is inconsistent across the assigned sequence: valid-depth median is 5.676 m at frame 0, 6.009 m at 45, 6.172 m at 90, 5.988 m at 135, but 0.500 m at 179. The manifest already discloses this collapse; it is not evidence to shrink the room or change supplied cameras.
- Existing input-only MAE is 0.487/0.545/0.541/0.515/6.470 m at frames 0/45/90/135/179. These are author checker results for the matching scene hash, not GT accuracy and not independently recomputed metrics.
- Exact door states and the cause of black cushion artifacts remain partly inferential; the solid wall backing and cushion overlaps themselves are measured.
- Author depth estimates report 0.3–1.2 m wall/glazing conflicts; hidden surfaces, joinery, physical coefficients and foliage topology remain assumptions.
- No extra render was made. Existing comparisons were checked against source and render/build records; individual comparison images do not contain a cryptographic scene-hash binding.
- Reviewer scope was limited to the assigned M3 directories, two contracts and generic inspect_scene.py, plus executable/runtime libraries. No parent experiment, GT, held-out frames, other methods, historical model, plan or publication was inspected. Declaration review cannot certify unobserved historical access.

Extra renders: **0**. Extra all-frame depth passes: **0**. Geometry and author build script were not changed.

## Read-path record

All intentionally read data paths follow; command accounting is in `input_access_log.json`. The generic inspector output and targeted numeric evidence are in `artifact_inspection.json` and `record_checks.json`.

- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/review_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/modelling_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/tools/inspect_scene.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/packet.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/000_029.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/030_059.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/060_089.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/090_119.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/120_149.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/contact_sheets/150_179.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/rgb/0000.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/rgb/0045.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/rgb/0090.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/rgb/0135.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/rgb/0179.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/geometry/0000.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/geometry/0045.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/geometry/0090.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/geometry/0135.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M3/geometry/0179.npz`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/scene.blend`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/build_scene.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/render_checks.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/modelling_manifest.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/layout.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/objects.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/colliders.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/cameras.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/iteration_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/input_access_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/analysis/measurements.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/analysis/camera_checks.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/analysis/object_inventory.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/input_v1/report.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/glb_load.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/build_time.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/render_v1.log`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/independent_review/artifact_inspection.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/independent_review/record_checks.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/v1/comparison_0000.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/v1/comparison_0045.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/v1/comparison_0090.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/v1/comparison_0135.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M3/checks/v1/comparison_0179.jpg`
