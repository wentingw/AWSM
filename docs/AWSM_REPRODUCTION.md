# AWSM reproduction and evidence guide / 复现与证据指南

This guide concerns `experiments/world_lobby_four_trajectory_20260929`, especially the **`astra_blender2` fixed ten-view run**. It supplements the [English README](../README.md) and [中文 README](../README.zh-CN.md). It does not replace the byte-preserved historical records or claim a new full-pipeline execution.

**中文速览：** 先选复现层级：①无需数据的源码/数学检查；②使用 Blender 5.2.0 重建保存程序；③准备外部采集、轨迹、权重、GT、智能体权限并重定位路径后，独立重跑全流程。下文所有全流程命令均为完成这些前置条件后的示例，不是从空机器一键安装。最新十视角轮次与文章展示模型不同，不能混用指标或哈希。

## Which results belong to which models

| Evidence family | What it identifies | Safe use |
| --- | --- | --- |
| `astra_blender2/models/` and its final reviews | Later fixed ten-view run; M1/M2/M3/M4 versions 2/3/3/2 | Saved-program rebuild; README results |
| Saved `astra_blender2/report/space/index.html`, Tables **3–5** | Later-run surface, five-view appearance, perturbed-view depth; original requested Tables 9–11 | Historical numeric evidence; raw linked JSON/CSV absent from Git |
| Earlier Table 2 and mixed media in that same HTML | Other model/report lineage | Do **not** assume all content in this HTML is the later run |
| Official article `data/tables_1_7.json` | Explicit scope: `astra_blender/models/M1..M4` | Published article only; not later-run performance |
| `tools/build_reference_style_figures.py` | Explicitly renders `astra_blender/models`, despite tool location | Explains why article pictures do not illustrate the rebuild helper's scenes |
| Root `artifact-lock.json` and `experiments/world_lobby/` | Earlier release, including OpenVINS/MapAnything history | Historical audit only; not a September 29 asset installer |

The later-run HTML is [tracked here](../experiments/world_lobby_four_trajectory_20260929/astra_blender2/report/space/index.html). [ten-view-results.json](awsm/ten-view-results.json) is a small, explicitly labelled transcription of its displayed Tables 3–5, accompanied by source hash and final-review identities. [ten-view-results.svg](awsm/ten-view-results.svg) plots that transcription; it is a numerical illustration, **not a Blender render**. Table numbers alone are insufficient provenance.

### Later-run frozen Blend identities

These hashes come from the included independent final reviews, not newly rebuilt files:

| Method | Version | Paired checks | Full 180-frame input passes | Blend SHA256 |
| --- | ---: | ---: | ---: | --- |
| M1 | 2 | 20 | 0 (RGB-only) | `747b24362a5c0a2d71d24499a0e82cdc8a1f4595fc9e724a7da5c0d192708f63` |
| M2 | 3 | 30 | 3 | `8f80d6299b98743be2151788827528ed8c4fa714ca8490f9797b52cc2c24177a` |
| M3 | 3 | 30 | 3 | `5e6e6e373472762e0f96efecf4fa5a8912a3b4657cb1061842e0c34288bad15e` |
| M4 | 2 | 20 | 3 | `a86c6656bfd7f3ff1435c037a48aecb1d503047b799d75c9fc5524baba5c5ec5` |

All reviews are `LIMITED`. M1 has no reliable frozen RGB-only camera registration, so its independent GT table entries remain N/A. Do not borrow the article's GT-assisted M1 Sim(3) to fill them in.

### Live publication checks (October 1, 2026, Hong Kong time)

The official [English](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/) and [Chinese](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html) pages, `#figure-3` 3D viewer anchor, and `#figure-4` image-comparison anchor were verified in live HTML. The article's [five-view image](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/assets/fixed_five_view_comparison_m1_m4.jpg) returned 1,755,470 bytes with SHA256 `501a674252a492deb209a9cfd847e8f0c83103c49d5f250964ee451d233481a9`, matching its [publication manifest](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/evidence/publication_manifest.json). It is embedded remotely rather than adding another large image to Git. HTTP/asset checks are not a browser/GPU rendering acceptance test.

The [official provenance note](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/evidence/provenance-note.md) explicitly records a naming conflict: article M4 uses a Blend hash also described historically as MapAnything-conditioned; M3 naming differs too. This is **unresolved provenance**, not permission to relabel historical evidence. The README therefore does not import the article's headline surface/depth values as later-run results. Its robot video likewise is not a successful result of this source release.

Anonymous requests for the original HF Space metadata and raw report returned **401**. Authorized access may be needed; availability is not guaranteed. GitHub access does not imply HF dataset access. The older root downloader/lock does not fetch these later scenes. No credentials or gated assets are required for levels 1–2 below.

## Level 1 — source and math checks / 源码与数学检查

**Requirements:** Python 3.10+; NumPy 2.2.5 and SciPy 1.15.3 from the root requirements. No Blender, GPU, capture, model weights, or service credentials.

From the repository root:

```bash
python3.10 -m venv .venv-core  # Python 3.11/3.12 also suitable
.venv-core/bin/python -m pip install -r requirements-core.txt
.venv-core/bin/python scripts/verify_source_snapshot.py
.venv-core/bin/python scripts/check_world_lobby_depth_math.py
.venv-core/bin/python tests/test_pose_metrics.py
```

**Expected:** verifier JSON reports `status: pass`; depth suite reports five tests `OK`; pose script prints `PASS`. The verifier checks the original plus supplemental byte-preserved snapshots, runnable Python syntax, and artifact lock. New root documentation/portability helpers are Git-tracked separately. The depth wrapper deliberately selects only asset-free tests; the entire historical test module additionally needs omitted data.

**Not established:** inference quality, exact scene binaries, rendered images, GT evaluation, or robot execution. If installation fails on Python 3.8, select a supported interpreter instead of weakening pins or changing the system environment.

## Level 2 — saved scene reconstruction / 保存场景重建

**Requirements:** level-1 host Python and Blender **5.2.0**; the recorded run contract identifies build `fbe6228777e7`. Blender supplies `bpy`, `bmesh`, and `mathutils` itself. Do not pip-install these as a substitute. Saved builders use included layouts/cameras/measurement companions, not raw RGB or DA3 arrays.

```bash
/path/to/blender --version
.venv-core/bin/python scripts/rebuild_world_lobby_scene.py --help
.venv-core/bin/python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/awsm-M4-rebuild
```

`--method` accepts `M1`, `M2`, `M3`, `M4`. `--blender` defaults to `BLENDER_PATH` if set, otherwise executable `blender`. `--output` is required: it must not already exist and must be outside this repository. The helper refuses an in-repository destination; do not defeat that guard.

The helper copies `.py`, `.json`, and `.npy` companions (excluding independent reviews and caches), creates output folders, and executes:

```text
blender --background --factory-startup --threads 2 --python-exit-code 1 --python OUTPUT/build_scene.py
```

**Expected outputs:** `scene.blend`, `scene.glb`, `objects.json`, `colliders.json`, plus `rebuild.log` and the builder's other metadata. A nonzero Blender exit or missing required artifact fails the helper. On failure inspect `rebuild.log`, then use a new output directory for retry rather than overwriting a previous result.

Open the generated Blend in Blender or GLB in a compatible viewer to inspect it. This helper does not render validation images, run the Astra loop, or score against GT. File-existence checks are not geometric or visual equivalence checks; resaving can change binary hashes. Independent evaluation against **historical** scores needs the exact frozen assets/hashes, not a newly saved binary silently treated as identical.

Blender 5.2.0 was not available in the documentation QA environment; the helper interface was verified, but a new Blender rebuild is **not claimed** in this update.

## Level 3 — full pipeline / 完整推理、建模与评测

### External input and environment checklist

| Needed component | Recorded identity / location | Included? / action |
| --- | --- | --- |
| Original capture | `lobby_orb_success_20260929T123153`; 4,499 RGB frames, 44,999 IMU samples; camera 25 Hz, IMU 250 Hz | Not bundled. Obtain RGB/CSV/video/calibration and verify `contract.json` hashes |
| Calibration and timing | 1280×960; fx=fy=762.8, cx=640, cy=480; nanosecond simulation timestamps; IMU FRD and optical camera conventions | Metadata included. Preserve transform direction and timestamp units |
| Native trajectories | ORB-SLAM3 frozen `camera.npz` hash in contract; full-video ViPE configuration in `COMMANDS.md` | Native solutions and full estimator stack external; ORB-SLAM3 runner is not provided as a portable recipe here |
| Sampling schedule | `data/depth_samples/modeling_180.json` and `eval_500.json` | Included metadata; 180 modelling and 500 disjoint depth-evaluation identities; referenced RGB external |
| DA3 inference | `depth-anything/DA3-GIANT`, recorded snapshot `7cd62ae9315b9dff094d2d300e4ad012640607dd`, `model.safetensors`; vendor adapter `vipe_official_95a8816` | Weights, vendor package, torch/CUDA runtime external. `--weights` can relocate the checkpoint; record and verify hashes |
| Modelling packets | `packets/M2..M4/packet.json`, `astra_blender2/inputs/M1..M4/packet.json` | JSON included; RGB/geometry NPZ omitted. Verify referenced hashes, do not substitute another run's data |
| Agent author/reviewer | Recorded model `gpt-6-astra`, method-scoped fresh contexts | Service/model access and authorized credentials external. Never put secrets in tracked files or command arguments |
| GT scene and depth | Original World Lobby USD with referenced assets; validated fresh 680-view cache `gt_fresh_20260930T021632Z` in recorded contract | Not bundled. Rebuild and validate fresh optical-Z; no old cache substitution |
| Analysis/appearance | `requirements-analysis.txt`; compatible torch/torchvision, `lpips==0.1.4`, LPIPS AlexNet v0.1 weights | Optional requirements are not a full lock; provisioning and licensed weights are separate |
| Frozen evaluation inputs | Exact scene binaries, freeze manifests, registration/camera JSON, GT manifest and ray validation | Some small source records included, but required full evaluation bundle is absent |

See the [capture contract](../experiments/world_lobby_four_trajectory_20260929/contract.json), [run contract](../experiments/world_lobby_four_trajectory_20260929/astra_blender2/configs/run_contract.json), [modelling contract](../experiments/world_lobby_four_trajectory_20260929/astra_blender2/configs/modelling_contract.md), and [historical commands](../experiments/world_lobby_four_trajectory_20260929/COMMANDS.md) before provisioning. Use normal provider login mechanisms; no token is embedded or required in this documentation. An unavailable recorded agent model is a reproduction blocker, not justification for silently substituting another model and calling it the same run.

### Relocate in a separate working copy

Do not execute historical tools over frozen source/result directories. Choose a new work root and copy the experiment there. Several tools derive paths assuming this sibling layout:

```text
WORKROOT/
  world_lobby_four_trajectory_20260929/
  vio-reconstruction/sessions/lobby_orb_success_20260929T123153/
  stable_orbit_orb_success_20260929/
  world_model_blog/
  reconstruction/
  drone-web/
```

Inspect absolute paths without executing them:

```bash
grep -R -n '/home/hchen/' \
  experiments/world_lobby_four_trajectory_20260929 \
  --include='*.py' --include='*.json' --include='*.md'
```

`code/depth_pipeline.py` uses `Path(__file__).resolve().parents[2]` as the shared workspace root. In the compact checkout that points to `experiments/`, where the omitted siblings do not exist. `run_da3_depth.py` derives its vendor/checkpoint paths from that root. Other tools directly hard-code Blender, analysis Python, GT USD, and report paths under `/home/hchen/...`; not every script has a `--root` option. **Changing only the shell working directory is insufficient.** Relocate source paths, packet entries, and output destinations consistently in the new copy; keep an explicit relocation map and retain the original hashes. Rewriting metadata changes its hash, so record both original identity and relocated copy rather than pretending bytes are unchanged.

### Stage order and checked entry points

The following are **conditional examples after provisioning and relocation**, not commands to run unmodified in the compact checkout. Use the correct estimator/CUDA/analysis interpreter for each stage. Let `EXP` point to the relocated experiment; do not point it at your frozen original.

1. **Capture/pose inputs:** verify the contract, obtain or rerun native ViPE/ORB-SLAM3 trajectories, then freeze their hashes before GT pose diagnostics. `COMMANDS.md` records ViPE's `no_vda` pipeline, full native RGB, UniDepth-S configuration, and freeze commands. OpenVINS is optional trajectory comparison evidence, not the M3 scene frontend. The saved scripts do not constitute a complete portable ORB-SLAM3 build/install pipeline.
2. **Sampling and DA3:** preserve the deterministic disjoint 180/500 schedules. DA3 uses four-view windows, process resolution 392 (the historical 504 setting exceeded the available 10 GB GPU), and native pose scale. `DA3METRIC-LARGE` is not this model and lacks the required camera encoder.

```bash
# Run with the provisioned DA3/CUDA interpreter, after relocation.
python "$EXP/code/run_da3_depth.py" \
  --method M4 --split modeling_180 --window-index 0 \
  --weights /absolute/path/to/model.safetensors --process-res 392 --device cuda

# After validating the smoke window, complete both splits for M2, M3 and M4.
for method in M2 M3 M4; do
  for split in modeling_180 eval_500; do
    python "$EXP/code/run_da3_depth.py" \
      --method "$method" --split "$split" \
      --weights /absolute/path/to/model.safetensors --process-res 392 --device cuda
  done
  python "$EXP/code/build_depth_packets.py" --method "$method" --split both
done
```

3. **Input packet preparation:** `astra_blender2/tools/prepare_inputs.py` checks all 680 RGB hashes and copies method-specific RGB/geometry evidence. Treat it as a **new-run coordinator tool**: it writes directories and a run contract and must not be run over the saved snapshot. M1 gets RGB/intrinsics only; M2–M4 get their own native poses and predicted DA3. No GT depth or other method's evidence goes to authors. Sampling selection audit files are coordinator-side, not unrestricted author inputs.
4. **Fresh agent construction and independent review:** follow the modelling contract instead of blindly running historical `launch_*` wrappers. Those wrappers contain runtime-specific agent CLI and permissive sandbox settings, not a portable requirement or a recommendation to disable safeguards. Use an authorized environment with explicit method-scoped access. Start each author from an empty scene; preserve logs and independent reviewer identities. At most five versions; every version checks **33/61/74/82/91/100/108/118/129/155**. M2–M4 perform exactly three full 180-frame input-depth passes. Separate input copies do not enforce OS-level isolation. New agent runs are nondeterministic.
5. **Freeze all candidates:** `tools/validate_artifacts.py`, the independent final reviews, and `tools/freeze_models.py` form the saved gate. Only reviewed, technically valid candidates may enter independent GT evaluation. Retain hashes for all files named in each `freeze_manifest.json`. A saved builder replay does not regenerate omitted reviews/check evidence or confer frozen status on new artifacts.
6. **Independent GT generation and scoring:** prediction hashes must be frozen before native-depth GT evaluation; candidate scenes must be frozen before scene GT scores become available. Only the evaluator may read GT geometry/depth. Use original USD dependencies and validate optical-Z/camera rays, then run the appropriate scoring scripts. Do not feed scores back to authors.

```bash
# Only with the original GT scene/assets provisioned and paths relocated.
/path/to/blender --background --python-exit-code 1 \
  --python "$EXP/code/generate_gt_depth_blender.py" -- --split modeling_180
/path/to/blender --background --python-exit-code 1 \
  --python "$EXP/code/generate_gt_depth_blender.py" -- --split eval_500
python "$EXP/code/evaluate_da3_depth.py" --split modeling_180
python "$EXP/code/evaluate_da3_depth.py" --split eval_500
python "$EXP/code/verify_depth_pipeline.py" --require-results

# Later-run scene depth: requires all exact frozen binaries/manifests and
# a fresh GT root with manifest.json + ray_validation.json + both depth splits.
python "$EXP/astra_blender2/tools/evaluate_models.py" \
  --gt-root /absolute/path/to/validated-fresh-gt \
  --out /absolute/path/to/new-empty-depth-evaluation
```

**GT cache compatibility is an additional blocker:** `code/generate_gt_depth_blender.py` above writes per-split native-depth caches under `evaluation/depth/gt/`. It does **not** itself produce the aggregate fresh-cache `manifest.json` and `ray_validation.json` required by `astra_blender2/tools/evaluate_models.py`. The complete fresh-cache assembly/validation recipe is not present in this snapshot. Obtain the recorded validated bundle or implement and independently validate a compatible fresh-generation pipeline; do not hand-write PASS metadata to bypass the evaluator's checks.

`evaluate_models.py` validates GT completion/`old_gt_read=false`, ray validation, freeze hashes, and camera/pixel matching. It internally invokes Blender using a historical hard-coded executable path—relocate that too. `run_frozen_evaluation.py` orchestrates more stages but likewise hard-codes paths and outputs; inspect and adapt it rather than assuming it is a turnkey launcher.

For Table 4 appearance, the actual rendering interface is:

```bash
/path/to/blender --background --factory-startup --python-exit-code 1 \
  --python "$EXP/astra_blender2/tools/render_frozen_views.py" -- \
  --model /absolute/path/to/exact-frozen-scene.blend \
  --cameras /absolute/path/to/gt_cameras_modeling_180.json \
  --registration /absolute/path/to/registration.json \
  --out /absolute/path/to/new-render-directory \
  --indices 0,36,72,108,144 --samples 16 --device CPU --threads 2
```

Specify `--indices`: the standalone renderer's default is **0,45,90,135,179**, not the five-view table protocol. After rendering, `evaluate_blog_table5.py` computes the historical appearance stage (its filename predates report renumbering). `evaluate_blog_tables_46_blender.py` takes `--run`, `--gt-usd`, `--gt-depth`, and `--out` for surface/perturbed-depth evaluation; its optional `--model-root`, `--methods`, `--registrations`, and `--cameras` must refer to the same model family. The public seven-table article builder can intentionally select **earlier** models. Verify model hashes, not filenames/table numbers, before merging results.

7. **Audit outputs, not merely exit codes:** verify scene hashes stayed unchanged, GT cache and registration hashes match, M1 remains N/A when registration is unavailable, all view/sample identities and units match, and missing predictions retain penalties. Save per-view metrics alongside aggregates. Publishing is a separate explicit action; **do not run** `hf_metrics_release.py`, `build_hf_release.py`, or other upload tools just to reproduce a local result.

## Known blockers and honest completion criteria / 阻塞与验收

| Symptom | Meaning / action |
| --- | --- |
| Snapshot hash mismatch | Check checkout/revision/local modifications; do not regenerate manifests merely to hide a mismatch |
| `ModuleNotFoundError: numpy` / unsupported wheel | Use a supported isolated Python and install the pinned core requirements |
| Blender not found or wrong version | Supply an actual Blender 5.2.0 executable; interface inspection is not a rebuild |
| Output directory exists | Choose a new destination; preserve previous evidence |
| Missing RGB, geometry NPZ, GT USD, freeze manifest | Compact source release is incomplete for that stage; obtain exact authorized inputs, not a similarly named historical bundle |
| HF 401/403 | Access is gated/unavailable; use an authorized account through normal login, never paste credentials into source or chat |
| Inference/agent model unavailable | Record the blocker; a substitute model is a new experiment |
| Article numbers disagree with local later-run report | First compare model family and hashes. Do not merge or “correct” one using the other |
| Good geometry but poor RGB, or vice versa | Report both; materials/lighting and geometry are different error sources |

**Completion claims must name the level:** “source/math checks passed,” “saved program rebuilt,” or “fresh inference/modelling/evaluation completed with these inputs and hashes.” None implies the next level. 本指南不把数学单测、文件存在、静态页面可访问或媒体导出，等同于全流程复现、视觉验收或机器人成功。
