# Clean Astra modelling contract

This file is a generic tool contract, not a scene specification. A modeller receives only its packet path and an empty output directory. It must not open other experiments, evaluation folders, GT meshes/depth, published models or existing scene programs.

Input packet: sampled original RGB images, optional per-view OpenCV camera-to-world poses and optical-Z depth, per-image intrinsics and frame timestamps. M1 has RGB only; M2 has ViPE geometry; M3 has OpenVINS + MapAnything geometry; M4 has pose-conditioned MapAnything geometry with a permitted GT-pose input. No method receives GT geometry, object labels or rendered evaluation images.

Use GPT-6 Astra to inspect images and call Blender 5.2 Python tools. Construct the scene from an empty Blender file. Author named semantic objects with parametric solids/materials. Visible surfaces must follow supplied geometry where available; record conflicting or weak measurements rather than secretly rescaling. Separate observed geometry from inferred backsides, thickness, joints and physical parameters. Avoid placing a single fused scan as the entire semantic model: retain scan only as an input measurement or explicitly named separate visualization layer.

Required outputs: scene.blend, scene.glb, build_scene.py (or modular equivalent), objects.json (object_id, category, attributes, spatial relations, evidence frame ids, geometry provenance, bounds), colliders.json, cameras.json, input_access_log.json, iteration_log.json, modelling_manifest.json. Metric methods preserve the input frame/units or provide exact T_input_model including any gravity normalization. Render 5 input views in your own supplied camera frame for internal checking; an independent evaluator handles GT after freezing.

Budget for first engineering run: at most 5 complete scene revisions, at most 60 tool-rendered checking views, report actual elapsed/tool/model token use where available. This is not yet the three-run statistical experiment. A clean separate Astra verifier checks allowed evidence and returns specific frame/object complaints; it must never grade using GT evaluation images. Stop with honest unresolved items when the fixed engineering budget is exhausted; do not erase failures.

Use only output paths within the new run. Read-only tools/code without scene-specific geometry can be reused; old object dimensions, old material assignments and old scene source cannot be reused. No publication tools in modeller role.
