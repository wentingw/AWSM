# SceneWeft

**Geometry-grounded reconstruction of editable 3D worlds.**

Reconstruction code accompanying [**AWSM: Agentic World Simulation and Mapping**](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/). SceneWeft turns RGB observations and geometric evidence into structured Blender scene programs: explicit objects, spatial relationships, and editable geometry—not just a point cloud or a rendered view. It builds on pose estimation and depth reconstruction, using an agent to construct, inspect, and refine the scene.

[中文](README.zh-CN.md) · [Experiment & reproduction](experiments/world_lobby_four_trajectory_20260929/README.md) · [Third-party notices](THIRD_PARTY.md)

## Four reconstruction routes

The World Lobby study compares four routes with a shared RGB observation set and scene-authoring objective. All use an Astra–Blender workflow; their geometric inputs differ.

| Method | Camera poses | Depth evidence |
| --- | --- | --- |
| **M1 · RGB-only** | No estimated trajectory | None |
| **M2 · ViPE** | ViPE, from RGB | Pose-conditioned Depth Anything 3 |
| **M3 · ORB-SLAM3** | ORB-SLAM3, from RGB + IMU | Pose-conditioned Depth Anything 3 |
| **M4 · GT-pose reference** | Ground-truth camera poses | Pose-conditioned Depth Anything 3 |

M4 supplies reference poses, **not GT geometry or GT depth**, to the modeler. Evaluation separates pose accuracy, scene geometry, depth, and appearance. This is a single-scene system comparison, not a claim that one metric captures reconstruction quality or that the routes isolate a single variable.

## Implementation

The [September 29 experiment](experiments/world_lobby_four_trajectory_20260929/) contains the implementations described above:

- [`code/`](experiments/world_lobby_four_trajectory_20260929/code/) — trajectory preparation, DA3 inference, and geometric input packets.
- [`astra_blender2/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/models/) — M1–M4 scene builders and construction parameters.
- [`astra_blender2/tools/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/tools/) — view checks, model freezing, and reconstruction evaluation.

Earlier OpenVINS/MapAnything experiments remain separate historical records; their method labels and assets must not be substituted for this run.

## Reproduce

Verify the source snapshot and run the portable depth checks:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
.venv/bin/python scripts/verify_source_snapshot.py
.venv/bin/python scripts/check_world_lobby_depth_math.py
```

Rebuild a saved scene with Blender 5.2.0; use a new output directory outside the repository:

```bash
.venv/bin/python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/sceneweft-M4
```

Choose `M1`–`M4`. This executes the saved construction program; it does not rerun inference, agent reasoning, or evaluation. Full pipeline reproduction additionally requires the recorded capture, frontend dependencies, weights, evaluation assets, and path relocation. See the [experiment guide](experiments/world_lobby_four_trajectory_20260929/README.md) for requirements and boundaries.

## Scope

This release focuses on **reconstruction methods and reproducibility**. Embodied demos, robot control, and task execution are outside its scope and deferred to a future release. Code and external assets remain subject to the terms documented in [THIRD_PARTY.md](THIRD_PARTY.md).
