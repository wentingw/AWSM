# AWSM — Agentic World Simulation and Mapping

**Turning visual observations into geometry-grounded, editable 3D worlds simulation-ready for robots.**

AWSM investigates how an agent can turn RGB observations and geometric measurements into a **structured Blender scene program**: named objects, materials, cameras, spatial relationships, and collision proxies—not only a point cloud or a novel-view renderer. The longer-term goal is a shared spatial representation for mapping, simulation, and interaction. This repository releases the **reconstruction implementation and its audit trail**, not a validated end-to-end robotics system.

[中文](README.zh-CN.md) · [Official article](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/) · [Interactive 3D comparison](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/#figure-3) · [Reproduction guide](docs/AWSM_REPRODUCTION.md) · [Experiment source](experiments/world_lobby_four_trajectory_20260929/README.md)

> **Evidence scope.** This README's numerical results refer specifically to the September 29 **`astra_blender2` fixed ten-view modelling run**. The live article displays a different frozen model set (`astra_blender`), with a documented upstream naming discrepancy. Do not interchange their figures, metrics, or model hashes. See [the evidence map](docs/AWSM_REPRODUCTION.md#which-results-belong-to-which-models).

## Updates

- **2026-10-01 · v0.1** — Published the [AWSM research blog](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/) and the initial reconstruction code release: M1–M4 implementations, evaluation tools, and reproduction guidance.

## Explore the project

- **[English article](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/) / [中文文章](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html):** motivation, methods, interactive comparisons, and limitations.
- **[Shared-camera 3D viewer](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/#figure-3):** rotate and zoom the selected reconstruction against GT; cutaway display changes do not modify the frozen assets.
- **[Matched-view image comparison](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/#figure-4):** inspect model/GT image differences rather than relying on an aggregate score.
- **[September 29 source report](experiments/world_lobby_four_trajectory_20260929/astra_blender2/report/space/index.html):** included HTML preserves the later run's Tables 3–5. Its images, models, and linked raw metric files are not bundled. The [original HF Space](https://huggingface.co/spaces/Ooliva/world-lobby-exps-new) returned **401 without authentication** when checked on October 1, 2026; it is not an anonymous public demo.

<details>
<summary>Official article visual preview — a separate published model set, not the ten-view results below</summary>

![Official article: M1–M4 and input GT over five fixed views](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/assets/fixed_five_view_comparison_m1_m4.jpg)

The official hosted figure uses views 0/36/72/108/144 and the article's `astra_blender` models. Its [figure-generation source](experiments/world_lobby_four_trajectory_20260929/astra_blender2/tools/build_reference_style_figures.py) explicitly targets that earlier model directory, despite living under `astra_blender2/tools/`. This image is **not** a rendering of the scenes rebuilt by the quick-start below. The article's [provenance note](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/evidence/provenance-note.md) records unresolved historical frontend naming; the preview is not used to establish the later run's numerical claims.

</details>

## What AWSM builds

1. **Observe:** inspect the shared set of 180 modelling RGB frames, camera calibration, and only the geometric inputs allowed for that method.
2. **Measure and construct:** derive dimensions and placements, identify uncertain/inferred structure, and write object-level Blender Python.
3. **Check and revise:** compare RGB and optical-Z depth at fixed review cameras; preserve parameter changes, residuals, and independent review findings.
4. **Freeze:** save the scene, GLB, semantic/object records, collision proxies, and hashes before independent GT scoring.
5. **Evaluate separately:** measure trajectory, predicted depth, scene surface geometry, rendered appearance, and frozen-model depth. These answer different questions.

The resulting representation is editable: a wall, chair, planter, or light remains an explicit scene component rather than an anonymous surface sample. Explicit geometry and collision proxies are useful interfaces for later simulation, but do not by themselves certify physical accuracy, navigation safety, or real-world transfer.

### Four reconstruction routes

| Route | Pose input | Depth input | Interpretation |
| --- | --- | --- | --- |
| **M1 · RGB-only** | No measured trajectory; common intrinsics known | None | Visual/layout prior baseline; scale is assumed, not measured |
| **M2 · ViPE** | RGB-only ViPE native poses | Pose-conditioned Depth Anything 3 (DA3) | Image-based geometric evidence |
| **M3 · ORB-SLAM3** | Monocular-inertial ORB-SLAM3; RGB + IMU + calibration | Pose-conditioned DA3 | Visual–inertial geometric evidence |
| **M4 · GT-pose reference** | Permitted sampled GT camera poses | Pose-conditioned DA3 | Diagnostic reference; **no GT mesh or GT depth given to the modeller** |

All routes use the Astra–Blender objective and the same 180 RGB identities. Frontends may process the full 4,499-frame capture. M2 versus M3 is a **system comparison**, not an isolated IMU ablation. GT poses do not make M4 a deployable estimator or a theoretical upper bound. OpenVINS is a trajectory diagnostic in this experiment—not its M3 modelling frontend. Earlier OpenVINS/MapAnything records elsewhere in the repository retain their historical meanings.

### Implementation map

All relative paths in this table start at [`experiments/world_lobby_four_trajectory_20260929/`](experiments/world_lobby_four_trajectory_20260929/).

| Stage | Implementation / evidence |
| --- | --- |
| Capture identity, calibration, input hashes | [`contract.json`](experiments/world_lobby_four_trajectory_20260929/contract.json), [`COMMANDS.md`](experiments/world_lobby_four_trajectory_20260929/COMMANDS.md) |
| Pose preparation and diagnostics | [`code/freeze_vipe.py`](experiments/world_lobby_four_trajectory_20260929/code/freeze_vipe.py), [`code/evaluate_and_plot.py`](experiments/world_lobby_four_trajectory_20260929/code/evaluate_and_plot.py); ORB-SLAM3 native solution is an external input |
| Sampling, DA3, geometric packets | [`code/`](experiments/world_lobby_four_trajectory_20260929/code/): `prepare_depth_samples.py`, `run_da3_depth.py`, `build_depth_packets.py`, `depth_pipeline.py` |
| Input isolation and review budget | [`astra_blender2/configs/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/configs/), `tools/prepare_inputs.py`, `tools/paired_check_blender.py` |
| Saved M1–M4 scene construction | [`astra_blender2/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/models/): builders, layouts, cameras, objects, colliders, revisions, and independent reviews |
| Freeze and independent evaluation | [`astra_blender2/tools/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/tools/): `freeze_models.py`, `evaluate_models.py`, `render_frozen_views.py`, `evaluate_blog_tables_46_blender.py` |
| Earlier model set / publication tooling | [`astra_blender/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender/models/); some `astra_blender2/tools/build_blog_*` scripts deliberately report this **other** set |

## Reproduce: choose the level you need

### 1. Verify the source and portable math — no scene assets, GPU, or credentials

Use **Python 3.10+** from the repository root (the pinned NumPy/SciPy versions do not support Python 3.8):

```bash
python3.10 -m venv .venv-core  # or another Python >= 3.10
.venv-core/bin/python -m pip install -r requirements-core.txt
.venv-core/bin/python scripts/verify_source_snapshot.py
.venv-core/bin/python scripts/check_world_lobby_depth_math.py
.venv-core/bin/python tests/test_pose_metrics.py
```

The verifier checks snapshot hashes, Python syntax, and the artifact lock. The five depth tests check window scheduling, deterministic deduplication, bilinear valid support, missing-depth penalties, and optical-Z ray conventions. Passing is **not** a reconstruction or GT-score reproduction.

### 2. Rebuild a saved scene — Blender 5.2.0, no inference or agent access

```bash
/path/to/blender --version  # expected: Blender 5.2.0
.venv-core/bin/python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/awsm-M4-rebuild
```

Choose `M1`–`M4`; use an **absent directory outside the repository**. The helper copies the saved `astra_blender2` builder and small companions, runs Blender headlessly, and checks for `scene.blend`, `scene.glb`, `objects.json`, and `colliders.json`; diagnostics go to `rebuild.log`. It creates no visual renders and does not replay agent reasoning, inference, or evaluation. Resaved binary hashes need not equal the frozen original. Do not download the root legacy HF bundle expecting these models.

### 3. Re-run inference → modelling → independent evaluation — external setup required

This is **not a one-command, self-contained reproduction**. The [practical guide](docs/AWSM_REPRODUCTION.md) gives the stage order, checked CLI examples, input inventory, isolation/freeze requirements, and known path traps. You need the exact capture and native trajectories, CUDA/upstream runtimes and model weights, original GT assets plus validated fresh GT depth, and authorized Astra access for a new agent run. Historical scripts contain absolute paths and assume sibling workspaces. Agent runs are nondeterministic; saved-builder replay and new modelling are different experiments.

## Limitations and roadmap

**Current boundaries**

- One synthetic lobby and one engineering run per route do not establish broad superiority or statistical significance.
- Geometry, appearance, uncertain/hidden structure, materials, and physical proxies have separate failure modes. All four later-run reviews retain concrete limitations.
- Input isolation is physical packet separation and method-scoped contexts, **not an OS-enforced read sandbox**. Independent GT scores must never be fed back into candidate authoring.
- Raw capture, dense predictions, weights, original GT scene, frozen model binaries, render images, and full evaluation outputs are not included in this compact source snapshot.
- The live article and preserved historical records have version/provenance differences. A shared method label or even an identical output hash does not establish which frontend produced an asset.

**Planned work — not completed features or promised benchmark gains**

- [ ] Reconcile public article/input-packet/model lineage; release run-specific asset locks and a clean data-availability index.
- [ ] Replace hard-coded workspace paths with portable configuration and publish tested, versioned frontend environments.
- [ ] Extend to real captures and multiple scenes, with repeated agent runs, matched budgets, and genuinely held-out evaluation.
- [ ] Track object/geometry uncertainty and improve fine structure, materials, lighting, and local shape rather than relying on global scale alone.
- [ ] Study persistent scene updates and multimodal spatial memory with explicit task metrics.

## Documentation, attribution, and citation

Start with [the current reproduction guide](docs/AWSM_REPRODUCTION.md) and [experiment README](experiments/world_lobby_four_trajectory_20260929/README.md). Root [REPRODUCING.md](REPRODUCING.md) and [CODEMAP.md](CODEMAP.md) also describe **older experiments**; their OpenVINS/MapAnything labels and asset lock are not the later run's recipe. Dependencies and external assets retain their respective terms in [THIRD_PARTY.md](THIRD_PARTY.md); this documentation update introduces no new license.

```bibtex
@misc{awsm_2026,
  title = {{AWSM}: Agentic World Simulation and Mapping},
  author = {{Phygital AI}},
  year = {2026},
  howpublished = {Interactive research article},
  url = {https://phygital-ai.github.io/agentic-world-simulation-and-mapping/}
}
```

For reproducible comparisons, additionally record the repository commit, experiment subdirectory, model hashes, and evaluation protocol—not only the project name.
