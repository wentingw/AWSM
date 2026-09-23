# M3 frozen semantic model, revision 3

Status: `frozen_for_independent_GT_evaluation`. Construction used only the allowed M3 RGB, supplied OpenVINS poses, supplied MapAnything optical-Z depths/intrinsics, authorized sensor calibration, and the clean revision-2 review. No GT, other reconstruction or evaluation result was read. Revision 3 is the modeller's response to that review, not a new independent approval.

The inventory has **259 named model elements: 195 trim/detail elements and 64 non-trim entries**. The non-trim entries contain 10 architectural entities and 54 other entries. Three scene roots/groups are separate metadata nodes and do not inflate the inventory. These are model counts, not verified real-object instance counts or coverage scores. The prior revision-2 inventory was 258 = 195 trim + 63 non-trim; the new independently grouped table bowl adds one entry.

`scene.blend`, `scene.glb`, `build_scene.py`, `geometry_plan.json`, `objects.json`, `colliders.json`, `cameras.json`, `known_space.json`, `navigation_constraints.json`, provenance/iteration logs and `modelling_manifest.json` are final deliverables. `freeze_manifest.json` hashes the frozen delivery, including the modelling manifest. `render_contact_r3.jpg` shows the final five supplied-camera checks. `artifact_checks.json` records actual analytic/schema checks and a coarse model-space ground-connectivity check.

Coordinates remain the native OpenVINS world in metres, with Z up and identity `T_input_model`. The floor top is **-2.5382169319971153 m** and the support collider has `object_id: floor`, `role: floor`. All 175 camera poses match the packet exactly. Blender uses the OpenCV RDF-to-Blender conversion diag(1,-1,-1). The GLB retains native Z-up coordinates (`export_yup=False`).

## G1 and drone consumers

Use the **52 physical hard colliders** in `colliders.json`, including full floor-lamp shades and 20 pendant-shade bounds. They are conservative AABB approximations of the selected solid model, not a claim that the inferred metric model matches the real environment. The floor is support; other hard colliders are obstacles. Plant containers are hard colliders; foliage is represented separately as planning keepouts. Thin suspension cables above the conservative flight domain are not separate bodies.

A consumer must also read **`navigation_constraints.json`**. `known_navigation_bounds` is a conservative model-space planning domain, not an already empty volume. Subtract all agent-inflated hard obstacles, vegetation keepouts and unknown regions. Anything outside those bounds is unknown and blocked. `unknown_regions` entries provide `bounds: [min,max]` and `reason`; they are planner exclusions with `physical_obstacle: false`, not fabricated walls and not counted among the 52 physical colliders.

The unsupported mirror-side continuation is excluded at native bounds `[-24.3, 4.65, floor_z]` to `[-13.5, 8.15, ceiling_z]`. The known planning domain is `[-23.2, -4.05, floor_z]` to `[0.10, 4.65, ceiling_z - 0.35]`. Inflate obstacle and domain boundaries by the vehicle extent plus the stated 0.15 m margin. G1 requires floor support; drones require floor/ceiling clearance and overhead/vegetation exclusions. `known_space.json` contains the fuller policy. Model-space tasks are supported; unresolved source conflicts prevent any claim of validated real-world navigation safety.

## What changed after clean review

Five pairs of generated seat cylinders no longer intersect. A deterministic local correction preserves each group's centroid and leaves at least 0.03 m between seat radii; the largest seat translation is 0.11145 m. Each displacement is logged per object. Reception front facets and a recessed counter, the grouped shield/U wall installation, the small table bowl, finer grass/bush blades and the tall planter flower silhouette are present. Pendant shades use open ring/spoke geometry. The reflective patterned floor inset is labelled `surface_inlay`; its material identity remains unknown rather than being asserted as carpet.

Scene root/group and part/support/mount relations all resolve. `conflict_present` has explicit semantics independent of measurement count, uncertain furniture has low confidence, and ceiling provenance describes its actual ceiling-mode rule. See `review_resolutions.json` for each clean-review finding and remaining limitations.

## Unresolved evidence conflicts

The native depth windows disagree substantially. Ten time-spaced floor modes span -3.056 to -1.708 m; the model floor uses their median. The back wall lies at x=-15.004 in frame-5 depth but approximately -22 to -24.5 m in closer views. Central plant containers lie around x=-7.9 and x=-13.3 m from opposite views. The unchanged raw measurements are retained in `depth_semantic_measurements.json` and `plane_consensus.json`. No input pose, depth or global scale was corrected.

The door/column/reception positions in frames 105/126 remain inconsistent with the selected metric model. Their locations were retained with low confidence and explicit unresolved alternatives; no external target was used to move them. The far mirror-side enclosure is unknown and omitted from physical geometry. Unseen backsides, structural thickness, joints and static rigid behavior are inferred. Botanical details, woven fixtures, material response and wall relief remain approximations.

## Rebuild and accounting

Run Blender from any working directory with this script path:

```bash
/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender --background --threads 4 --python build_scene.py -- --render
```

It reads `geometry_plan.json` beside the script and the absolute packet path recorded there. Re-derivation uses `triangulate_rgb.py`, `measure_geometry.py`, `plane_consensus.py`, `generate_plan.py` and `review_fixes.py` with NumPy/OpenCV/Pillow. Diagnostic point clouds are never exported as the semantic scene. `validate_model.py` checks the local solids and interfaces. Rebuilding creates a new artifact set; evaluate the hashes in `freeze_manifest.json` for this frozen run.

The run used **3/5 complete revisions and 15/60 tool-rendered check views**, with five unique supplied camera IDs. Exact model-token/tool-call counters are unavailable; wall-time accounting states its measured scope in the logs.
