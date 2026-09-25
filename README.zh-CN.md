# SceneWeft

**以几何为依据的智能体式重建：生成可编辑、可执行的三维场景。**

SceneWeft 是这组研究的私有代码仓库。项目研究 GPT-6 Astra 如何在 RGB 和可选几何证据约束下，生成包含命名部件、空间关系、可渲染相机和碰撞代理的 Blender 场景程序。这里的 agentic 指工具调用、检查和修订流程，不等于已经训练出具有时间预测能力的通用世界模型。

文章与研究资产：

- 中文博客：https://wentingw.github.io/astra-world-model-blog/
- English：https://wentingw.github.io/astra-world-model-blog/en.html
- 科研资产（当前为 private，需 HF 权限）：https://huggingface.co/datasets/Ooliva/astra-world-model-blog

四种方法为 M1 RGB-only、M2 ViPE、M3 OpenVINS+MapAnything、M4 GT-pose oracle；B1 共享 M2 frontend，B2 是已知内参 RGB-only 基线，B2p 共享 M3 frontend 但跳过 Astra。当前证据是单个静态合成 World Lobby 场景。M2 pose translation RMSE 为 0.118 m，M3 为 2.595 m；M4 的 GT pose 是输入条件，不是算法精度。

当前两个下游实验固定使用 **M4 场景**：无人机 20 次中有 **17 次无碰撞候选到达、3 次碰撞**，精确复拍严格和宽松成功率均为 **0/20**。G1 的 5 条受约束中文目标描述分别从 4 个起点执行，共 20 次；**目标身份、无碰撞导航、评估器可见性核验均为 20/20**。控制器使用仿真器状态定位；G1 使用已知语义地图和受约束语言解析，可见性是基于几何的评估，不是在线视觉识别。原 M3 记录保留为历史证据，不能视为受控的 M3/M4 对比。

本次同步对应当前博客提交 [`cd63134103e1f14660d00fd4d20988f25cbf50ea`](https://github.com/wentingw/astra-world-model-blog/commit/cd63134103e1f14660d00fd4d20988f25cbf50ea)，覆盖全部 8 张表格、几何表的 B2p、M1–M4 五视角 PSNR/SSIM/LPIPS、对比图、两项 M4 任务的 40 次执行记录、轨迹、终点图和回放视频。详细入口见 [当前网页证据索引](evidence/blog_20260925/README.md)。

建模、前端、融合、指标计算及任务相关代码与原始结果按字节保存，附 SHA256 清单。大型完整模型仍通过固定版本的 Hugging Face 资产读取；展示 GLB 对应固定的公开博客提交。历史脚本含原工作区绝对路径，重新运行前需按复现说明重定位，并使用新的输出目录。

SceneWeft 与 SLAM 互补：SLAM/VIO 提供注册和几何约束，SceneWeft 将证据转成可编辑、可查询、可渲染并能进入声明仿真的场景程序。当前没有证据表明它超越、替代或首创 SLAM/agentic reconstruction。

复现说明见 [REPRODUCING.md](REPRODUCING.md)，冻结资产见 [artifact-lock.json](artifact-lock.json)。上游代码和资产保留原始 attribution 与许可条件；本仓库不新增开源许可证。
