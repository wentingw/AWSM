# Final evaluation definitions

The current summary is `results/final_evaluation.json`; the flat table is `results/final_evaluation.csv`. `scripts/build_final_evaluation.py` reads frozen per-method reports, computes five-view RGB scores, and builds publication figures. M1–M4, B1 and B2 are the six main systems; B2p is supplementary.

Pose uses `results/evaluation/pose/current/report.json`, native SE(3). B1 inherits M2's ViPE frontend; B2p inherits M3's OpenVINS+MapAnything frontend. M1 has no native estimated camera trajectory. M4 poses are GT input, not a pose-estimation score. M1 geometry/display uses an explicitly GT-assisted Sim(3), scale 0.6897587343, from four frozen presentation-camera associations.

Native frontend depth and rendered model depth are separate. Reported all180 and common175 use fixed GT masks; prediction coverage and a 30 m missing-prediction MAE penalty remain available. Predicted/model optical-Z must be finite in [0.1,30] m. No post-hoc scale fit is applied to these depths.

Surface metrics use exact nearest triangles with 100,000 area-sampled model points. The observed reverse metric samples fixed GT image-ray hits uniformly across all180 observations; it is observation-weighted rather than area-weighted. Full-building GT-to-model distances include unobserved structures and are separately retained. M1 geometry comes from M1_observed_eval, not its earlier lower-sample diagnostic.

RGB PSNR/SSIM use five input views at 640×480. GT is downsampled with Lanczos; predicted images already have that size. scikit-image computes channel-averaged 7-window SSIM with data_range=1. No exposure, color, per-image alignment or camera fit is applied. The black M1 frame108 is included. All six main systems and B2p have RGB scores. Baked-color TSDF uses Standard display; Astra renders use their scene lighting/AgX. These differences are part of appearance error, not pose accuracy.

The 5×4 figure rows are keyframes [0,36,72,108,144], columns M1/M2/M3/original simulator RGB. These are input views. The depth-error heatmap is five rows × six systems, a shared [0,1] relative-error display scale; teal marks missing or invalid predictions.

Novel-pose depth is independently implemented in `scripts/evaluate_novel_depth_blender.py`: 20 deterministic perturbations within the same synthetic scene, 5,000 fixed random rays each, seed23, exact GT-only BVH with asserted triangle count. The report stores ray samples, source hashes, transforms, masks, and pooled pixel statistics. The penalized MAE includes both valid absolute errors and 30 m per missing prediction. Old compositor Z arrays failed validation and are quarantined; novel RGB is not scored.

Task definitions are in `docs/INDEPENDENT_FINAL_REVIEW.md`. Candidate arrival differs from accurate drone rephotography. G1 reports a constrained model-world semantic approach goal, not independently verified target visibility or identity. GT static clearance does not test inside/outside or dynamics transfer; G1 foot points are fixed base-pose proxies.
