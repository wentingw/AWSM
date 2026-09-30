# Astra Blender 2 — fixed ten-view rerun

Authorized request: execute the plan-only portion of `../plan_astra_blender2.md`, build four new models with GPT-6 Astra in clean method contexts, compute the current HF Table 9/10/11 protocols, and publish metrics first. **Do not publish new model files or rendered model images.** Replace the plan's execution record only after completion.

## Completed result

All four new models were independently reviewed, rebuilt from their scripts, and frozen. Final review status: LIMITED for all methods, with no remaining technical/protocol blockers. M1 has no validated RGB-only camera registration, so its GT metrics are N/A.

- M1/M2/M3/M4: 2/3/3/2 geometry versions and 20/30/30/20 fixed paired views.
- M2–M4: exactly three full 180-frame input checks each.
- Independent 180/500 model depth and requested Tables 9/10/11 protocols: `evaluation/`.
- The remote page was renumbered during execution: former Tables 9/10/11 are now Tables 3/4/5. The page retains that numbering and labels the mapping.
- Metrics-only HF commit: https://huggingface.co/spaces/Ooliva/world-lobby-exps-new/commit/2c85afffb46f75b323f70b4af0b008df9c7268ca. All 18 changed remote files verified; Space RUNNING; existing models/images unchanged.
- New models remain under `models/M1..M4/`; no new model, source, parameter or rendered-image assets uploaded.
- Plan execution record replaced in `../plan_astra_blender2.md`.
- Desktop and mobile metrics QA passed without regression. The baseline page already has mobile document overflow; this is recorded in `report/browser_qa.json`.
- Fresh GT caches relocated from the authenticated remote snapshot, with exact original manifest hashes: `evaluation/gt_reference/` and `provenance/gt_reference_relocation.json`. All 39 source USD layer hashes match.

Current recorded status is obtained with `python3 tools/status.py`.

## Inputs and isolation

Four physical method copies in `inputs/M1..M4/`. Fixed checks: 33,61,74,82,91,100,108,118,129,155. Only clean fixed RGB identity manifests are supplied to authors; the coordinator-only original fixed-view manifest includes GT selection audit and is not supplied.

M1/M2 initial authors used fresh collaboration contexts `/root/rerun2_m1` and `/root/rerun2_m2`; M1/M2 repair contexts were recovered through fresh method-scoped CLI sessions, preserving saved evidence (see `provenance/m1_repair_recovery.json` and `m2_repair_recovery.json`). M3/M4 use fresh `codex exec -m gpt-6-astra` sessions with logs in provenance. Independent initial/final reviewers use new method-scoped CLI contexts. Filesystem access is not OS sandboxed; tool scope and actual records are retained. No evaluation feedback to authors.

## Execution tools

- `paired_check_blender.py`: ten paired RGB+Z images per version, parameter snapshot, hash validation, per-method file lock/reuse.
- `visualize_checks.py`: comparison grids, signed/absolute/relative error, masks and depth-edge differences (M1 model depth only).
- `raycast_scene.py`: own-input full180 depth pass, at most3; file lock/reuse. Exactly3 required before geometry-method freeze.
- `launch_phase.py`: fresh initial_review, repair, final_review contexts.
- `inspect_scene.py`, `validate_artifacts.py`, `verify_rebuild.py`, `freeze_models.py`: technical artifacts, semantic mapping, program regeneration, freeze gates.
- `run_frozen_evaluation.py`: requires all4 freezes, then independent180/500 opticalZ and Table9/10/11. Uses verified fresh GT from preceding regeneration, not legacy GT cache.
- `write_execution_record.py`: replace plan execution section with new measured records after all evaluation complete.
- `build_metrics_release.py`, `check_metrics_release.py`, `hf_metrics_release.py`: metrics-only delta and remote parent-commit guard, keeping model/visual hashes unchanged.

Table9:100000 area-weighted model samples to exactGT triangles;100000 observed180GT ray hits to model. Table10: five existing evaluation samples0/36/72/108/144,640x480,Cycles16,PSNR/SSIM/LPIPS. Table11:20 deterministic perturbed cameras,5000 rays per view, original protocol seed23. These evaluation protocols differ from the ten author check views.

No task is complete until four models are reviewed and frozen, evaluations complete, plan records updated, metrics-only browser validation and HF upload/hash verification pass. HF credential is read only via hidden stdin and must never enter artifacts or shell arguments.
