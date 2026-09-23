# M3 downstream evaluation plan

目标是证明 M3 产出的场景可被机器人查询、规划和验证，而不是展示“把目标位姿写进控制器后机器人走过去”。两个任务都在同一套冻结的 M3 Blender/scene representation 上运行；另建未见的查询视角与任务指令；目标物体允许在建图中被观察，否则任务变为未知物体探索，但目标 GT 位姿与查询答案不向建模器或导航器开放。

## 公共实验协议

固定一个 scene ID、坐标系、相机内参、机器人 URDF、碰撞层和随机种子。M3 只接收 RGB 视频与同步 IMU；OpenVINS 输出 pose，MapAnything 接收规范化后的图像、内参、pose 和 `is_metric_scale=True`，Astra 生成场景后冻结。任务运行时只能调用场景公开 API：对象类别/实例候选、语义 embedding、几何 mesh/TSDF、可见性、raycast、碰撞查询和渲染器；禁止读取 GT object pose、GT mesh 或隐藏的目标轨迹；在线 RGB/depth 仿真传感器可按统一传感器协议使用。每次 episode 保存输入、检索候选、规划轨迹、碰撞结果和最终 RGB/depth/pose，支持盲评。

对照至少包括：GT scene（评测参考）、M3 scene、M2 scene、M1 scene；再加 oracle ablation（M3 geometry + GT object labels，或 M3 scene + GT pose）只用于拆分语义和几何瓶颈，不能算主结果。M4 的 GT pose 只是条件诊断，不能标成严格上界。报告模型内成功与跨 GT 仿真迁移分开：前者衡量在重建世界中闭环执行，后者将同一个计划/控制器放入 GT 仿真碰撞世界，衡量地图到真实几何的外推。

## 任务一：无人机由参考图定位并复现视角

给定目标参考图 `I_ref`（从 held-out 的 GT 仿真相机位姿渲染），无人机从未见过该视角的起点出发，在 M3 场景中搜索对应区域，并在安全距离内拍摄 `I_out`。参考图不提供目标 pose、深度、地图坐标或文件名。

管线为：视觉语言编码器从 `I_ref` 提取全局/局部特征；在 M3 的对象/房间节点和可渲染 viewpoint cache 中检索候选；用多视角渲染 + feature matching/reranking 选目标；在地图上规划无碰撞 SE(3) 航路（ESDF/膨胀障碍，速度/加速度和视场约束）；在仿真中执行 position/yaw controller；到达后以模拟 RGB 传感器做图像重定位闭环微调，最后渲染/拍摄输出图。本文范围是仿真，不主张真实无人机部署。

主要指标：成功率（达到目标视图容差且无碰撞）、image retrieval Recall@1/5、最终相机平移误差（GT 仅用于评测）、旋转误差、目标区域 IoU、LPIPS/SSIM、航程、规划时间、碰撞/近碰撞率和重定位迭代次数。视角成功阈值建议同时给严格/宽松两档，例如平移 0.10/0.25 m、旋转 5°/10°，具体阈值随场景尺度预注册。把“在 M3 中渲染相似”与“在 GT scene 中真实视角复现”分别列出；后者要求输出相机轨迹在 GT mesh 上无碰撞且最终图像相似。

防泄露检查：参考图生成时只保留 RGB；候选 cache 的 pose 是 M3 估计 pose；目标 GT pose 只在 evaluator 中使用。若目标图由 GT 场景渲染，可把随机光照、纹理、轻微裁剪和相机内参扰动作为附加 robustness 轴。

## 任务二：Unitree G1 按语言指令找物体

输入如“找到厨房桌上的红色杯子并停在它前面”。语言解析为对象类别、属性、关系和终止条件；语义检索在 M3 对象节点、开放词汇特征和实例 mask 上产生候选。规划器先做房间/区域级导航，再做物体级视点选择和主动观测；每次观测用仿真 RGB（可加仿真传感器深度）更新 belief，处理遮挡和多个实例。局部规划使用占据/ESDF 碰撞体、G1 足底支撑和人体/关节限制。若已有可复用 G1 dynamic locomotion policy，则报告 dynamic locomotion；若没有，只做明确标注的 kinematic route demo，不能把运动学路径当成行走成功。

指标分三层：语言 grounding 的类别/属性/关系准确率与目标 Recall@K；导航的 SPL、成功率、路径长度、时间、碰撞/跌倒/最小障碍距离；终止状态的目标中心距离、朝向误差、可见面积和语言条件满足率。多实例场景必须报告 first-choice、最终选择和拒答/不确定率；不能把“看见同类物体”当成实例级成功。

三种评测世界要分开：

1. **M3-world closed loop**：G1 的观测、碰撞和动作都在 M3 导出的 mesh/语义场景中运行，测试 world model 是否可查询和可执行。
2. **GT-geometry transfer**：同一策略和初始条件转移到 GT 仿真 mesh；地图仍来自 M3，GT 只提供物理碰撞和 evaluator，测试几何误差导致的失败。
3. **同一仿真中的 RGB/physics robustness（可选）**：将相机噪声、动力学、摩擦、延迟和遮挡随机化；本文不包含实机部署，不能用仿真结果代替真实验证。

## 归因实验与展示素材

对 M3 逐项替换：GT pose（M4）、GT depth、GT semantic labels、GT mesh。若 M3-world 成功而 GT transfer 失败，优先排查几何、尺度、渲染域差与定位；检索失败排查语义与外观；运动失败排查控制和碰撞。只有对应替换消融支持时才作因果归因。若模拟自定位直接读取 GT pose，必须标记为 `state-oracle`，并让所有方法在相同条件下比较；目标 GT object pose 仍禁止给 planner，但模拟 RGB/depth 传感器是合法输入。每个任务展示一条完整 episode（输入、候选、地图路径、碰撞体、终止图）及实际出现的代表性失败 episodes（若无失败不人为制造）；画出 M1–M4 的 trajectory、目标视锥、GT 轨迹及误差，不只放最佳截图。

最低可接受的发布表格包含：方法、是否使用 GT、scene-world success、GT-transfer success、collision rate、localization/grounding metric、平均/中位数规划时间、样本数和 95% bootstrap CI。所有阈值、失败计数规则、动态物体 mask、随机种子和评估脚本随 blog 工作目录发布。

## 关键实现接口（建议）

`SceneQuery(text, attributes, relation) -> candidate instances + uncertainty`；`RenderView(T_cam, intrinsics) -> RGB/depth/mask`；`CollisionCheck(robot_state, swept_volume) -> distance, contacts`；`PlanSE3(start, goal, ESDF) -> trajectory`；`PlanG1(start, goal, traversability) -> footstep/velocity trajectory`。接口只返回冻结 M3 世界的信息，GT evaluator 单独进程运行并不暴露其值给 planner。
