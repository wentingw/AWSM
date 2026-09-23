# M4 independent Astra final model

Status: **frozen_for_independent_GT_evaluation**, revision4. The modeller has not read any GT mesh/depth, other-method model or evaluation. The clean verifier reviewed revision2 only against permitted RGB/model evidence; `review_response.json` documents all nine responses and remaining issues.

The scene preserves native metres and Z-up (identity input/model transform), and includes named parametric solids with semantic metadata, static AABB collision proxies and 180 supplied cameras. Rebuild with:

```sh
M4_REVISION=4 /home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender -b -t 4 -P build_scene.py
```

CPU Cycles, four threads, 40 samples. Four revisions and twenty checking renders used out of five revisions and sixty views. Current renders are `renders_v4/frame_000.png`, `frame_060.png`, `frame_090.png`, `frame_108.png`, `frame_138.png`. `comparison_v4.jpg` contains only allowed RGB on the left and own model renders on the right.

All required outputs are listed with immutable hashes in `final_freeze.json`. `layout_parameters.json` and `cameras.json` are needed alongside `build_scene.py` to rebuild. `input_access_log.json` and `modelling_manifest.json` retain the evidence boundary, depth conflicts and inferred surfaces/materials.

Remaining limitations: several pendant identities/height/diameter remain approximate, manual furniture outlines have residual error, and reflective-floor/fabric appearance is imperfect. Uncertainty numbers are heuristic author estimates. Collision bounds conservatively include foliage/curved empty spaces; floor contacts should select the highest supporting role=floor surface, including the visible inset atz0.041. No dynamic simulation or quantitative fidelity claim has been made.
