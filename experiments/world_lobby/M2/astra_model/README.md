# M2 clean Astra semantic lobby — frozen revision 5

Status: `frozen_for_independent_GT_evaluation`. This model has not read GT or other methods. Native ViPE scale is 1.0; the exact rigid `T_input_model` and all 180 input cameras are in `cameras.json`.

Open `scene.blend` or import `scene.glb`. Exact regeneration from an empty Blender file uses `build_scene.py`, `cameras.json`, and `mirror_refit.json` in this directory:

```
/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender -b -t 4 --python build_scene.py
```

The exported artifact hashes are frozen in `frozen_artifacts.json` and `SHA256SUMS`. Do not rebuild this directory during evaluation; use an isolated copy for regeneration.

`review_response.json` responds to the independent clean review. `final_geometry_validation.json` records actual Blender solids, collider and projection checks. Final input-frame renders are in `checks_v5`. Five complete revisions and 25 checking views were used; the scene-revision budget is exhausted.

Objects remain separate semantic parametric assemblies. Measurement clouds are auxiliary derivations and are not imported as scene geometry. The fixed window wall excludes the entry portal, while two static closed glass door leaves block it. No open-door traversability is claimed.

`modelling_manifest.json` and `review_response.md` retain unresolved native-depth conflicts, plant/material approximations, wall-floor dark seams, hidden backsides and open boundaries on some inferred lathed decor. Freezing is not a claim of GT accuracy.
