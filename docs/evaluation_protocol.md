# 世界模型建图评测协议（draft）

本文档定义 blog 中四种方法和两个外部基线的可复现实验。它是评测协议，不代表任何实验已经运行。所有结果必须由配置、版本、随机种子和原始中间产物重算得到。

## 1. 方法、输入和公平比较

统一记号如下：

| ID | 方法 | 输入 | 主要输出 | 是否 metric pose |
|---|---|---|---|---|
| M1 | RGB-only + Astra/Blender | 采样 RGB | 场景模型 | N/A |
| M2 | ViPE + Astra/Blender | 视频或采样 RGB；ViPE pose/depth | 场景模型、ViPE pose、depth | 学习得到的近米制尺度；实测核验 |
| M3 | OpenVINS + MapAnything + Astra | 视频+IMU；采样 RGB | metric pose、metric depth、模型 | 是 |
| M4 | GT-pose diagnostic + MapAnything + Astra | 视频；建图阶段另给 GT pose | metric depth、模型 | 是（诊断参考） |
| B1 | ViPE standalone | 视频/采样 RGB | pose、depth | 学习得到的近米制尺度；实测核验 |
| B2 | MapAnything standalone (joint pose/depth) | 视频/RGB | pose、depth、点云/mesh | 方法自身预测 |
| B2p | MapAnything with OpenVINS pose | 视频+OpenVINS pose | depth、点云/mesh | 继承 OpenVINS |

补充系统 `M3b` 为已有的 SfM+IMU metric pipeline，`M3c` 为 batch-VIO pipeline；二者不能冒名替代主 M3。继承实验记录显示 M3b ATE=0.36644696 m，M3c 最新 ATE=0.3423 m，但 M3c 尚未重跑 depth；OpenVINS 原版曾发散至 6.92 km，`max_clones=31` 仅在 62 s 片段上验证且第 60 s 约 1.05 cm。上述数值只能作为 provenance/补充结果，不能填入 OpenVINS 的 M3 行。主 M3 必须先在全程完成 OpenVINS，再运行 MapAnything 和 Astra。

用户需求中的“5 种方法”与列出的 M1–M4、ViPE、MapAnything 不一致。本协议按 M1–M4、B1、B2 六组主结果处理，并把 B2p 作为与 M3 的 pose 消融。B1（ViPE）和 B2（MapAnything joint）生成几何时，均以各自标准输出的 pose+depth，使用同一参数融合成点云/mesh；不接 Astra。

所有系统固定同一视频、相机内参、分辨率、帧率、采样帧索引、Astra/Blender 版本、渲染器和渲染设置；各方法推断的材质是结果，不能强行设为相同 GT 材质。M4 的 GT pose 只允许进入 M4；它是诊断参考条件，不保证严格上界，也不能当作在线系统或与 M3 合并为一个分数。

## 2. 数据划分与取样

当前稳定 World Lobby360s 记录的原始序列为 8999 帧、25 fps、1280×960；若本实验使用该序列，必须固定建模采样索引 `0,50,...,8950`（180 帧），另采完全未被前端使用的新轨迹作为 independent holdout。若未来换 scene，按同样规则记录实际常量，不得复用这一组数字。

每个 scene 分成：

* `mapping`: 连续视频及 IMU，供方法运行；固定使用 `0,50,...,8950` 共 180 个采样帧给 M1–M4。
* `same-video withheld-from-modeller`: 同一视频中未给 Astra/融合建模器的帧，可用于前端观测帧诊断，但不是真正独立 holdout，因为前端可能已看到它们。
* `independent_holdout`: 新轨迹，完整隐藏于所有前端和建模器之外；每个 pose 有 RGB 和 GT depth。
* `geometry_holdout`: 真实仿真 mesh 的表面采样点和遮挡/不可见区域标记，专门评估模型几何。
* `task_holdout`: 下游任务轨迹和目标，完全不参与建图或模型调参。

固定 180 帧仍按每 2 秒采样；独立新视角按弧长、覆盖和近/远距离分层；至少报告 scene 数、每 scene 帧数、视角角度/距离范围及可见面积。固定公开 `scene_id`、`input_frame_ids`、holdout pose ids 和随机种子。当前只有单场景时，不做 leave-one-scene-out，也不使用 scene-bootstrap；报告单场景条件结果，连续块或重复 run CI 必须标明其含义。推广性结论需要额外独立场景。

主 5×4 图严格使用用户指定的 5 个建模采样帧：每行是同一个输入采样视角；第 1–3 列分别为 M1、M2、M3 在该视角的渲染，第 4 列为该输入采样图 GT。它不是 holdout 图。另做独立 holdout 图，使用新轨迹视角并加入 M4、B1、B2、B2p。

## 3. 坐标、深度和对齐规则

保存每帧 `T_world_camera`（相机坐标到世界坐标）、内参 `K`、图像坐标约定、右手系、深度轴和单位。所有模型先转换到统一 world frame；不得仅凭文件名猜轴。

深度协议必须区分：

* `z-depth`: 相机坐标 z 分量，适用于标准 pinhole 重投影；
* `ray-depth`: 沿视线的距离；不得与 z-depth 直接相减。

统一转成 z-depth 后计算像素指标；若模型只输出 ray-depth，记录转换公式和有效视场。评测域由 GT 有效深度及共同视域预先决定。标准深度误差在该域中的有效预测上计算，同时报告域内无效比例；另列固定规则的缺失惩罚误差，不得以共同有效 mask 隐藏失败。

所有方法先应用一次由 mapping 估计的全局 SE(3) gauge 变换，再在统一 world frame 评估；该单一变换用于 pose 与模型，并在变换后的场景中重新渲染；原始相机坐标下的 z-depth 数值不会因 SE(3) 世界坐标变换而缩放。M1 没有相机对应时，用预留配准集建立单次 diagnostic Sim(3)，单独披露 GT 辅助、变换和拟合点；不报告为原生米制精度。若预测与 GT 原本就在同一 world frame，才报告 raw；raw 不具备跨系统意义。

姿态误差分三种，不能混成一个数字：

1. metric translation：`e_t=||t_pred-t_gt||_2`（m），同时给相对场景对角线百分比；
2. rotation：`e_R=acos((trace(R_gt^{-1}R_pred)-1)/2)`（deg）；
3. up-to-scale 轨迹：对非 metric 方法先做 Sim(3) Procrustes（旋转、平移、单一正尺度），报告 alignment 前后 ATE；若系统保证尺度但原点不同，只做 SE(3)。

ViPE 具有学习先验，不能笼统写成“无尺度”；记录并报告 native-scale SE(3) 结果，Sim(3) 作为补充。M1 鼓励同时输出采样 camera pose；若没有，pose 指标为 `NA`，可做独立配准 diagnostic，但不得冒充估计 pose。M4 的 GT pose 只作为输入条件核验，不记作系统 pose 成绩。

## 4. 指标与表格 schema

主结果表每一行是 `scene × method × split`，每个指标报告 mean、median、P90；单场景不伪造 scene-bootstrap CI，可报告连续块/重复 run CI 并明确标注。建议 CSV/Parquet schema：

```text
scene_id, method_id, system_variant, split, seed, n_frames, n_valid_views,
pose_scale_mode, pose_align_mode, pose_ate_trans_m, pose_rpe_trans_m,
pose_rot_deg, pose_ate_trans_aligned, pose_rot_aligned_deg,
render_psnr_db, render_ssim, render_lpips, render_depth_absrel,
depth_absrel, depth_rmse_m, depth_delta1, depth_valid_coverage, depth_invalid_rate, depth_missing_penalty,
geom_chamfer_m, geom_completeness_5cm, geom_accuracy_5cm,
geom_normal_deg, geom_scale_mode, geom_valid_area_ratio,
semantic_instance_precision, semantic_instance_recall,
runtime_s, peak_gpu_gb, input_cost, model_version, config_hash
```

### 4.1 相机位姿

在 mapping 全轨迹上报告 ATE translation、RPE translation（固定 1 秒、10 秒间隔；按时间戳匹配）、rotation ATE/RPE。所有系统报告一次全局 SE(3) gauge 对齐后的结果；metric 系统也不能主张“不对齐”。ViPE 另给 native-scale SE(3) 和 Sim(3) 补充。对齐变换只在 mapping 区间估计，再用于 independent holdout。

### 4.2 渲染误差

每个 independent holdout GT pose 将预测模型渲染成 RGB 和 z-depth。RGB 给 PSNR、SSIM、LPIPS；深度渲染误差单独给 AbsRel、RMSE。这里的 render error 应使用相同 GT 相机 pose（isolated geometry render），另设一个 `estimated-pose render` 版本将系统估计 pose 直接用于渲染。两者差值只能作为耦合诊断，不能把 PSNR 差线性解释成 pose error。

### 4.3 深度图

原始前端 depth 在其实际观测帧评估；同视频未给 Astra 的帧只能标为 `same-video withheld-from-modeller`。严格 independent holdout 只评估 rendered-model-depth，除非明确让网络看到新图并单独标注。计算 AbsRel、RMSE、δ1 和 coverage；无效预测须报告 invalid rate，并按统一最大误差/缺失惩罚计入汇总。

### 4.4 模型几何

把预测 mesh/点云用同一个全局 SE(3) gauge 变换至 GT world frame；非 metric 方法另报 Sim(3) 补充。B1/B2/B2p 直接由各自 pose+depth 按统一 intrinsics、mask、voxel 和融合参数生成，不接 Astra。对 GT 表面均匀采样点 `P_gt`，预测表面采样 `P_pred`：

* accuracy：`mean_{p∈P_pred} min_q ||p-q||`；
* completeness：`mean_{q∈P_gt} min_p ||q-p||`；
* symmetric Chamfer：两者均值；
* 5 cm completeness/accuracy；
* 法向角误差和有效覆盖面积比。

报告可见表面与全场景两套结果，并把未重建区域记为缺失，不能用背景或空 mesh 获得虚高 accuracy。语义/物理主张必须另测：实例 precision/recall、类别混淆、可碰撞表面穿透率和支撑面高度误差。几何指标不能证明语义正确，语义指标也不能证明物理可用。

## 5. 同图轨迹和可视化

同一 3D axes 分开画全局 SE(3) 对齐轨迹和 Sim(3) 形状图；不把 raw 与 Sim(3) 混在一图。主轨迹图图例明确六个主系统及 GT 的对应关系：M1（可能 N/A）、M2 与 B1（共享曲线）、M3、M4 与 GT（重合）、B2；B2p 作为额外消融共享 M3 轨迹，并明确重叠/NA；M1 若无 pose 为 NA。补充图展示重叠关系和各自输出。

## 6. 下游任务评测

任务一（无人机参考图检索与复拍）：固定 20 个 query reference image，报告 top-1/top-5 场景检索率、成功复拍率，以及复拍图与参考图的 LPIPS/SSIM、相机位姿误差和目标可见面积。无人机初始位姿、控制频率、最大飞行距离、碰撞规则、每 query 时限固定；成功阈值在看测试集前用 validation scene 校准。

任务二（G1 语言找物）：至少 30 条语言指令、每类物体和距离分层；报告最终物体识别率、到达率、碰撞率、路径长度比、用时和语言 grounding precision/recall。指令、目标物体、初始位姿在 task_holdout 固定；不得靠人工看 GT mesh 修正地图。

## 7. 质量门槛与统计校准

不设按性能高低决定是否发布的门槛。只设数据完整性、版本锁定、输入/输出哈希、坐标/深度约定、holdout 隔离、失败日志和可重算性的质量 gate。任务成功阈值在 validation 上冻结后报告；pose、depth、几何只报告客观数值、分布和阈值曲线。

有多个场景时给 scene-bootstrap 95% CI；单场景只给连续块或重复 run CI，并明确其不代表跨场景泛化。报告 paired 差异。结论使用预注册的 primary metrics：pose 用全局 SE(3) gauge 后 ATE，深度用 AbsRel，几何用 Chamfer，任务用成功率。若 OpenVINS 全程发散，M3 的主结果必须记为失败/未完成并保留轨迹，而不能切换为 M3b 或 M3c。

## 8. 复现与审计清单

每次运行保存完整 config、git commit、容器/依赖锁定、GPU/驱动、模型 checkpoint 哈希、许可证、seed、输入文件哈希、运行时间、峰值显存、失败帧及日志。保存 raw outputs（pose、depth、mesh、render）、对齐变换、mask 和聚合脚本版本。

报告中必须显式声明：M4 使用 GT pose 是诊断参考条件而非严格上界；B2 使用 joint pose/depth，B2p 使用 OpenVINS pose；ViPE 的 native-scale 配置；MapAnything 的深度轴和尺度；holdout 是否真正未进入所有前端；以及未验证的“空间智能、具身智能、SLAM 颠覆”只能作为假设或下游证据，不能从单个场景或视觉观感外推。

## 9. 稠密前端与数据来源补充

主 M2/B1 用完整视频推理，现有 ViPE 180 帧稀疏结果为补充条件。M3 的每帧 pose 必须标记 estimated/interpolated/propagated/missing；不能把插值视为逐帧独立优化。MapAnything 的窗口合并只使用观测与允许的输入位姿，不用逐窗 GT 拟合；M4 仅允许 GT pose 输入。M1 冻结后追加的 RGB-COLMAP 轨迹是后处理基线，不是 Astra 位姿。
