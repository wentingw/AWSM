# Project positioning and naming review

Date: 2026-09-23. This review covers naming and research positioning only; it does not create a repository or use authentication.

## Recommendation

Use **SceneWeft** as the project name.

Public title: **SceneWeft: geometry-grounded agentic reconstruction of executable 3D scenes**

Slogan: **Weaving observations and geometry into an executable scene program.**

Private repository name: **sceneweft**

GitHub description (under 160 characters): Geometry-grounded agentic reconstruction of editable, executable 3D scenes from RGB, video, camera pose, and depth.

SceneWeft is short and distinctive, while its subtitle says what the system actually does. The name suggests that observations, geometry, semantic parts, programmatic construction, and verification are woven into one artifact. It avoids claiming a learned general world model. This is a preliminary naming recommendation, not trademark or availability clearance.

## Accurate technical positioning

The strongest description is:

A tool-using, geometry-grounded scene-reconstruction pipeline that converts sampled RGB and optional camera/depth evidence into an editable, renderable Blender scene with named parts, spatial relations, and collision proxies.

Agentic is defensible at the workflow level: Astra inspects evidence, chooses construction actions, calls Blender tools, renders checks, and revises within a declared budget. It does not mean autonomous sensor exploration, online active mapping, or learned dynamics.

Mapping is only partly accurate. Frontends estimate camera and depth over a capture; the downstream result is an objectized scene program. Scene reconstruction should lead the title.

World reconstruction can describe the application ambition, but world model is too strong for the current evidence. This is one static synthetic World Lobby capture with frozen scene artifacts and simulator tasks. It does not demonstrate learned temporal prediction, counterfactual dynamics, open-world generalization, dynamic tracking, calibrated uncertainty, or physical-robot transfer.

## Candidate terminology

| Term | Accurate signal | Risk | Assessment |
|---|---|---|---|
| Agentic Mapping & Reconstruction | Connects agents, mapping, and reconstruction | Suggests online active mapping and ownership of the full SLAM loop | Useful field description; too broad as the title |
| Agentic World Reconstruction | Signals environment construction | Implies complete-world coverage and can be confused with a predictive world model | Plausible future-facing phrase; still broad |
| Executable Scene Reconstruction | Names the measurable output | Does not emphasize tool use or evidence provenance | Safest generic technical descriptor |
| Scene-program synthesis | Names structured code-like output | Hides camera/depth measurement and verification | Good subsystem term, incomplete project title |
| SceneWeft | Distinctive identity for the integrated workflow | Needs a technical subtitle | Recommended name |

The preferred positioning is therefore: **geometry-grounded agentic reconstruction of editable, executable 3D scenes**. Keep executable scene program as the output representation. Use agentic mapping and reconstruction as a field label, not as an unsupported claim that the current system is online SLAM.

## Public name collision check

A lightweight GitHub repository search was run on 2026-09-23. This only checks visible repository names, not trademarks, package indexes, domains, or legal rights.

Worldwright has multiple repositories, including ka1kqi/worldwright, adamalbu/worldwright, G061206/Worldwright, kotonja/Worldwright, and DasDarki/worldwright. It is also technically close: public search descriptions include an LLM agent authoring simulation tasks.

WorldWeft has visible repositories including hX1-dev/worldweft and PriyanshRaj30/WorldWeft. Public descriptions include autonomous agent worlds, making it close in both name and theme.

SceneWeft returned no exact-match repository in the queried GitHub repository search. This does not establish availability or trademark safety. It is simply the cleanest result among these three candidates in this limited check.

The documented neighboring work already includes agent-driven scene generation and reconstruction; these precedents are sufficient to avoid a “first agentic reconstruction system” claim.

## Relation to existing research

ViPE and MapAnything provide the geometric frontend roles used here; OpenVINS provides visual-inertial pose estimation. Hydra, ConceptFusion, and VLMaps establish semantic scene graphs and language-linked maps. SceneScript and Real2Code establish structured or code-based reconstruction directions. Holodeck generates embodied environments from language. Lab Kitchen Twin and LiteReality-Agent are close engineering demonstrations. These precedents support an integration and evaluation claim, not invention of semantic mapping, programmatic reconstruction, or tool-using 3D agents.

Evidence links:

- ViPE: https://arxiv.org/abs/2508.10934
- MapAnything: https://github.com/facebookresearch/map-anything
- OpenVINS: https://docs.openvins.com/
- Hydra: https://github.com/MIT-SPARK/Hydra
- ConceptFusion: https://concept-fusion.github.io/
- VLMaps: https://github.com/vlmaps/vlmaps
- SceneScript: https://arxiv.org/abs/2403.13064
- Real2Code: https://arxiv.org/abs/2406.08474
- Holodeck: https://arxiv.org/abs/2312.09067
- Astra capability page: https://developers.openai.com/api/docs/models/gpt-6-astra

The local evidence inventory is references/research_sources.json.

## Relationship to SLAM

The relationship is complementary and layered.

SLAM or VIO estimates camera motion, registers observations, and exposes scale, loop-closure, uncertainty, and tracking failures. This project consumes some of those answers and turns them into a different downstream representation: named parts, measured dimensions, spatial relations, cameras, materials, collision proxies, and a scene that can be edited, rendered, queried, and used by a declared simulator.

In M3, OpenVINS is the metric-pose frontend and MapAnything is the metric-depth frontend. M3 shows why the distinction matters: metric units do not imply low long-horizon drift, and Astra does not repair drift by writing Blender code. M4 supplies ground-truth pose as an oracle ablation; it is not a deployable SLAM result.

A future SLAM system could export richer executable semantic maps. A scene-program layer could provide object hypotheses, traversability, and task relations to planners. Neither direction removes the need to evaluate tracking, loop closure, scale, dynamics, uncertainty, or map consistency. The current result demonstrates an interface and error propagation, not a replacement for SLAM.

## Potential application breadth and limits

If it survives broader tests, the approach could support simulation-environment authoring, task-specific navigation and manipulation assets, evidence-linked scene editing, semantic queries, reconstruction-assisted synthetic data, and inspection workflows.

These are possible applications, not measured product impact. The current evidence is one static synthetic scene. Named elements have no independent object-level precision/recall evaluation. Colliders do not prove real friction, mass, inertia, or contact behavior. Drone and G1 results are simulator tasks; the drone report separates collision-free candidate arrival from failed precise rephotography. No real-robot transfer is established.

## Claims policy

Recommended claims:

- Astra authored an editable Blender scene program from RGB plus geometric evidence.
- The pipeline connects camera/depth measurements to semantic scene construction and verification.
- Four geometric input conditions expose how frontend errors propagate into an executable artifact.
- The scene is executable under declared simulator assumptions.
- The experiment suggests a bridge between geometric mapping and task-oriented scene assets.

Avoid:

- The first agentic mapping system or first executable world model.
- A learned predictive world model.
- Replacement or disruption of SLAM.
- Solved semantic or physical alignment.
- Metric correctness everywhere.
- Physically realistic colliders.
- Robot success as proof of embodied intelligence.
- Open-world real-scene generalization.

## Naming decision

Adopt **SceneWeft** with the subtitle **geometry-grounded agentic reconstruction of editable, executable 3D scenes**. Keep executable scene program as the technical output phrase and agentic mapping and reconstruction as the related field description. Do not use Agentic World Model as the primary name until temporal prediction and broader environment coverage are demonstrated.
