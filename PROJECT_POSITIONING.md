# Project positioning

**Name:** SceneWeft  
**Slug:** sceneweft  
**Descriptor:** Geometry-grounded agentic reconstruction of editable, executable 3D scenes.  
**Slogan:** Weaving observations and geometry into an executable scene program.

“Agentic World Reconstruction” may describe the future direction, but the present artifact is one static synthetic scene and a Blender scene program. It is not a learned predictive world model: temporal prediction, counterfactual dynamics, open-world generalization, calibrated uncertainty, and physical-robot transfer are unproven.

Agentic accurately describes the workflow: Astra inspects permitted evidence, calls Blender tools, renders checks, and revises within a declared budget. Geometry-grounded describes explicit pose, depth, calibration, and coordinate inputs. Executable describes the renderable, queryable, editable scene and declared collision layer. “Mapping” is a useful interface term, but “reconstruction” should lead the title.

SceneWeft complements SLAM/VIO. SLAM estimates camera motion, registration, scale and uncertainty; SceneWeft consumes those constraints and constructs named parts, relations, cameras, materials and collision proxies. M3's 2.595 m pose translation RMSE shows that Astra does not repair frontend drift. M4's GT pose is a diagnostic ablation, not a deployable SLAM result. There is no evidence of surpassing, replacing or being first in SLAM.

Scope boundaries: M1 has no native metric pose; M2 uses ViPE near-metric geometry; M3 uses OpenVINS and MapAnything; M4 receives GT pose; semantic precision/recall and real physical properties are unmeasured; drone and G1 results are simulation-only; the experiment is one static synthetic scene.

Public blog: https://wentingw.github.io/astra-world-model-blog/  
Hosted assets (HF access required): https://huggingface.co/datasets/Ooliva/astra-world-model-blog

Worldwright and WorldWeft have visible public repositories and are poor choices. SceneWeft was cleanest in the limited exact-name search; this is not trademark or legal clearance. The detailed evidence review is [docs/PROJECT_POSITIONING_REVIEW.md](docs/PROJECT_POSITIONING_REVIEW.md).

## Research opportunity

The long-term opportunity is a common scene-program layer for robotics, digital twins, simulation authoring, synthetic training data, spatial editing and 3D content creation. Geometry supplies measurable constraints; semantic structure supports queries and targeted edits; executable assets support task evaluation. This application scope could extend beyond localization, but breadth is not measured impact.

The next milestones are multi-scene real-data evaluation, matched modelling budgets, object-level identity and relation metrics, incremental updates, uncertainty propagation, and measured sim-to-real behavior. Comparing impact with SLAM is premature until reliability and adoption are demonstrated.
