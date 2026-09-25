# Reproduce the World Lobby experiment

This workspace is independent of earlier experiments. The original capture, GT asset and historical M1 are read-only external inputs. The public site bundle contains results and presentation assets; it is not a copy of the complete capture or Python/model environments.

## Entry points

- `blog/index.html`: Chinese article; `blog/en.html`: English.
- `results/final_evaluation.json`: six main systems; B2p is supplementary.
- `results/rgb_metrics_five_views.json`: RGB image scores and individual frame paths.
- `results/evaluation/novel_depth/report.json`: independently raycast same-scene novel-pose depth.
- `experiments/tasks/drone_M3/photographic_20/`: all 20 drone runs.
- `experiments/tasks/g1_M3/final_margin047/`: all 30 G1 instructions, including planning failures.
- `docs/INDEPENDENT_FINAL_REVIEW.md`: implementation and interpretation audit.

## Environment used

Blender 5.2.0 CPU rendering, four threads; Cycles 16 samples for the fixed-view model evaluation. The `mapanything` conda environment runs learned depth. The existing reconstruction virtualenv supplies Open3D, NumPy, SciPy, scikit-image and Transformers. `.venv-tasks` contains MuJoCo 3.3.7 and the control dependencies. `runtime/site_python` contains only Markdown and lightweight browser-QA dependencies. None of these changes upgrades the old project environment.

On this host, the reconstruction environment needs:

```bash
export LD_PRELOAD=/home/hchen/Documents/astraBlenderTest/reconstruction/runtime/lib/libjitprofiling.so
export OMP_NUM_THREADS=4
```

Use the absolute Blender and Python paths from the saved logs on another checkout, or replace them consistently. Existing scripts record their input paths; relocate input manifests before running on another machine. Do not silently substitute a different lobby scene or a different trajectory.

## Frozen data and model provenance

`manifests/input_inventory.json`, `data/world_lobby/rgb_180_manifest.json`, and `data/packets/*/packet.json` identify the capture and the method packets. The capture has 8,999 RGB frames at 25 Hz and 89,999 IMU samples at 250 Hz; 180 RGB frames are selected at source indices 0,50,…8950. The GT wrapper `lobby.usda` includes a 0.01 unit conversion. GT evaluation verifies 9,984,967 triangles.

M2, M3, M4 source and output artifacts live in `experiments/world_lobby/M*/astra_model/`; their modelling manifests, freeze files, Python builders, semantic inventories, collision proxies, and independent reviews accompany them. The M1 source remains the historical `visual-recon/scene.blend`. Its SHA256 is `fd2ff0bc5cbc1efd47457410cd6474c9718422cccd0b60a8fb7c36e2f01c641b`.

Astra sessions were independent, with the contract in `configs/astra_modelling_contract.md`; agent choices are not deterministic. Re-executing a saved scene builder reproduces that artifact's construction, not a new model session with identical reasoning. M1's older budget differs from the new methods. OpenVINS output was fingerprinted after the full run and GT diagnostics; this is not a preregistered benchmark.

## Frontends

- ViPE: `scripts/run_full_vipe.sh`, output `experiments/world_lobby/M2/vipe_full_20260923/`. `complete.json` records all 8,999 cameras/depths and input provenance. The bounded RGB cache and resumable depth scheduling are documented in that run's `resume_provenance.json` and `phase_handoff.json`. Do not rerun SLAM merely to resume depth.
- OpenVINS: `experiments/world_lobby/M3/openvins_20260923/`, max_clones=31, full 360-second sequence. It supplies 8,784/8,999 image-associated poses and 175/180 sampled poses. Initialization failure remains missing.
- MapAnything: four-view joint windows, overlap two, bf16, 518-resolution inference. M3/M4 condition on known intrinsics and supplied poses. B2 uses RGB with known intrinsics, without external poses. Outputs and exact run configuration are in each `depth_20260923/full4_overlap2/` directory. Eight-view OOM and single-view smoke runs are diagnostics, not reported baselines.
- `scripts/prepare_astra_packet.py`, `prepare_vipe_packet.py`, and `consolidate_b2.py` prepare method packets. M3/M4 preserve supplied camera poses; B2's overlap chain is a rigid alignment without GT or scale fitting.
- `scripts/fuse_baseline.py --method B1|B2|B2p` performs TSDF fusion, voxel 0.05 m, truncation 0.15 m, maximum depth 30 m and maximum depth width 640. A different fusion setting defines a different baseline.

## Evaluate frozen models

From this workspace, with the reconstruction Python selected:

```bash
python scripts/evaluate_current_poses.py
python scripts/evaluate_packet_depth.py --packet data/packets/M2/packet.json --out results/evaluation/depth/M2_native
python scripts/evaluate_packet_depth.py --packet data/packets/M3/packet.json --out results/evaluation/depth/M3_native
python scripts/evaluate_packet_depth.py --packet data/packets/M4/packet.json --out results/evaluation/depth/M4_native
python scripts/evaluate_packet_depth.py --packet data/packets/B2/packet.json --out results/evaluation/depth/B2_native
python scripts/evaluate_frozen_model.py --method M2
python scripts/evaluate_frozen_model.py --method M3
python scripts/evaluate_frozen_model.py --method M4
blender -b --python-exit-code 1 --python scripts/evaluate_novel_depth_blender.py
python scripts/build_final_evaluation.py
```

The model wrapper invokes Blender and checks frozen source hashes. It generates fixed views, model depth, and surface metrics. Geometry uses exact nearest triangles, not nearest sampled point clouds. For metric methods, `GT_from_model = GT_from_input × inverse(model_from_input)`; `T_input_model` in the modeller manifest means model-from-input. M1 has one GT-assisted Sim(3), never native metric recovery. Frontend sharing is explicit: B1=M2, B2p=M3 for pose/depth, while final geometry differs.

GT depth validity is finite optical-Z in [0.1,30] m. Prediction coverage and 30 m missing-prediction MAE penalties are reported alongside valid-pixel errors. The mapping-depth cache's historical joint `valid` mask is not authoritative. Novel cameras use 5,000 fixed random rays each; the old compositor-derived novel Z arrays are quarantined because they fail independent BVH validation. Novel RGB is unscored due to renderer mismatch.

Pose implementation checks:

```bash
python -m pytest -q tests/test_pose_metrics.py
```

## Robot tasks — current M4 revision

Both tasks in the current article use M4. See [M4 downstream protocol and commands](M4_DOWNSTREAM_20260924.md) for the new 20-query drone experiment and 20-execution G1 language/planter experiment, independent target/visibility evaluation, and exact limitations. The reproduction ZIP retains both revisions.

### Historical M3 experiments

The following commands and results describe the earlier M3 tasks, retained unchanged for provenance; they are not the current article results.

The official Unitree asset/policy checkout is pinned at `276801e46c5d433564f24658bac64f254b7d2d4b`. The DINOv2-small weights and hashes are recorded under `runtime/visual_features/dinov2-small/`. Neither task reads GT target poses or the GT map during planning/execution. Both use simulator-state-oracle self-localization.

```bash
python scripts/run_drone_photographic_batch.py
blender -b --python-exit-code 1 --python scripts/render_drone_endpoints_blender.py
python scripts/evaluate_drone_photographs.py
```

The batch uses the reconstruction Python for DINO and explicitly launches `.venv-tasks/bin/python` for MuJoCo. Cached episode summaries are reused; use a new output directory for a genuine new experimental run. `request.json`, `retrieval.json`, `drone_world.xml`, trajectory CSV and summary are retained per episode. `final_rgb.png` comes from each achieved final camera, not an ideal target-camera render.

G1 requests, exact commands and episode outputs remain in `experiments/tasks/g1_M3/final_margin047/`. The runner is `python -m src.tasks.g1_episode --help`. OSMesa libraries are unpacked locally under `runtime/osmesa/`, with no system installation. G1 success requires model-world approach and bearing conditions; it has no independent pixel/instance verification. G1 foot points in the static GT audit are fixed base offsets, not true articulated foot geometry. Static GT clearance is not GT dynamics transfer.

Presentation videos are shaded replays/visual reruns of actual recorded dynamics. They do not provide additional task successes. Interactive GLBs are disclosed cutaways; original models and physical worlds retain walls and ceilings.

## Build and preview the site

```bash
python scripts/build_final_evaluation.py
python scripts/build_blog.py
python scripts/package_blog.py
python -m http.server 8766 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8766/`. Both languages, tables, videos, figures, local model-viewer library and lightweight GLBs are in the static bundle. The page needs HTTP for the model-viewer assets; opening a `file://` URL may trigger browser CORS restrictions.

`python scripts/qa_blog_browser.py --dist` checks both languages at desktop and mobile widths, the view selector and the interactive model. `results/site_qa/` contains screenshots and a machine-readable report. The bundle intentionally excludes runtime environments, raw full-capture frames, checkpoints, browser profiles and credentials.

## Five-view appearance metrics (Table 5)

`scripts/evaluate_appearance_lpips.py` reads the frozen five-view renders and verifies that recomputed PSNR/SSIM match their original values. It adds LPIPS for M1–M4 in a separate result directory, leaving the original images and reports unchanged. The implementation is `lpips==0.1.4`, AlexNet, learned v0.1 calibration with an ImageNet-pretrained backbone; all results average keyframes 0/36/72/108/144 at 640×480. See `results/evaluation/appearance_five_views_20260925/report.json` for per-image hashes, settings, versions and weight hashes.

Install only the added package into the isolated workspace target and run with the reconstruction Python, which already supplies Torch, torchvision, NumPy, Pillow and scikit-image:

```bash
python -m pip install --no-deps --target runtime/lpips_python lpips==0.1.4
python scripts/evaluate_appearance_lpips.py
python scripts/build_blog.py
```

On this host retain the earlier `LD_PRELOAD` setting for Torch. The evaluator defaults to a workspace-local `runtime/lpips_torch` model cache and downloads the official PyTorch AlexNet checkpoint when absent. Weight files and runtime environments are not part of the public source archive. Table 4 reads B2p geometry from the frozen `supplementary_rows.B2p` result, with no re-fitting.
