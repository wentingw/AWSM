# AWSM — Agentic World Simulation and Mapping

**以几何证据约束智能体重建，构建可编辑的三维世界。**

AWSM 让大模型智能体将视觉观测转化为结构化的 Blender 场景，并以相机位姿与深度估计进行几何锚定，其中包括融合 IMU 的视觉惯性约束。目标不只是生成看起来合理的房间，而是保留忠实的尺度、形状与空间关系，为建图、仿真和交互提供可编辑的空间参照。

[English](README.md) · [研究博客](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html) · [代码仓库](https://github.com/wentingw/AWSM) · [交互式对比](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html#figure-3) · [复现指南](docs/AWSM_REPRODUCTION.md)

![AWSM：输入视频、重建场景与网格](docs/awsm/awsm_teaser.png)

## 更新

- **2026-10-01 · v0.1** — 发布 [AWSM 研究博客](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html)与首版重建代码，包含 M1–M4 方法实现、评测工具和复现说明。

## 方法概述

重建智能体遵循**观测 → 构建 → 验证**的迭代流程：检查允许访问的观测、编写 Blender Python、渲染检查视角，再修订并冻结场景用于评测。输出显式保留对象、材质、相机、空间关系与碰撞代理，而不止于点云或渲染图像。

位姿与深度约束场景构建，而非取代它。AWSM 以 SLAM 和视觉惯性估计为基础，研究几何证据如何在转化为可编辑对象时得到保留。评测分别考察轨迹、原生深度、最终场景深度、表面几何与外观。

### 四条重建路线

World Lobby 实验在一个受控的 NVIDIA Isaac Sim 场景中比较四条完整管线，使用相同的 180 帧建模 RGB 观测和共同的 Astra–Blender 建模目标。

| 方法 | 相机位姿 | 深度证据 |
| --- | --- | --- |
| **M1 · 纯 RGB** | 无测量轨迹；已知公共内参 | 无 |
| **M2 · ViPE** | 由 RGB 估计 | 位姿条件化的 Depth Anything 3（DA3） |
| **M3 · ORB-SLAM3** | 由 RGB + IMU + 标定进行单目惯性估计 | 位姿条件化的 DA3 |
| **M4 · GT 位姿参照** | 真值相机位姿 | 位姿条件化的 DA3 |

M4 向建模器提供参照位姿，**不提供 GT 网格或 GT 深度**。四条路线是系统级比较，不是 IMU 的独立消融；M4 是诊断性参照，不是可部署的位姿估计器。

## 博客结果

博客报告的经配准 M1 → M4 对比为：

| 指标 | 纯 RGB M1 | GT 位姿 M4 | 相对降幅 |
| --- | --- | --- | --- |
| 双向平均表面误差 | 0.376 m | 0.072 m | ≈81% |
| 模型深度 AbsRel · 180 个评估视角 | 16.44% | 7.60% | ≈54% |

数值来自[博客冻结数据的表 2–3](https://github.com/Phygital-AI/agentic-world-simulation-and-mapping/blob/77b04cc6043b29b43b9e1ff91402343708665ada/data/tables_1_7.json)，相对降幅由未舍入值计算。M1 使用 GT 辅助的 Sim(3) 配准，M4 使用 GT 位姿。这是单场景、完整系统之间的差异，**不代表 M1 原生恢复了度量尺度，也不是 IMU 单独带来的增益**。位姿、几何与 RGB 相似度是不同目标，任何单项指标都不能独自说明整体场景质量。

结合[共享相机三维对比](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html#figure-3)和[同视角图像](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/zh.html#figure-4)检查具体差异。博客中的真实采集示例属于定性观察，不是新增的配对 GT 基准。

## 实现与复现

重建源码位于 [9 月 29 日实验目录](experiments/world_lobby_four_trajectory_20260929/README.md)：

- [`code/`](experiments/world_lobby_four_trajectory_20260929/code/)：轨迹准备、DA3 推理与几何输入包；原生估计器结果及上游运行环境需另行准备。
- [`astra_blender/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender/models/) 与 [`astra_blender2/models/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/models/)：两轮保存的 M1–M4 场景构建程序。
- [`astra_blender2/tools/`](experiments/world_lobby_four_trajectory_20260929/astra_blender2/tools/)：输入检查、模型冻结、渲染与重建评测。

**校验源码与便携数值实现**，使用 Python 3.10–3.12：

```bash
python -m venv .venv-core
.venv-core/bin/python -m pip install -r requirements-core.txt
.venv-core/bin/python scripts/verify_source_snapshot.py
.venv-core/bin/python scripts/check_world_lobby_depth_math.py
.venv-core/bin/python tests/test_pose_metrics.py
```

**重建已保存的场景**，使用 Blender 5.2.0；方法可选 `M1`–`M4`，输出目录需位于仓库之外且尚不存在：

```bash
.venv-core/bin/python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/awsm-M4-rebuild
```

此命令执行后续 `astra_blender2` 轮次的保存程序，**不重新运行推理、智能体建模、渲染或评测**。博客展示模型与这轮固定十视角模型不同，对比输出前请核对[模型与证据对应关系](docs/AWSM_REPRODUCTION.md#which-results-belong-to-which-models)。历史前端命名差异仍记录在[博客来源说明](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/evidence/provenance-note.md)中。

完整流程还需原始采集、标定、估计器结果、模型权重、GT 资产、智能体访问权限及路径重定位，具体要求与边界见[复现指南](docs/AWSM_REPRODUCTION.md)。后续研究聚焦效率、精度、可复用仿真资产与持续空间记忆；这些是研究方向，不是本次已验证结果。

## 引用与使用条件

```bibtex
@misc{awsm_2026,
  title = {{AWSM}: Agentic World Simulation and Mapping},
  author = {{Phygital AI}},
  year = {2026},
  howpublished = {Interactive research article},
  url = {https://phygital-ai.github.io/agentic-world-simulation-and-mapping/}
}
```

用于可复现比较时，请同时记录代码版本、建模轮次、模型哈希与评测协议。组件及资产使用条件见 [THIRD_PARTY.md](THIRD_PARTY.md)；本仓库不授予新的许可证。
