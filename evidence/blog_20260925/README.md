# Current blog evidence · 25 September 2026

Public blog: https://wentingw.github.io/astra-world-model-blog/

Frozen public commit: `cd63134103e1f14660d00fd4d20988f25cbf50ea`.

## Article tables and their source records

| Table | Subject | Source in this repository |
| --- | --- | --- |
| 1 | Four methods and inputs | `blog/templates/article.zh.md`, `configs/astra_modelling_contract.md`, `docs/pipeline_audit.json`, modelling manifests |
| 2 | Pose/native/model depth; M1–M4, B1/B2/B2p | `results/final_evaluation.json`, `results/evaluation/pose/`, `results/evaluation/depth/` |
| 3 | Pose and depth coverage | `results/final_evaluation.json`, `docs/pipeline_audit.json`, `revisions/scene_comparison_20260924/m2_uv_coverage_reproduction.json` |
| 4 | Model → GT and observed GT → model geometry | `results/final_evaluation.json` (B2p is the supplementary row), `results/evaluation/geometry/*/surface_metrics.json` |
| 5 | M1–M4 PSNR/SSIM/LPIPS on five input views | `results/evaluation/appearance_five_views_20260925/{report.json,per_view.csv,means.csv}` |
| 6 | Novel-view depth | `results/evaluation/novel_depth/report.json` |
| 7 | M4 drone and G1 | `results/evaluation/tasks/m4_downstream_20260924/report.json` |
| 8 | Frozen complete models | `artifact-lock.json` (HF access required) |

## M4 task evidence

The scene SHA256 is `cc6cb605246a255d94e36b9dc3f8b91d5a292b047470bc0ff75b8a5c404b0cfe`. All measurements remain frozen; this synchronization does not rerun or improve an experiment.

- Drone: `experiments/tasks/drone_M4/replay_20260924/`, 20 episode requests, summaries, retrieval decisions, trajectories and final RGB. Thirty candidate renders are in `experiments/tasks/drone_M4/view_cache/`; twenty reference photographs are in `experiments/tasks/frozen_inputs/photographic_mapping_queries/`. Metrics are in `results/evaluation/tasks/drone_M4_20260924/`.
- G1: `experiments/tasks/g1_M4/replay_20260924/`, 20 episodes with compact and full joint-state trajectories. Intended-instance IDs, endpoint RGB and visibility masks are in `results/evaluation/tasks/g1_M4_20260924/`.
- Presentation: `blog/assets/m4_tasks/` has two display-only replays, posters and provenance. `figures/m4_tasks/` has the workflow and result panels. Only the final material-grouped display OBJ files are included, via the published source archive's allowlist.
- Independent audits: `revisions/m4_downstream_20260924/`; full steps and limits: `docs/M4_DOWNSTREAM_20260924.md`.

The file named `photographic_reference_truth_private.json` is evaluator-only ground truth. “Private” describes separation from the controller; it is not an authentication secret. Do not feed it to retrieval or navigation.

## Appearance evidence

All 20 predicted images and the five original GT RGB files referenced by the LPIPS report are included with their original bytes. Views are `[0,36,72,108,144]`, scored at 640×480 with the preprocessing recorded in the report. These are input views, not held-out appearance evaluation. LPIPS uses learned v0.1 calibration on an ImageNet-pretrained AlexNet backbone, not random weights. Checkpoints remain external.

## File provenance and missing large assets

`../../source_snapshot.json` hashes the original source/evidence files. `published_files.json` hashes all 204 files in the deployed website. `display_asset_lock.json` provides fixed-commit URLs, sizes and hashes for omitted display GLBs and the published source ZIP. Full Blender scenes and original model GLBs use `../../artifact-lock.json`; the HF dataset remains private. The HF snapshot predates the current M4 tasks and LPIPS scores, which are stored here in Git.

Raw capture video/IMU, full GT scene, pretrained checkpoints, runtime environments and large dense depth arrays are not all included in this source snapshot. Re-running the full pipeline needs the sources and environments listed in `../../REPRODUCING.md`; installing the portable core alone is insufficient. Historical absolute paths are preserved, so relocate a working copy before running jobs. Source HTML preserves workspace-relative links and needs externally pinned display assets for a complete local viewer.

## Quick audit

```bash
python scripts/verify_source_snapshot.py
python scripts/audit_blog_snapshot.py
```

These commands are read-only and run with the Python standard library. They verify frozen evidence integrity and aggregation; they do not claim a fresh simulation or fresh neural-network evaluation.
