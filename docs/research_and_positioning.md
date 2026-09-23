# From pixels to an executable world model: research positioning and evidence

本文件服务于 blog 的技术论断、相关工作和实验口径。时间点为 2026-09-22；论文/代码链接应在发布前再锁定版本和访问日期。

## 先把主张说准确

我们要展示的是一条工程管线：采样图像 + 相机几何 + 深度，经 Astra 调用 Blender 生成一个带物体/材质/空间关系语义、并尽量和真实尺度及几何对齐的可渲染场景。目标输出是可查询、可编辑、可重渲染的 scene program/Blender 场景。需要与已有语义 SLAM、场景图和程序化重建比较具体能力，不能将它们概括为只有轨迹或点云，也不能声称已解决开放世界的遮挡、物理和动态问题。

OpenAI 官方模型页现在公开列出 GPT-6 Astra：支持文本输入、图像输入、Responses API 及多种工具调用；该页没有证明“颠覆 3D 建模行业”这一结论。blog 应把 Astra 的能力和本项目实际测得的 Blender 工作流结果分开叙述。

## 四条路径的可证伪定义

| 路径 | 输入 | 几何来源 | 场景生成 | 必须报告的限制 |
|---|---|---|---|---|
| M1 RGB-only | 采样 RGB 图片 | Astra/Blender 推断和构造 | 图片、提示和工具调用生成 Blender scene | 无显式 metric 几何监督；尺度、遮挡和不可见面可能是猜测 |
| M2 ViPE | 视频及采样帧 | ViPE 的相机内参/运动和 dense **near-metric** depth | 采样帧 + ViPE 输出输入 Astra/Blender | “near-metric”不等于每场景公制；动态物体、相机模型和尺度漂移需单独评测 |
| M3 OpenVINS + MapAnything | RGB 视频 + 同步 IMU | OpenVINS metric pose；MapAnything 输入图像、内参和 pose，输出 metric 3D/depth | 采样帧 + pose + depth 输入 Astra/Blender | 需校验时间同步、IMU-camera 外参、坐标系和 MapAnything 的 metric-scale 标志 |
| M4 GT-pose oracle | RGB 视频 + GT pose | GT camera pose；MapAnything 输出 depth | 同 M3 | 条件诊断/消融；不保证是严格上界，因深度网络和 Astra 仍可能有误差耦合 |

M2 的“metric”字样在图表中建议写 `ViPE near-metric`。M3/M4 的 MapAnything 输入应显式记录 `camera_poses`、`intrinsics`、`is_metric_scale=True`、OpenCV (+X right, +Y down, +Z forward) cam2world 约定；否则所谓 metric depth 可能只是尺度标签错误。

## 一手证据和与本项目的关系

1. **ViPE: Video Pose Engine for 3D Geometric Perception**，Huang et al., arXiv:2508.10934 (2025)：<https://arxiv.org/abs/2508.10934>；NVIDIA 项目页：<https://research.nvidia.com/labs/toronto-ai/vipe/>。摘要明确是从原始视频估计内参、camera motion 和 dense *near-metric* depth，支持 pinhole、wide-angle、360°，并报告 TUM/KITTI 与 3–5 FPS。它适合作为 M2 和 baseline；论文摘要没有承诺用户提供外部 metric pose 后进行 metric depth 条件推理，因此不要把这种模式写成 ViPE 的官方接口。
2. **MapAnything: Universal Feed-Forward Metric 3D Reconstruction**，Keetha et al., arXiv:2509.13414 (2025)：<https://arxiv.org/abs/2509.13414>；官方代码：<https://github.com/facebookresearch/map-anything>；项目页：<https://map-anything.github.io/>。README 的 multi-modal 示例明确支持每个 view 的 `img`、`intrinsics`、`camera_poses`、`depth_z` 和 `is_metric_scale`；输出含 `pts3d`、`depth_z`、`camera_poses`、`metric_scaling_factor`。README 要求输入 pose 是 OpenCV cam2world。因而 M3/M4 在“接口层面”成立，但本项目仍要验证 pose-only conditioning 的实际 checkpoint/版本、输入格式和尺度误差；不能只凭函数能运行就宣称准确。
3. **OpenVINS**，Geneva et al., “OpenVINS: A Research Platform for Visual-Inertial Estimation”, ICRA 2020；代码：<https://github.com/rpng/open_vins>；论文页：<https://docs.openvins.com/>。OpenVINS 是基于相机和 IMU 的 MSCKF/VIO 研究平台，估计状态包含姿态、位置和速度。静止观测可以帮助估计重力方向，但不能单独恢复视觉平移尺度；需要相机-IMU 标定、时间同步和充分运动来约束 metric scale；纯单目视觉本身存在尺度不确定性。应报告初始化、tracking loss、漂移和对齐方式，而不要把“使用 OpenVINS”自动等同于无漂移 metric pose。
4. **3D Gaussian Splatting for Real-Time Radiance Field Rendering**，Kerbl et al., SIGGRAPH 2023：<https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/>。说明了从已知/估计相机和图像得到高质量可渲染表示的路线；它是渲染表示基线，不提供语义对象、碰撞网格或物理可执行性。
5. **VGGT: Visual Geometry Grounded Transformer**，Wang et al., CVPR 2025：<https://github.com/facebookresearch/vggt>。提供多视图相机、深度、点图预测，代表 feed-forward geometry foundation model，与 DUSt3R/MASt3R 等共同构成相关的前馈几何路线。它支持定位本项目的几何模块，但不等价于 Blender scene program。
6. **Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction and Optimization**，Hughes, Chang, Carlone, RSS 2022：<https://github.com/MIT-SPARK/Hydra>。将几何、语义和层次场景图用于机器人空间理解；这提醒我们不要把传统 SLAM 概括为只有轨迹/点云。我们的 Blender 输出可用场景图节点/边和渲染验证补足其展示方式。
7. **ConceptFusion: Open-set Multimodal 3D Mapping**，项目原始来源：<https://concept-fusion.github.io/>。把视觉语言特征融合到 3D 地图，支持开放词汇查询；对应本项目的语义对象检索，但其地图表示和本项目的 Blender/物理几何输出不同。
8. **VLMaps: Building Visual-Linguistic Maps for Robot Navigation**，项目原始来源：<https://github.com/vlmaps/vlmaps>。展示语言查询到空间位置的路线；可作为 G1 “语言找物体”的外部定位基线。必须区分“在 3D 地图中找到 feature”与“控制真实机器人到达并避障”。
9. **Holodeck: Language Guided Generation of 3D Embodied AI Environments**，<https://arxiv.org/abs/2312.09067>；官方代码：<https://github.com/allenai/Holodeck>。它是语言生成 AI2-THOR 具身环境，属于生成而非从真实视频重建，应作为邻近的语言到可执行环境工作。
10. **SceneScript: Reconstructing Scenes With An Autoregressive Structured Language Model**，<https://arxiv.org/abs/2403.13064>。它是结构化语言模型驱动的场景重建，和“场景程序”表达相关；不把它写成 Blender 或 metric reconstruction。
11. **Real2Code: Reconstruct Articulated Objects via Code Generation**，<https://arxiv.org/abs/2406.08474>。从观测生成可表达关节/结构的代码，适合支撑可编辑物体建模的邻近工作；它不是完整房间重建系统。
12. **Lab kitchen twin**，项目页：<https://frank-zy-dou.github.io/kitchen-twin/>；发布仓库：<https://github.com/Frank-ZY-Dou/kitchen-twin>。这是与本项目最接近的公开实例：手机 walkthrough、ViPE metric scan、对象测量，再由 GPT-6 Astra 生成 Blender 资产；仓库明确称为 published output 而非 pipeline source，故应作为公开演示证据而非独立论文基线。
13. **LiteReality-Agent**，<https://github.com/LiteReality/LiteReality-Agent>。其 README 描述从真实扫描到 simulation-ready 3D 环境、碰撞和 articulated assets；技术报告仍标为 coming soon，只能作为工程邻近工作引用。

## 建议的比较口径

除四个新方法外，baseline 表保留：ViPE-only（视频到 pose/depth 后按传统几何融合）、MapAnything-only（按官方 image-only 或 pose-conditioned 配置）、以及必要时 COLMAP/传统 VIO+MVS。用户要求的“5 种方法”若指 M1–M4 加一条传统基线，应在 caption 明确；若同时列 ViPE 和 MapAnything，则是 6 个系统，不能在表头写成 5 个。

所有误差先在同一世界坐标系下评估：pose 用 SE(3) ATE/RPE（若方法有尺度自由度，分别报告 similarity alignment 前后）；depth 用 valid mask 上 AbsRel、RMSE、δ1 和 scale-aware/scale-fixed 两列；模型用 GT mesh/体素的 Chamfer-L1、精度/召回 F-score、normal consistency、可见区域渲染 LPIPS/SSIM，以及对象级 3D IoU。对动态物体单列 mask，避免用不可比的背景/动态误差掩盖结果。

## 需要在 blog 中主动披露的风险

“语义正确”要由对象级检测/开放词汇查询和人工审计定义；“物理对齐”至少要有 metric 尺度、地面/墙体几何、碰撞测试和重渲染一致性证据。Astra 生成的不可见面、物体尺寸、材质和拓扑不能只通过漂亮渲染图证明。所有 pose 误差、深度误差、重建误差和下游成功率应同时公开失败例、随机种子、采样帧、checkpoint、坐标约定和是否使用 GT。
