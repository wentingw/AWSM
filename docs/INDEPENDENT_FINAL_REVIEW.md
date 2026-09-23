# Independent final review

Date: 2026-09-23

This review is read-only over the frozen model outputs, evaluation scripts, and existing test suite. No model, scene, or existing metric was changed.

## G1 task success semantics

`src/tasks/g1_episode.py` marks an episode `success` only when the simulator state remains upright, has zero recorded world-obstacle contact steps, reaches the planned approach point within 0.3 m, aligns the target bearing within 15 degrees, and remains there for 1.5 s. The code does not perform image visibility, pixel-level target detection, or independent object-identity verification. Grounding is the constrained `query_scene` parser over frozen object metadata and localization is explicitly simulator-state-oracle. Therefore the formal G1 count is collision-free simulator approach success under constrained semantic grounding; it is not visual recognition success or open-language success.

Evidence: `src/tasks/g1_episode.py` lines 63–66 and 82–113; `experiments/tasks/g1_M3/final_margin047/batch_summary.json` reports 18 success and 12 planning_failed.

## G1 GT clearance audit

`scripts/audit_task_gt_clearance_blender.py` imports only the authorized GT USD, verifies exactly 9,984,967 GT triangles, builds its BVH from GT mesh vertices/triangles only, and maps each logged G1 proxy point with `results/M3/model_registration.json` before querying nearest surface distance. It does not load the predicted mesh into the BVH and does not test inside/outside.

The torso/head points are fixed offsets `[0,0,0.45]` and `[0,0,1.10]` rotated by the logged base quaternion. The two foot points are fixed offsets `[-.12,0,-.78]` and `[.12,0,-.78]`; the JSON field `foot_bottom_minus_gt_floor_m` is therefore a height proxy, not a measured link or sole contact height. The report README states this limitation. The floor reference is the 0.5th percentile of GT mesh vertex z values, so the reported foot deviation is a reference-height difference after the same model-to-GT transform, not a collision distance.

Existing result evidence: `results/evaluation/tasks/gt_clearance/g1_M3/g1_gt_clearance.json` has 18 trajectories, GT triangle count 9,984,967, and semantics explicitly stating nearest-surface-only, no inside/outside, no dynamics replay.

## Drone GT clearance audit

`scripts/audit_drone_gt_clearance_blender.py` covers all 20 readable drone trajectories and uses the same GT-only 9,984,967-triangle BVH and M3 registration transform. It reports nearest surface distance from the logged drone center. The `<0.30 m` flag is only a spherical center-to-surface potential-overlap heuristic; it is not collision truth and does not determine whether the center is inside the GT mesh.

## Pose metrics

`src/evaluation/pose.py` validates TUM timestamps and quaternions, interpolates translation linearly and rotation with Slerp, and computes explicit SE(3) or Sim(3) Umeyama alignment. RPE translation is computed in the predicted body frame with the estimated global scale, while rotation uses relative rotations. `tests/test_pose_metrics.py` passes all four tests, covering Sim(3)/RPE, quaternion sign flips, endpoint timestamp tolerance, and no-overlap rejection (`4 passed`).

The current report labels M1 as having no native pose and uses Sim(3) only as a diagnostic presentation alignment. `results/M1/render_manifest.json` explicitly says “diagnostic Sim3 ... GT-assisted; not metric recovery” and records scale 0.6897587. This is not a hidden metric pose claim.

## Model depth and geometry

`evaluate_model_depth_blender.py` transforms only the frozen predicted mesh into GT coordinates, builds a BVH from that model mesh, and raycasts from the supplied GT camera poses. Camera rays use the calibrated intrinsics, are rotated by the TUM camera rotation, and divide Euclidean ray-hit distance by ray norm to recover optical-z. The GT depth arrays provide the comparison domain; the GT mesh is not used as the predicted raycast BVH.

`evaluate_blend_surface_blender.py` uses separate BVHs: predicted samples query the GT BVH and GT samples query the predicted BVH. It verifies the GT triangle count and applies one supplied global transform without ICP. The M1 transform is the explicitly documented diagnostic Sim(3); M2/M3/B2 transforms are the fixed registration files used by the existing evaluation.

No material implementation defect was found in these reviewed paths. The main interpretation constraints are semantic: G1 success has no independent visibility/identity test; the G1 foot result is a fixed proxy; all GT clearance results are static nearest-surface diagnostics; and M1 Sim(3) is diagnostic rather than metric recovery.
