# SceneWeft

**Geometry-grounded agentic reconstruction of editable, executable 3D scenes.**

SceneWeft is the private research repository for a controlled World Lobby experiment. GPT-6 Astra uses RGB and optional geometric evidence to author Blender scene programs with named parts, spatial relations, renderable cameras, and collision proxies. This studies an agentic reconstruction workflow; it is not a learned predictive world model.

[中文说明](README.zh-CN.md) · [Code map](CODEMAP.md) · [Research positioning](PROJECT_POSITIONING.md)

Article and assets:

- Blog: https://wentingw.github.io/astra-world-model-blog/
- English: https://wentingw.github.io/astra-world-model-blog/en.html
- Assets (currently private; HF access required): https://huggingface.co/datasets/Ooliva/astra-world-model-blog

## Methods

- **M1 RGB-only:** sampled RGB → Astra → Blender. No native metric camera estimate; supplementary Sim(3) registration is not metric recovery.
- **M2 ViPE:** video → ViPE near-metric pose/depth → Astra → Blender.
- **M3 OpenVINS + MapAnything:** RGB+IMU+calibration → OpenVINS metric pose → pose-conditioned MapAnything depth → Astra → Blender.
- **M4 GT-pose ablation:** RGB + simulator GT pose → MapAnything → Astra → Blender. GT pose is an oracle input, not an estimated-pose result.
- **B1:** direct ViPE fusion, sharing M2's frontend.
- **B2:** calibrated RGB-only / known-intrinsics MapAnything baseline.
- **B2p:** direct fusion sharing M3's OpenVINS+MapAnything inputs, without Astra.

## Evidence and limits

This is one static synthetic World Lobby capture and one engineering run per primary method. M2 reports 0.118 m pose translation RMSE, 0.0738 native-depth AbsRel, and 0.182 m model-to-GT mean surface distance. M3 reports 2.595 m, 0.2612, and 0.459 m. M4 receives GT pose and is not an estimator result.

The drone task reports 15/20 collision-free candidate arrivals, 5/20 collisions, and 0/20 strict or relaxed precise rephotography successes. G1 reports 18/30 model-world approach successes and 12 planning failures across five target families with six paraphrases each; the task uses simulator-state localization and has no independent visual identity check. Named elements and colliders are not independent semantic precision/recall or real physical-property measurements.

SceneWeft complements SLAM/VIO: those systems provide registration and geometric constraints; SceneWeft turns evidence into an editable scene program. There is no evidence here of surpassing, replacing, or being first in SLAM or agentic reconstruction.

## Reproduction

See [REPRODUCING.md](REPRODUCING.md) and [artifact-lock.json](artifact-lock.json). Upstream attribution and terms remain in force; this repository adds no open-source license.
