# M4 author repair handoff — final candidate v2 (LIMITED)

This is an author handoff for a separate final independent review. It is not a review verdict or a freeze. All work stayed within the M4 method scope; no subagents or external sources were used.

Blender SHA256: `a86c6656bfd7f3ff1435c037a48aecb1d503047b799d75c9fc5524baba5c5ec5`  
GLB SHA256: `a98c5f5a83776c2fb2a4d3a0635db5c6b8794994b49d15fa4fb6b3600823a31b`

Built from an empty scene with `build_scene.py`, `layout.json`, exact `cameras.json`, `repair_colliders.py`, and `repair_mesh_audit.py`. Blender and GLB load and pass the generic artifact validators. All 1,059 real mesh components have explicit `component_names` ownership among 80 semantic objects. Model transform is identity and metric scale is 1. All 180 cameras remain exact packet copies.

## Completed checks

Two full exported versions (v1 and v2), 20 actual paired views total, no supplemental renders. Each version uses exactly 33,61,74,82,91,100,108,118,129,155. All ten v1 and all ten v2 comparison sheets were actually inspected, including RGB, optical-Z, residuals, domain masks and edges. CPU Cycles, 2 threads, 12 samples.

Exactly three actual full 180-frame BVH passes: `checks/input_v1`, `checks/input_v2`, `checks/input_final`. Final is a separately executed pass on unchanged v2 geometry, after inspection and technical validation. Both v2 pass hashes and predicted-depth arrays agree. No fourth pass remains authorized under this contract.

Own-DA3 paired MAE: v1 **0.8311m** → v2 **0.7244m**; final paired AbsRel **0.1058**. Full-input MAE: **1.4700m** → **1.3800m**. These describe agreement with predictions, not ground-truth accuracy. Domains are unchanged; all difficult frames remain included.

Mixed region evidence includes improvements and regressions: missing-pendant MAE61 **0.851→0.153m**,74 **0.801→0.115m**; shrub118 **0.958→0.478m**. Seat region129 worsens **0.326→0.396m**, while155 improves **1.295→1.040m**. Signed residuals, rectangles and before/after parameters are retained in the JSON notes and analysis records.

## Initial review issue responses

### M4-I01 — RECORDS_PRESERVED

v1 snapshots and completed handoff retained. v2 exact commands, one pre-export failed construction attempt, full check counts, geometry hashes and own validation recorded.

### M4-I02 — REPAIRED_PENDING_INDEPENDENT_VERIFICATION

Reverse desk shell faces; correct final chair-back cap winding, recalculate outward solid normals, remove degenerate-generating backrest bevel. Read-only saved-file audit finds no inconsistent edges, degenerate triangles or nonpositive closed volumes.

Remaining: Curved backs have less rounded corners; visual approximation.

### M4-I03 — SOLID_OVERLAPS_REPAIRED_VISUAL_LIMITED

Jointly refit all ten seat centers/radii/rotations and two main tables using RGB top rays plus clearance constraints. Conservative circle-envelope audit: minimum clearance 0.0053104m and no seat-seat or seat-table solid intersection.

Remaining: Source seat shapes, rotations and spacing imperfect. 129 seats_A mixed ROI MAE 0.326->0.396m worsens;155 seats_A 1.295->1.040m improves. Estimates not exact triangulation.

### M4-I04 — PARTIALLY_REPAIRED_LIMITED

Four-view missing mirror pendant fit;14 existing fixtures refit with two-view diffuser observations; six uncertain west fixtures added with own DA3 anchors and explicit in-room inference. Exposed underside weave geometry.

Remaining: Some correspondences have >5px reprojection error. West identities and heights inferred; two DA3 anchors crossed room boundary and were explicitly regularized. Pendant08 unchanged uncertain. Other near/middle lamps still displaced.

### M4-I05 — REPAIRED_PENDING_INDEPENDENT_VERIFICATION

West wall and east feature-return panels placed on +X room faces at +0.0975m offset. Actual82/91/100 comparisons now show exposed panels.

Remaining: Panel joint layout and material remain approximate.

### M4-I06 — PARTIALLY_REPAIRED_LIMITED

Reduce shrub spread, leaf width and branch count; replace spiky mirror fern with rounded fine-leaf canopy. Keep pot centers and measured architecture.

Remaining: Shrubs still approximate. Mirror fern is too thin/flat and lacks convincing visible connecting stems; grass and reception trees remain simplified. Botanical detail inferred. No reflected DA3 used to duplicate plants.

### M4-I07 — PROXY_AND_SUPPORT_REPAIRS_PENDING_INDEPENDENT_VERIFICATION

Add inferred desk plinth and foot pads to inlay top z0.011. Component compound colliders replace semantic AABBs. Segment facade and backing around doors; separate closed leaves. Author aperture-volume test has no static obstruction in five door apertures when leaves disabled or in declared finite recess.

Remaining: Doors remain CLOSED as observed; exterior/interior destinations and articulation unknown. Corridor is declared finite inferred recess ending at y16.25. No dynamic simulation, exact collision hull or comprehensive assembly intersection sweep.

### M4-I08 — PARTIALLY_REPAIRED_LIMITED

Add inferred regular metallic floor pattern, darker/wider frames, visible lamp underside weave, oak color grain and reduced diffuse lighting.

Remaining: Pattern is too uniform and reflection/lighting differ substantially. Source finish mechanism uncertain. Procedural Blender floor/oak shaders are not baked into GLB, which retains approximate base PBR materials.

### M4-I09 — DOCUMENTED_INPUT_LIMITATION_RETAINED

Retain identity transform, metric scale1, all180 exact packet cameras and unchanged prescribed depth domains. Keep conflicting end-wall/ceiling predictions and extreme DA3 frames. Final pass uses own DA3 only.

Remaining: Far-wall median signed residual remains -2.685m at33,+2.226m at129,-2.746m at155. Frames177..179 median own DA3 about0.0666m. No attempt to distort layout to fit global prediction score.

## Reproducibility and records

- `analysis/repair_changes_v2.json`: each edited dimension/position/construction parameter, before/after values, source pixels, signed v1 depth residuals, rationale and uncertainty.
- `analysis/component_changes_v2.json`: complete inspected component bounds/topology changes.
- `analysis/repair_measurements_v2.json`: actual multi-view RGB triangulation, reprojection residuals and own DA3 backprojections using NPZ intrinsics.
- `analysis/comparison_observations_v2.json`, `spatial_residuals_v2.json`, `full_input_diagnostics_v2.json`: observed limitations and regional conflicts.
- `checks/saved_mesh_validation.json`: read-only saved artifact audit of all meshes, including the six blocking components. Desk signed volume is positive; all five backrest solids have consistent outward winding and no degenerate triangles.
- `checks/author_candidate_audit.json`: semantic ownership, camera equality, conservative furniture clearance, support heights and portal proxy checks. These are author checks, not independent review.
- `checks/revision_command_history.json`, `input_access_log.json`, `iteration_log.json`: command/access/budget history. One v2 construction attempt failed before scene export because the bevel still generated degenerate triangles. Its logs remain; it produced no scene version, render or BVH pass. The corrected build exited0.
- `versions/v1` and `versions/v2`: retained artifacts, parameters, programs, metadata and evidence snapshots.

Visual fidelity remains LIMITED. In particular, some lamp positions/identities, foliage forms, chair backrest shapes, source lighting and reflections are not faithfully reconstructed. Hidden supports, material details and collision/door mechanics are inferred. Final independent review should revisit all M4-I01–M4-I09 and the actual v2 artifacts/checks.

Validation preservation note: the current top-level generic validation JSONs now describe v2. The original v1 GLB result was recovered from its retained verbatim log; an explicitly labelled equivalent v1 scene inspection is retained from the separate reviewer. Every paired and full-input output remains intact.
