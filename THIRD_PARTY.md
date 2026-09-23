# Upstream components and attribution

This private research repository does not grant a new open-source license for its own code or for third-party components. Preserve upstream copyright notices and consult each upstream license before redistribution or downstream use. Publicly accessible artifacts do not by themselves imply unrestricted licensing.

| Component | Role | Upstream |
| --- | --- | --- |
| Blender | Scene construction, geometry and rendering | https://www.blender.org/ |
| OpenVINS | Visual-inertial camera estimation | https://github.com/rpng/open_vins |
| ViPE | Video pose/depth frontend; local adapters retain their provenance | https://github.com/nv-tlabs/vipe |
| MapAnything | Pose-conditioned metric depth and RGB baseline | https://github.com/facebookresearch/map-anything |
| MuJoCo | Task simulation | https://github.com/google-deepmind/mujoco |
| Unitree RL Gym assets/control | G1 model and controller dependencies | https://github.com/unitreerobotics/unitree_rl_gym |
| DINOv2 | Reference-image retrieval features | https://github.com/facebookresearch/dinov2 |
| model-viewer | Browser scene viewer | https://github.com/google/model-viewer |

`blog/vendor/model-viewer.min.js` retains its bundled notices; its exact origin/version is in `blog/vendor/model-viewer-source.json`. `src/vipe/upstream_provenance.json` records the local adapter origin. Original scene assets, checkpoints, external runtimes, and vendor checkouts are not part of this Git source snapshot. Their origins and frozen hashes are recorded by the experiment/HF manifests.

Historical M1 builders and the OpenVINS replay wrappers were copied from the existing local project without modification; `source_snapshot.json` records their source paths and SHA256 digests. Research precedents and citations are in `references/research_sources.json` and the article.
