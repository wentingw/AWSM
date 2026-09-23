# SceneWeft

**以几何为依据的智能体式重建：生成可编辑、可执行的三维场景。**

SceneWeft 是这组研究的私有代码仓库。项目研究 GPT-6 Astra 如何在 RGB 和可选几何证据约束下，生成包含命名部件、空间关系、可渲染相机和碰撞代理的 Blender 场景程序。这里的 agentic 指工具调用、检查和修订流程，不等于已经训练出具有时间预测能力的通用世界模型。

文章与研究资产：

- 中文博客：https://wentingw.github.io/astra-world-model-blog/
- English：https://wentingw.github.io/astra-world-model-blog/en.html
- 科研资产（当前为 private，需 HF 权限）：https://huggingface.co/datasets/Ooliva/astra-world-model-blog

四种方法为 M1 RGB-only、M2 ViPE、M3 OpenVINS+MapAnything、M4 GT-pose oracle；B1 共享 M2 frontend，B2 是已知内参 RGB-only 基线，B2p 共享 M3 frontend 但跳过 Astra。当前证据是单个静态合成 World Lobby 场景。M2 pose translation RMSE 为 0.118 m，M3 为 2.595 m；M4 的 GT pose 是输入条件，不是算法精度。

无人机 20 次中有 15 次无碰撞候选到达、5 次碰撞，精确复拍严格和宽松成功率均为 0/20。G1 的 30 条指令覆盖 5 类目标、每类 6 种改写，18 次在重建模型中接近目标成功，12 次规划失败；控制使用仿真器状态定位，未独立验证视觉物体身份。语义命名没有独立实例 precision/recall，碰撞体也不等于真实物性。

SceneWeft 与 SLAM 互补：SLAM/VIO 提供注册和几何约束，SceneWeft 将证据转成可编辑、可查询、可渲染并能进入声明仿真的场景程序。当前没有证据表明它超越、替代或首创 SLAM/agentic reconstruction。

复现说明见 [REPRODUCING.md](REPRODUCING.md)，冻结资产见 [artifact-lock.json](artifact-lock.json)。上游代码和资产保留原始 attribution 与许可条件；本仓库不新增开源许可证。
