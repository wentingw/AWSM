# SceneWeft

**以几何证据为基础，重建可编辑的三维世界。**

[**AWSM：智能体世界仿真与建图**](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html)的重建实现代码。SceneWeft 将 RGB 观测与几何证据转化为结构化的 Blender 场景程序：保留显式对象、空间关系和可编辑几何，而不止于点云或渲染图像。它以位姿估计和深度重建为基础，由智能体完成场景构建、检查与修订。

[English](README.md) · [实验与复现](experiments/world_lobby_four_trajectory_20260929/README.md) · [第三方声明](THIRD_PARTY.md)

## 四条重建路线

World Lobby 实验使用共同的 RGB 观测集和场景构建目标，对比四条路线。各方法均采用 Astra–Blender 工作流，区别在于提供的几何证据。

| 方法 | 相机位姿 | 深度证据 |
| --- | --- | --- |
| **M1 · 纯 RGB** | 无估计轨迹 | 无 |
| **M2 · ViPE** | ViPE，由 RGB 估计 | 位姿条件化的 Depth Anything 3 |
| **M3 · ORB-SLAM3** | ORB-SLAM3，由 RGB + IMU 估计 | 位姿条件化的 Depth Anything 3 |
| **M4 · GT 位姿参照** | 真值相机位姿 | 位姿条件化的 Depth Anything 3 |

M4 向建模器提供参照位姿，**不提供 GT 几何或 GT 深度**。评测分别考察位姿、场景几何、深度与外观。这是单场景的系统级比较，不将单一指标等同于重建质量，也不将不同路线视为严格的单变量消融。

## 代码入口

上述方法实现在 [9 月 29 日实验目录](experiments/world_lobby_four_trajectory_20260929/)中：

- [`code/`](experiments/world_lobby_four_trajectory_20260929/code/)：轨迹准备、DA3 推理与几何输入包。
- [`astra_blender2/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/models/)：M1–M4 场景构建程序与参数。
- [`astra_blender2/tools/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/tools/)：视角检查、模型冻结与重建评测。

早期 OpenVINS/MapAnything 实验作为独立历史记录保留，其方法标签和资产不能替代本轮实现。

## 复现

校验源码快照并运行便携深度测试：

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-core.txt
.venv/bin/python scripts/verify_source_snapshot.py
.venv/bin/python scripts/check_world_lobby_depth_math.py
```

使用 Blender 5.2.0 重建已保存的场景，输出目录需位于仓库之外且尚不存在：

```bash
.venv/bin/python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/sceneweft-M4
```

方法可选 `M1`–`M4`。此命令执行已保存的构建程序，不重新运行推理、智能体建模或评测。完整流程还需原始采集、前端依赖、模型权重、评测资产及路径重定位；具体要求与复现边界见[实验指南](experiments/world_lobby_four_trajectory_20260929/README.md)。

## 发布范围

本次聚焦**重建方法实现与复现方案**。具身演示、机器人控制和任务执行不属于本次发布范围，留待后续版本完善。代码及外部资产的使用条件见 [THIRD_PARTY.md](THIRD_PARTY.md)。
