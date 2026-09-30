# New independent Astra modelling run: ten paired check views

Use only your assigned method's `inputs/Mx/`, `models/Mx/`, this contract, and the explicitly listed generic tools. Start from an empty Blender scene. Never read the parent experiment, old models, published pages, plans, evaluation data/results, GT scene/depth, another method, or global process arguments (/proc, ps, pgrep, top). Your context is method-specific. Physical input copies and declared/logged tool scope are used; the filesystem is not an OS-enforced sandbox. Record paths read and commands honestly in input_access_log.json. Do not spawn further agents or publish anything.

Method inputs: M1 = 180 RGB, identity, public intrinsics only; derive layout, assumed scale and cameras from RGB without external SfM/SLAM/depth pipelines. M2 = ViPE native poses + own pose-conditioned DA3. M3 = ORB-SLAM3 native poses + own pose-conditioned DA3. M4 = explicitly allowed sampled GT camera matrices + predicted DA3; no GT geometry/depth. All input depth is prediction, never truth.

Read all six contact sheets covering 180 frames and inspect important source RGB. Derive a fresh semantic inventory, architectural layout, object measurements, placement, materials and uncertainties from only these inputs. Do not wrap a fused point cloud as the final semantic model. Geometry methods should perform real backprojection/plane fitting, image-correspondence triangulation or ray-plane measurement, record observations and conflicts with sample IDs/pixel regions/residuals. Preserve native metric scale; only a recorded rigid model_from_input (scale=1) is allowed. Use NPZ depth intrinsics for backprojection and packet camera_to_world, not predicted cameras.

Required outputs: build_scene.py and any modules, layout.json, scene.blend, scene.glb, objects.json, colliders.json, cameras.json, input_access_log.json, iteration_log.json, modelling_manifest.json; analysis/object_inventory.json, measurements.json, camera_checks.json; checks/ and independent_review/. Stable semantic object IDs must map to named Blender/GLB mesh components, with category, dimensions, spatial/support relations, evidence frame IDs and observed/inferred provenance. Hidden surfaces, thickness, material, lighting, plant detail and physics are inferred. Avoid duplicate reflected objects. All meshes must be semantic or marked hide_render/exclude_from_evaluation for helpers.

At most five full scene versions. Every built version MUST run ten paired RGB+depth checks at samples **33,61,74,82,91,100,108,118,129,155**, never substitute other frames. Each view produces RGB and model optical-Z; M2–M4 also compare with own DA3 on the identical grid and save signed/absolute/relative errors, masks and edge discrepancies. M1 has model depth for self-occlusion but quantitative depth reference N/A. All ten checks per version, at most 50 total, plus at most ten justified supplemental paired checks. Reuse actual outputs for review. No unlogged test renders.

Use coordinator generic tools:

    BLENDER -b --factory-startup --threads 2 --python-exit-code 1 --python TOOLS/paired_check_blender.py -- --method-dir YOUR_OUTPUT --packet YOUR_PACKET
    python3 TOOLS/visualize_checks.py --method-dir YOUR_OUTPUT --packet YOUR_PACKET --version N

These use CPU Cycles 12 samples at 640×480 and matching geometric optical-Z at pixel centres; no transparency/refraction in geometric depth. Original RGB camera K: fx=fy=762.8,cx=640,cy=480 at 1280×960. Public camera calibration must be validated; OpenCV RDF c2w to Blender camera is right multiply diag(1,-1,-1,1). Do not move geometry-method cameras per frame or trim masks to improve scores.

M2–M4 must run exactly three full 180-frame input checks: initial version, major-repair version, final version (can be separate logged passes on same geometry if a later pass makes no geometry change; explain). Limit three; no GT. Command:

    BLENDER -b --factory-startup --threads 2 --python-exit-code 1 --python TOOLS/raycast_scene.py -- --model YOUR_OUTPUT/scene.blend --input-packet YOUR_PACKET --model-manifest YOUR_OUTPUT/modelling_manifest.json --out YOUR_OUTPUT/checks/input_vN

Keep all outputs from each version. Retain parameter snapshots and report each size/position/orientation change with multiple RGB/depth views, pixel regions, signed residual evidence and rationale. Changes without sufficient evidence must be marked inference. Don't optimize silently against whole-scene DA3 score; inspect spatial errors and keep conflicts/limitations.

INITIAL PHASE: complete fresh measurements/model v1, ten paired checks, inspect comparisons, full input check for geometry methods, write actionable limitations, then stop for independent review. Do not self-certify review or freeze. Root will launch a separate reviewer, then ask you to revise. FINAL PHASE: fix specific review issues within budgets, complete checks and input passes, return final candidate for another independent review. Frozen evaluation never feeds back to authors.

JSON interoperability:

- cameras.json = {"frames":[{"sample_index":int,"source_index":int,"timestamp_ns":int,"camera_to_world":4x4 OpenCV c2w IN MODEL COORDINATES,"intrinsics":3x3,"valid":bool,"confidence":...}],"coordinate_frame":"model","pose_convention":"OpenCV RDF camera-to-world"}. Geometry methods include all180 with exact X @ packet pose. M1 should attempt all180 estimated cameras, mark unreliable ones honestly; retain assumed check cameras even when not validated. No external cameras may be borrowed.
- modelling_manifest.json requires method_id, model_id="gpt-6-astra", status="ready_for_independent_review", model_from_input (rigid4x4 or null M1), geometry_scale, revisions (1..5), checking_render_count (actual paired views), input_bvh_pass_count, input_packet_sha256, unresolved_issues, quality_status. Do not set frozen status yourself.
- objects.json preferably {"objects":[{"id":str,"category":str,"components":[mesh_names],"dimensions":...,"relations":...,"evidence_frames":[...],"provenance":...}]}.
- Save parameter/layout version snapshots and all prior check outputs; `versions/vN` populated by check tool. Scene programs must reconstruct without reading saved .blend.

Blender: /home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender
Python: python3 (numpy,scipy,Pillow); /home/hchen/Documents/astraBlenderTest/reconstruction/.venv/bin/python (trimesh, etc.). Limit native libraries to two threads and avoid shared GPU. No global process inspection. Use own tool sessions/logs only. For long running renders, monitor own log and persist until completion.

Review limitations honestly. A LIMITED model can freeze for evaluation after technical validity and independent review; this does not certify visual fidelity. Never invent measurements or claim images/tools were checked if they weren't.
