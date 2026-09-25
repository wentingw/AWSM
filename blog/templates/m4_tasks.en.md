## Let robots test the scene

Both downstream experiments use the frozen **M4: GT pose + MapAnything + Astra** scene. They share its objects, geometry and collision representation, and receive a reference photograph or a language instruction respectively. The original scene is unchanged; task code, requests, trajectories and evaluations are stored as a new revision.

M4 received GT camera poses during reconstruction, but no GT mesh or depth. Robots read their own state from the simulator, so these experiments test **target selection, planning and physical execution with known self-pose and a known reconstructed map**. They do not test visual localization or transfer to the original GT dynamics world.

![Drone reference-image and G1 language-goal pipelines in M4](../figures/m4_tasks/task_flow.en.svg)

### Drone: find the reference view and attempt rephotography

Inputs are the same 20 frozen simulator RGB reference photographs. Retrieval and planning cannot read their target camera poses; a separate evaluator uses them only after execution. These photographs come from the mapping video, making this a seen-input-view task.

{{DRONE_STEPS}}

{{DRONE_RESULTS}}

![M4 drone reference photographs, achieved endpoint images and rephotography evaluation](../figures/m4_tasks/drone_comparison.jpg)

{{DRONE_LIMITATIONS}}

### Unitree G1: find a specified planter from language

{{G1_PROTOCOL}}

{{G1_STEPS}}

{{G1_RESULTS}}

![Language instructions, planter targets and G1 execution results in M4](../figures/m4_tasks/g1_comparison.jpg)

{{G1_LIMITATIONS}}

{{M4_TASK_TABLE}}

{{M4_TASK_EVIDENCE}}
