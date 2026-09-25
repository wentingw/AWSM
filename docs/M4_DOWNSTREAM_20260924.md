# M4 downstream revision — 24 September 2026

The article now uses the frozen M4 scene for both robot tasks. Earlier M3 episodes remain unchanged historical evidence. New task results are not a controlled M3–M4 comparison: candidate views, language protocol and floor handling differ.

## Inputs and isolation

- Scene: `experiments/world_lobby/M4/astra_model/scene.blend`.
- SHA256: `cc6cb605246a255d94e36b9dc3f8b91d5a292b047470bc0ff75b8a5c404b0cfe`.
- M4 reconstruction receives RGB, calibrated intrinsics, GT camera poses and pose-conditioned MapAnything depth; it does not receive GT geometry or GT depth.
- Runtime controllers receive simulator self-state and the reconstructed semantic/collision map. Drone reference-pose answers and G1 intended-instance IDs enter only the evaluator.
- G1 uses original M4 finite stone and raised-inset floor slabs, with top heights 0.025 m and 0.041 m. Obstacle geometry is conservative reconstructed AABBs; friction and other physical properties are assumed.

## Drone reproduction

Run Blender with the reconstruction packet paths relocated consistently if needed:

```bash
blender -b --python-exit-code 1 --python scripts/m4_drone_render_task_cache_blender.py -- experiments/world_lobby/M4/astra_model/scene.blend data/packets/M4/packet.json experiments/tasks/drone_M4/view_cache
python scripts/m4_drone_photographic_batch.py
blender -b --python-exit-code 1 --python scripts/m4_drone_render_endpoints_blender.py
python scripts/evaluate_m4_drone_photographs.py
python revisions/m4_downstream_20260924/verify_drone_results.py
```

The batch uses the reconstruction Python with Torch, Transformers, NumPy and image dependencies; it launches `.venv-tasks/bin/python` for MuJoCo. DINOv2-small weights must already exist locally. There are 20 fixed RGB queries and 30 M4 candidate renders. Ranking uses CLS cosine similarity and the top five candidates are checked for planning. Planning receives candidate map cameras, not the reference target pose. There is no continuous visual refinement.

Reports: `results/evaluation/tasks/drone_M4_20260924/report.json`. Collision-free candidate arrival and rephotography are separate outcomes. Strict rephotography requires position error ≤0.10 m, rotation error ≤5°, and no collision; relaxed thresholds are ≤0.25 m and ≤10°. Endpoint images use achieved positions with the stated ideal stabilized-gimbal orientation. RGB scores compare all 20 resized references with their endpoint images at 640×480.

## G1 reproduction

```bash
.venv-tasks/bin/python -m src.tasks.m4_g1.prepare
.venv-tasks/bin/python -m src.tasks.m4_g1.batch
blender -b --python-exit-code 1 --python scripts/m4_g1_visibility_blender.py
.venv-tasks/bin/python revisions/m4_downstream_20260924/verify_g1_results.py
```

The five Chinese instructions specify low foliage in pale-grey ceramic, north/south golden-flower planters, and north/south bird-of-paradise plants. North is explicitly map +Y. Each instruction is executed from four deterministic free, floor-supported mapping locations: 20 executions, five targets. A transparent constrained parser matches generated semantic attributes; it does not use a sentence-to-ID answer lookup or online visual recognition. Ambiguous instructions are rejected. A* selects an approach pose using a 0.47 m inflation radius; the official G1 12DOF CPU locomotion policy drives articulated MuJoCo dynamics.

The protocol and requests live under `experiments/tasks/g1_M4/replay_20260924/`. The independent intended IDs are in `results/evaluation/tasks/g1_M4_20260924/expected_targets.json`. Navigation requires no obstacle contact/fall, approach distance <0.30 m, target bearing <15°, and at least 1.5 seconds of dwell; timeout is 90 simulated seconds. Visibility is verified separately in the M4 mesh, using a fixed body-relative virtual camera and occlusion-aware first-hit rays. The criterion is target coverage ≥0.1% of the image, estimated from a uniform 160×120 ray grid for a 640×480 camera. This is evaluator geometry, not learned visual recognition. Scene occlusion is included; robot self-occlusion is not modelled.

Recorded qpos/qvel are sampled at 20 Hz. The terminal camera uses the last complete recorded state, up to 50 ms before stopping; it is not synthesized from the answer pose. Runner contacts, falls and dwell are checked at the higher simulation/controller rate. The independent audit recalculates target identity, path length and terminal approach/bearing from the stored trajectory, and cross-checks the reported outcomes; it does not claim to independently re-simulate every contact.

Reports: `results/evaluation/tasks/g1_M4_20260924/visibility.json` and the canonical combined report `results/evaluation/tasks/m4_downstream_20260924/report.json`.

## Reuse and presentation

Batch runners reuse completed episode summaries. Use a new versioned output directory and freeze new requests for a genuinely new experimental run; do not overwrite these records. Presentation videos replay drone Query 13 and G1 Episode 00 at 1× from recorded physical states. Their display-only M4 meshes are exported from the frozen Blender scene in unchanged Z-up metre coordinates, grouped by source material; walls, ceiling, ceiling lights and attached mirrors are omitted for the camera view. This cutaway does not change the original collision world or the full-scene endpoint images. Video lighting and shading are simplified. They add no experimental trials. Reproduction ZIP includes task sources, requests, summaries and trajectories; complete models remain at the pinned Hugging Face asset revision, subject to its access settings.

Results establish only these tasks in one reconstructed scene with known self-pose. They do not establish original-GT-world transfer, real robot performance, recovered true physical properties, arbitrary-language understanding, or cross-scene generalization.

## Rebuild presentation media

Run with Blender, the task Python, OSMesa and an H.264-capable `ffmpeg` available. Set `FFMPEG` to its executable path if it is not on PATH.

```bash
blender -b --python-exit-code 1 --python scripts/m4_g1_export_display.py
python scripts/m4_g1_display_world.py
python scripts/m4_g1_replay_video.py --episode experiments/tasks/g1_M4/replay_20260924/episode_00 --world-xml experiments/tasks/g1_M4/presentation_20260924/episode_display.xml --out blog/assets/m4_tasks/g1_episode.mp4 --poster blog/assets/m4_tasks/g1_poster.jpg
python scripts/m4_drone_replay_video.py --query 13 --display-manifest experiments/tasks/g1_M4/presentation_20260924/material_manifest.json
python scripts/m4_drone_comparison_panel.py
python scripts/m4_g1_comparison_panel.py
python revisions/m4_downstream_20260924/assemble_report.py
python scripts/build_blog.py
```
