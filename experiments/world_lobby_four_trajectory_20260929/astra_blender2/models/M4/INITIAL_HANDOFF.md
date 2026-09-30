# M4 initial v1 — ready for independent review

This is the initial author handoff, not an independent review or a frozen model. Only M4 allowed RGB, exact sampled native cameras, and its predicted DA3 were used. No agents were spawned. Scale is 1 with identity `model_from_input`; all 180 cameras are exact packet copies.

## Artifacts

- `scene.blend` and `scene.glb`: 73 semantic objects, 5,119 named mesh components. GLB load, finite bounds and complete semantic ownership mapping pass.
- `build_scene.py` reconstructs from an empty scene using `layout.json` and `cameras.json`; it does not load a saved model. Native metric Z-up is preserved in Blender; GLB uses its standard Y-up coordinate conversion.
- `objects.json`, `colliders.json`, `analysis/object_inventory.json`: semantic mapping, evidence/provenance, measured bounds and inferred static AABB colliders.
- `analysis/measurements.json`, `triangulation.json`, `measurement_decisions.json`: real NPZ backprojections/local plane fits, original image-point ray intersections, residuals and conflicts. All six contact sheets and ten original check keyframes were viewed.
- `input_access_log.json`, `iteration_log.json`, `modelling_manifest.json`: scope, execution and budget records.
- `versions/v1/`: preserved scene, GLB, build script, layout, cameras and evidence records. The helper's original manifest snapshot has precheck counts; `completion_manifest.json` records final initial-phase counts.

## Completed checks

Exactly ten paired views: **33, 61, 74, 82, 91, 100, 108, 118, 129, 155**. CPU Cycles, 2 threads, 12 samples, 640×480. Each includes RGB, matching geometric optical-Z, own-DA3 reference, signed/absolute/relative errors, domain masks, depth edges and real comparison sheets in `checks/v1/`. All ten comparison sheets were actually viewed.

The generic helper's camera projection assertions pass. `checks/paired_ledger.json` contains ten completed entries and no supplemental renders. `checks/v1/paired_report.json` reports MAE **0.8311 m**, AbsRel **0.1283**, valid coverage **99.9980%** against own predicted DA3.

Exactly one full180-frame input BVH pass is preserved in `checks/input_v1/`: 19,200 rays/frame, MAE **1.4700 m**, AbsRel **0.8237**, valid coverage **99.9992%**. The input has severe prediction inconsistencies: frames177–179 have median predicted Z≈0.0666m, maximum≈0.187m. No cameras, scales, depth values or prescribed masks were adjusted to compensate. This is consistency with predictions, not ground-truth accuracy.

`checks/artifact_inspection.json`, `glb_load.json` and `initial_record_audit.json` pass their technical checks. All five generic helpers exited0. Build construction took roughly24 minutes due to thousands of operator-created components. An author Ctrl-C sent while monitoring was handled as a delayed internal-break event after the log's `BUILD_COMPLETE` and completed exports; the build process returned1. The saved artifacts were independently loaded by generic inspection, raycast and GLB validation. No rebuild or extra render was used. Full logs and commands are under `checks/`.

## Concrete limitations for the reviewer

See `analysis/initial_issues.json` and `comparison_observations_v1.json` for every inspected view, and `spatial_residuals_v1.json` for numeric regions. Main issues:

1. Western pendants are missing; other pendant positions/heights are approximate. Woven ribs lie above the bowl, so the rendered underside is incorrectly smooth.
2. West-wall and feature-return panels were generated on the wrong side of their backing and appear dark in82/91. Correct interior sidedness in a later repair.
3. Seat sizes, arrangement and backrest orientations differ, with overlaps and incorrect silhouettes in61/74/129. Furniture needs additional multi-view measurement.
4. Floor gold grid-like appearance is absent; wall grain, directional shadows and door frame widths differ. Lighting is overly diffuse/bright. Procedural Blender materials are not baked into GLB texture maps, so GLB appearance is more limited.
5. Shrub leaves are too broad and uniform, vase foliage too spiky, trees too sparse. Botanical detail, hidden surfaces, thickness, materials, lighting and physics remain inferred.
6. Far-wall signed region medians are −2.683m in33, +2.237m in129, −2.741m in155. Desk triangulation has <0.34px reprojection error, supporting restraint about moving the whole end wall to fit DA3 alone.

No author review verdict or freeze was issued. The `independent_review/` directory is reserved for the separate reviewer. Remaining budget: four built versions / forty standard paired views and exactly two future full-input passes. No later-phase repair or pass has run.
