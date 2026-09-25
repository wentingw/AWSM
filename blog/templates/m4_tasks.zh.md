## 让机器人检验场景

下游实验固定使用 **M4：GT 位姿 + MapAnything + Astra** 的冻结场景。两个任务共享它的对象、几何和碰撞表示，分别接收参考照片与自然语言指令。场景原件保持不变，任务代码、请求、轨迹与评测另存为新版本。

M4 建图时获得 GT 相机位姿，但没有获得 GT 网格或深度。运行时机器人读取仿真器提供的自身状态，因此本节检验的是**已知自身位姿、已知重建地图条件下的目标选择、规划与物理执行**。它没有评测机器人视觉定位，也没有将控制器迁移到原始 GT 动力学世界。

![M4 场景中的无人机参考图任务与 G1 语言目标任务](../figures/m4_tasks/task_flow.zh.svg)

### 无人机：找到参考图，并尝试复拍

输入为原先冻结的 20 张仿真 RGB 参考照片。检索器和规划器不能读取目标相机位姿；这些位姿只在飞行结束后进入独立评测。参考图来自建模视频，因此这是已见输入视角任务。

{{DRONE_STEPS}}

{{DRONE_RESULTS}}

![M4 无人机参考照片、实际终点图与复拍评价](../figures/m4_tasks/drone_comparison.jpg)

{{DRONE_LIMITATIONS}}

### G1：按照自然语言找到指定花盆

{{G1_PROTOCOL}}

{{G1_STEPS}}

{{G1_RESULTS}}

![M4 中的语言指令、花盆目标与 G1 执行结果](../figures/m4_tasks/g1_comparison.jpg)

{{G1_LIMITATIONS}}

{{M4_TASK_TABLE}}

{{M4_TASK_EVIDENCE}}
