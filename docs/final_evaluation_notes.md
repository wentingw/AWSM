# Final evaluation definitions

The current summary is `results/final_evaluation.json`; the flat table is `results/final_evaluation.csv`. `scripts/build_final_evaluation.py` reads frozen per-method reports, computes five-view RGB scores, and builds publication figures. M1–M4, B1 and B2 are the six main systems; B2p is supplementary.

Pose uses `results/evaluation/pose/current/report.json`, native SE(3). B1 inherits M2's ViPE frontend; B2p inherits M3's OpenVINS+MapAnything frontend. M1 has no native estimated camera trajectory. M4 poses are GT input, not a pose-estimation score. M1 geometry/display uses an explicitly GT-assisted Sim(3), scale 0.6897587343, from four frozen presentation-camera associations.

Native frontend depth and rendered model depth are separate. Reported all180 and common175 use fixed GT masks; prediction coverage and a 30 m missing-prediction MAE penalty remain available. The fixed GT optical-Z domain is finite and within [0.1,30] m; usable predicted/model depth must be finite and positive, with native sampling validity checked separately. No post-hoc scale fit is applied to these depths.

Surface metrics use exact nearest triangles with 100,000 area-sampled model points. The observed reverse metric samples fixed GT image-ray hits uniformly across all180 observations; it is observation-weighted rather than area-weighted. Full-building GT-to-model distances include unobserved structures and are separately retained. M1 geometry comes from M1_observed_eval, not its earlier lower-sample diagnostic.

RGB PSNR/SSIM use five input views at 640×480. GT is downsampled with Lanczos; predicted images already have that size. scikit-image computes channel-averaged 7-window SSIM with data_range=1. No exposure, color, per-image alignment or camera fit is applied. The black M1 frame108 is included. All six main systems and B2p have RGB scores. Baked-color TSDF uses Standard display; Astra renders use their scene lighting/AgX. These differences are part of appearance error, not pose accuracy.

The 5×5 figure rows are keyframes [0,36,72,108,144], columns M1/M2/M3/M4/original simulator RGB. These are input views. The depth-error heatmap is five rows × six systems, a shared [0,1] relative-error display scale; teal marks missing or invalid predictions.

Novel-pose depth is independently implemented in `scripts/evaluate_novel_depth_blender.py`: 20 deterministic perturbations within the same synthetic scene, 5,000 fixed random rays each, seed23, exact GT-only BVH with asserted triangle count. The report stores ray samples, source hashes, transforms, masks, and pooled pixel statistics. The penalized MAE includes both valid absolute errors and 30 m per missing prediction. Old compositor Z arrays failed validation and are quarantined; novel RGB is not scored.

Task definitions are in `docs/INDEPENDENT_FINAL_REVIEW.md`. Candidate arrival differs from accurate drone rephotography. G1 reports a constrained model-world semantic approach goal, not independently verified target visibility or identity. GT static clearance does not test inside/outside or dynamics transfer; G1 foot points are fixed base-pose proxies.

## Table 4: geometry; Table 5: appearance

Table 4 contains M1–M4, B1, B2 and B2p, with Model → GT and Observed GT → model only. Model-to-GT uses 100,000 area-weighted model samples and exact nearest-triangle distance. The observed reverse metric uses 100,000 samples from valid GT ray hits across 180 cameras. B2p uses the already frozen supplementary geometry results: 1.0322355083 m and 0.6757842306 m.

Table 5 contains M1–M4 only, with PSNR, SSIM and LPIPS. All three use the same five input views [0,36,72,108,144] at 640×480, without a method-specific validity mask. Per-view PSNR is -10 log10(MSE) on RGB normalized to [0,1]; reported PSNR is the arithmetic mean of five per-view PSNRs, not PSNR of pooled MSE. SSIM uses the scikit-image uniform 7x7 window, sample covariance, K1=0.01, K2=0.03, data_range=1, default border handling, then RGB-channel and view means. PSNR and SSIM are unchanged and have been recomputed against the frozen values.

LPIPS uses `lpips==0.1.4`, AlexNet, learned v0.1 calibration weights and an ImageNet-pretrained backbone, in evaluation mode on CPU float32. `normalize=True` converts [0,1] tensors to [-1,1]; spatial=False gives one score per pair, and the table averages five scores. No extra crop, resize, mask or color fitting is used. GT alone is Lanczos-downsampled from 1280×960 as for PSNR/SSIM. The black M1 frame remains included. Lower LPIPS is better; it is not restricted to [0,1]. Input hashes, weight hashes, per-view scores and dependency versions are in `results/evaluation/appearance_five_views_20260925/report.json`. An identical-image check returns zero. Baseline RGB scores remain available in the original full RGB report, outside the new Table 5.

The previous novel-depth, task and asset tables are now Tables 6, 7 and 8.

B1 fuses input RGB into vertex colors rendered as unlit emission with Standard color management. Astra uses generated materials and scene lights. B1 therefore reuses observed appearance at these same input views. Its better PSNR/SSIM does not establish better geometry or held-out-view generalization, and this experiment does not separately quantify color reuse and rendering-domain effects.

## Audited frontend implementations

M2/B1 use RGB-only ViPE with GeoCalib initialization, optimized intrinsics, DROID-style learned SLAM, frontend/backend bundle adjustment and pose infill. UniDepth V2 small (lpiccinelli/unidepth-v2-vits14) is the keyframe depth prior. Final adaptive_unidepth-s depth for the 180 sampled views uses SLAM-map-prompted PriorDA: an independent CPU reproduction of the frozen map projection yields minimum UV coverage 0.79, above 0.3. This reproduction mirrors the source geometry logic; it is not a saved runtime log or rerun of depth inference. No Video Depth Anything is enabled. The separately scheduled remaining frames skip index zero and retain the local branch score's default 1.0, also selecting PriorDA. The sampled-view branch is explicitly computed at index zero.

M3/B2p use RGB, calibrated intrinsics and OpenVINS metric camera-to-world input poses to condition MapAnything optical-Z depth. All 175 packet poses match OpenVINS, and depths pass unchanged into the packet; no GT scale fit is used. The trajectory plot measures these OpenVINS poses, without MapAnything pose feedback. The audit verifies data correspondence and body-to-camera conversion, not physical RGB/IMU synchronization or calibration accuracy. See pipeline_audit.json for independent checks and provenance hashes.

## Modelling reference and iteration accounting

Every method had 180 available sampled RGB references. M2/M3/M4 produced 5/3/4 complete scene versions, including the initial build, and 25/15/20 checking renders. Thus post-initial modification counts are 4/2/3. They share a five-version, sixty-render maximum, but actually use different budgets and different checking frame IDs. Historical M1 has no verified iteration count and is outside this common budget contract.

M2's analysis program reads 180 RGB files, which is not proof of 180 visual image deliveries to Astra. M3's RGB access log records 111 frame IDs with mixed contact-sheet, visual and SIFT purposes. M4 programmatically reads 180 RGB images and explicitly lists 34 personally inspected frames. No identical visual or token budget can be claimed. See modelling_protocol_audit.json for counts and frozen-source hashes.
