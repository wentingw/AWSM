# Upstream components and attribution

Original AWSM project code is licensed under the [Apache License, Version 2.0](LICENSE), copyright 2026 Wenting Wang and Yaofang Liu. This grant does not relicense third-party code, dependencies, datasets, model weights, or scene assets. Those components retain their respective upstream terms and copyright notices. Consult each applicable license before redistribution or downstream use; public accessibility alone does not imply unrestricted licensing.

| Component | Role | Upstream |
| --- | --- | --- |
| Blender | Scene construction, geometry and rendering | https://www.blender.org/ |
| OpenVINS | Visual-inertial camera estimation | https://github.com/rpng/open_vins |
| ViPE | Video pose/depth frontend; local adapters retain their provenance | https://github.com/nv-tlabs/vipe |
| MapAnything | Pose-conditioned metric depth and RGB baseline | https://github.com/facebookresearch/map-anything |
| MuJoCo | Task simulation | https://github.com/google-deepmind/mujoco |
| Unitree RL Gym assets/control | G1 model and controller dependencies | https://github.com/unitreerobotics/unitree_rl_gym |
| DINOv2 | Reference-image retrieval features | https://github.com/facebookresearch/dinov2 |
| LPIPS / AlexNet | Perceptual appearance evaluation | https://github.com/richzhang/PerceptualSimilarity |
| Three.js r180 | Registered scene comparison viewer | https://github.com/mrdoob/three.js |
| model-viewer | Browser scene viewer | https://github.com/google/model-viewer |

`blog/vendor/model-viewer.min.js` retains its bundled notices; its exact origin/version is in `blog/vendor/model-viewer-source.json`. `src/vipe/upstream_provenance.json` records the local adapter origin. Original scene assets, checkpoints, external runtimes, and vendor checkouts are not part of this Git source snapshot. Their origins and frozen hashes are recorded by the experiment/HF manifests.

Historical M1 builders and the OpenVINS replay wrappers were copied from the existing local project without modification; `source_snapshot.json` records their source paths and SHA256 digests. Research precedents and citations are in `references/research_sources.json` and the article.

The Three.js source retains `blog/vendor/three/LICENSE` and its pinned provenance. LPIPS and pretrained weights are external dependencies with their own terms; exact evaluated versions and weight hashes are in `results/evaluation/appearance_five_views_20260925/report.json`. Display meshes derived from the frozen scenes do not change the upstream scene asset terms.
