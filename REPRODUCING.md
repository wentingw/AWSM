# Reproducing and auditing SceneWeft

This is a source and evidence snapshot of the World Lobby experiment. Its portable evaluation core and verification utilities run from this checkout. The complete historical pipeline also needs the original capture, GT assets, upstream packages, calibrated environments and relocated paths. It is not a tested one-command installer.

## Verify the source snapshot

Use Python 3.10 or newer from the repository root:

```bash
python scripts/verify_source_snapshot.py
python -m venv .venv-core
.venv-core/bin/python -m pip install -r requirements-core.txt
.venv-core/bin/python tests/test_pose_metrics.py
```

The verifier checks the bytes and SHA256 of all files listed in the original 1,122-file `source_snapshot.json` and its linked supplemental snapshot manifests, parses every runnable Python file, and checks the artifact lock. The pose checks cover alignment and relative-pose invariance, quaternion sign equivalence, timestamp endpoint rounding, and rejection of trajectories without overlap. Passing these checks does not re-execute reconstruction or robot tasks.

`source_snapshot.json` maps each preserved file to its historical origin. Root project documentation and new portability helpers are separately tracked by Git. The original experiment workspace and legacy experiments remain unchanged.

## Download the exact hosted models

The HF dataset is currently private (verified 2026-09-23). Access requires a permitted Hugging Face account. Use `--auth` to read `HF_TOKEN` from your environment, or install `huggingface-hub` and use an existing `hf auth login` session. Tokens are not passed in command arguments or saved by this tool. Without `--auth`, requests are anonymous and work only if the dataset is public. GitHub collaborator access does not automatically grant HF dataset access.

The downloader uses the immutable revision in `artifact-lock.json`, verifies the manifest hash before interpreting it, and verifies each downloaded file's size and SHA256. Existing matching files are reused; mismatched files are refused.

```bash
python scripts/fetch_artifacts.py --auth --list
python scripts/fetch_artifacts.py --auth --group models --output assets
# Optional: all published evidence, models, figures and task artifacts (~759 MB).
python scripts/fetch_artifacts.py --auth --group all --output assets
```

This HF revision preserves the original frozen models; it does **not** include the later M4 task or LPIPS update. Those results and sources are included directly in Git. Display-only GLBs are separately pinned in `evidence/blog_20260925/display_asset_lock.json`.

The eight original Blender/GLB artifacts are written under `assets/models/M1/` through `M4/`. Open a `scene.blend` in Blender 5.2.0 to inspect the frozen output. The assets retain the upstream publication layout; the downloader does not rewrite input manifests or unpack source archives.

HF dataset: https://huggingface.co/datasets/Ooliva/astra-world-model-blog

Pinned revision: `241d313a264a3353bcb87f9fde30f7ef8a6f5bce`.

## Re-run a measurement or historical pipeline stage

1. Read [the recorded experiment procedure](docs/REPRODUCIBILITY.md), [metric protocol](docs/evaluation_protocol.md), and [final interpretation notes](docs/final_evaluation_notes.md).
2. Obtain the exact raw capture and GT scene identified by `manifests/input_inventory.json`. They are not fully redistributed here or in the HF bundle. Check input hashes, units and camera convention before comparison.
3. Provision the separate environments in `environments/observed.json`. This records observed components, not a complete cross-platform dependency lock. CUDA, ROS/OpenVINS and Blender are separate runtimes; installing `requirements-core.txt` is insufficient for them.
4. Work in a new experiment copy. Historical scripts/manifests contain absolute `/home/hchen/...` paths and output paths; inventory them with `rg '/home/hchen/' src scripts configs data experiments integrations`. Update executable, capture, model, calibration and output paths consistently in that new copy. Keep original snapshot checksums intact.
5. Follow the saved run configurations and entry points in [CODEMAP.md](CODEMAP.md). Create output/log directories before running. With Blender use `--python-exit-code 1` so failures propagate to the caller.

For the portable trajectory CLI, create a JSON file containing `method_id`, `pose_path` and `gt_pose_path` pointing to TUM trajectories (`timestamp tx ty tz qx qy qz qw`), then run:

```bash
.venv-core/bin/python scripts/evaluate_pose.py --manifest /path/to/manifest.json --out /path/to/pose-report.json
```

Do not treat rendering scores as pose errors. M1 has no native pose estimate; its GT-assisted Sim(3) is a diagnostic shape/display registration. M4 consumes GT pose as an oracle input and is not scored as an estimated zero-error trajectory. M2/B1 and M3/B2p respectively share their camera/depth frontend, so their trajectories coincide by construction.

## Agent sessions and task replay

Saved Blender builders preserve construction actions, measurements and frozen models. Executing a builder is not equivalent to reproducing the model's reasoning. Independent Astra sessions are nondeterministic; M1 also had a different historical budget. See `configs/astra_modelling_contract.md` and the modelling manifests.

The current M4 task snapshots include all 40 episode requests, summaries and trajectories in Git, plus the reference/candidate/endpoint images, G1 visibility masks and two presentation videos. See `docs/M4_DOWNSTREAM_20260924.md`. Both controllers use simulator-state self-localization. Drone arrival and exact rephotography are distinct outcomes. G1 target identity and mesh visibility are checked independently from navigation, but are not learned visual recognition or real-robot transfer. Earlier M3 records are historical evidence. The pinned HF release predates this M4 task revision; current task evidence is in this Git repository.

## Historical diagnostics

Three superseded novel-depth diagnostics are preserved as `.py.txt` in `archive/superseded_diagnostics/`. One has invalid syntax; their camera/depth assumptions are not authoritative. They are evidence of the audit trail, not runnable benchmark entry points. Use `scripts/evaluate_novel_depth_blender.py` and `results/evaluation/novel_depth/report.json` for the reported novel-view depth evaluation.

## Blog source

`blog/` includes the bilingual article and templates. Rendering/package scripts depend on the full original asset layout; this compact source checkout alone is not a self-contained website bundle. The already-published site is https://wentingw.github.io/astra-world-model-blog/. Do not run historical publishing commands to create or overwrite a release.

## Audit the current article without running Blender or robots

```bash
python scripts/verify_source_snapshot.py
python scripts/audit_blog_snapshot.py
# NumPy needed; recalculates G1 path length, approach and bearing from saved states.
python revisions/m4_downstream_20260924/verify_g1_results.py
```

The standard-library audit checks all 20 LPIPS input-pair hashes and score means, drone outcomes/thresholds, G1 identity/visibility records and both pages' table numbering. It verifies saved evidence, not fresh LPIPS inference or physics. The preserved independent check scripts document the deeper evaluations. To re-run LPIPS install the versions recorded in its report, obtain the exact weight hashes, and follow `scripts/evaluate_appearance_lpips.py`; no model checkpoint or Python environment is vendored here.

See [the current evidence index](evidence/blog_20260925/README.md) for the table-to-file map. `published_files.json` records the SHA256 of every deployed file at the fixed public commit. Source article files use the workspace layout and can differ from deployed copies due to link rewriting. `source_snapshot.json` preserves the original workspace bytes; the published ZIP rewrites paths and normalizes text, so its bytes can differ without changing the experimental values.

## September 29 / fixed ten-view modelling run

The [new experiment snapshot](experiments/world_lobby_four_trajectory_20260929/README.md) is preserved separately and uses the updated ViPE/ORB-SLAM3 + DA3 methods. The main verifier includes its byte-identical source manifest. Run the existing portable depth tests with `python scripts/check_world_lobby_depth_math.py`.

To rebuild one of the latest M1–M4 scene programs from included small companions, use `python scripts/rebuild_world_lobby_scene.py --method M4 --blender /path/to/blender --output /tmp/sceneweft-M4` with a new output directory. This rebuilds saved construction code without renders or a new Astra session. Full pipeline execution additionally requires the original capture, estimator solutions, GT scene and runtime dependencies, plus path relocation; it is not a one-command reproduction. The older pinned asset lock is unchanged and does not identify these newly authored scene binaries.
