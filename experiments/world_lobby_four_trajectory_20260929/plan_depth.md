# World Lobby 三轨迹 DA3 深度计划

## 目标

在 180 张建模采样帧和与之不重叠的 500 张评测帧上，分别以 ViPE、ORB-SLAM3 和 GT 位姿运行 pose-conditioned Depth Anything v3；产出可审计、可用于 Blender 测量的 M2/M3/M4 深度包，并与独立生成的 GT optical-Z depth 计算指标。

计划明确隔离 GT depth 和经过 GT 对齐的估计轨迹，确保 M2/M3 不发生 GT 泄漏。

## 已确认口径

- 仅使用三条轨迹：M2 = ViPE、M3 = ORB-SLAM3、M4 = GT；OpenVINS 不进入本次深度流程。
- ORB-SLAM3 缺失源帧 0–244；从其首个有效源帧 245 到末帧 4498 的共同覆盖区间，按时间均匀选取 180 个唯一原生帧。
- 以 session `inputs/cam0/data.csv` 中的 `source_index` 和 `timestamp_ns` 绑定 PNG，禁止按 MP4 解码序号配对。
- 从共同覆盖区间的剩余帧中，确定性、均匀地选取 500 张与上述 180 张完全不重叠的非采样评测图；单独记录选择算法、索引和哈希。
- 三种方法使用相同的 `depth-anything/DA3-GIANT` checkpoint、RGB、内参、4 视图窗口和 overlap=2；每种方法分别输入自己的原始 metric 位姿，并通过 `align_to_input_ext_scale=True` 对齐输出尺度，因此深度允许随轨迹变化。

## 数据与坐标适配

- 新增采样清单生成器，读取：
  - `world_lobby_four_trajectory_20260929/contract.json`
  - session `inputs/cam0/data.csv`
  - ORB-SLAM3 位姿有效性
- 输出 180 帧建模 manifest 和 500 帧评测 manifest，记录源索引、时间戳、RGB 路径与 SHA256。
- 位姿来源固定为：
  - M2：ViPE frozen `camera.npz`
  - M3：ORB-SLAM3 frozen `camera.npz`
  - M4：session `ground_truth/camera.csv`
- 按精确 `timestamp_ns` 关联，不插值、不外推。
- 推理使用各方法未经 GT 评测对齐的原始 metric 轨迹，不读取 `evaluation/aligned_common_trajectories.npz`。
- 统一验证 OpenCV RDF camera-to-world，并在 DA3 适配层显式转换为 DA3 所需的 extrinsics 方向。

## DA3 推理与输出

- 基于 `reconstruction/vendor/vipe_official_95a8816/vipe/priors/depth/dav3/api.py` 封装独立批处理入口。
- 使用 `depth-anything/DA3-GIANT`：`DA3METRIC-LARGE` 没有 camera encoder，不能接收 pose-conditioned 多视图输入。输出通过各方法的 metric pose 对齐到米制尺度。
- 四视图处理分辨率设为 392；504 在当前 RTX 3080 10 GB 上会 OOM。
- 将 180 帧建模集和 500 帧评测集分别组成 4 视图、步长 2 的窗口；尾部窗口锚定各自最后一帧。
- 两套数据不混合窗口，防止 500 张评测图改变 180 张建模深度。
- 每个窗口传入固定内参和该方法的四个位姿，启用 `align_to_input_ext_scale=True`。
- 每视图保存：
  - `depth_z_m`
  - 处理后内参
  - valid/sky/confidence 信息
  - 输入位姿和预测位姿
  - scale factor
  - 源帧身份
  - 模型和运行配置
- 每个窗口使用临时文件后原子提交，并支持断点续跑。
- 重叠帧采用“窗口中心性最高、平局取较早窗口”的统一规则。
- 分别生成 M2/M3/M4 的 180 帧建模几何包和 500 帧只读评测预测；不能混用历史 MapAnything 的 earliest-window 融合规则。

## GT depth 生成

- 当前 session 没有现成 GT depth 文件。
- 三种方法的 180 帧和 500 帧预测必须先全部完成、冻结并记录哈希，之后才允许加载 GT 场景和 GT 相机位姿。
- GT 场景使用 `drone-web/scenes/world_lobby/lobby.usda`。
- GT depth 不得进入 DA3 推理或 Blender 建模包。
- 复用 `world_model_blog/scripts/evaluate_novel_depth_blender.py` 的 Blender BVH 直接射线求交方案。
- 按 GT 相机光心、OpenCV RDF 方向和固定内参计算 camera optical-Z metres，避免直接采用可能混淆 ray-distance 与 optical-Z 的 compositor depth。
- 180 帧和 500 帧协议均使用固定、确定性的 160×120 原图像素网格，即每帧 19,200 条 GT-only 射线。
- 分别保存：
  - `truth_z_m`
  - `pixel_uv`
  - `timestamp_ns`
  - GT 有效域
  - GT 场景、位姿及采样 manifest 哈希
- 预测深度通过其处理后内参精确映射回相同的原图像素射线，并进行双线性采样。

## 深度指标

主评测不进行尺度拟合。GT 有效域固定为有限 optical-Z `[0.1, 30] m`，不得使用预测有效性缩小 GT mask。

每种方法分别在 180 帧建模集和 500 帧评测集报告：

- 有效覆盖率
- 无效率
- MAE（m）
- RMSE（m）
- AbsRel
- δ1：比例误差小于 `1.25`
- δ2：比例误差小于 `1.25²`
- δ3：比例误差小于 `1.25³`
- 30 m 缺失惩罚 MAE
- 逐帧指标
- 配对预测与 GT 深度数组

可以另外报告“每帧中值尺度对齐”诊断，用于区分绝对尺度误差和相对形状误差，但必须与无尺度拟合的主结果分栏，不参与主排序。

在相同帧集合上执行按帧配对 bootstrap，为三种方法的主指标及方法间差值提供 95% 置信区间。最终输出机器可读 JSON/CSV，以及 180 集和 500 集的汇总图。

## 文件结构

计划在 `world_lobby_four_trajectory_20260929/` 下生成：

```text
data/depth_samples/
├── modeling_180.json
└── eval_500.json

depth/
├── m2_vipe/
│   ├── modeling_180/windows/
│   └── eval_500/windows/
├── m3_orb/
│   ├── modeling_180/windows/
│   └── eval_500/windows/
└── m4_gt/
    ├── modeling_180/windows/
    └── eval_500/windows/

packets/
├── M2/
├── M3/
└── M4/

evaluation/depth/
├── gt/
└── metrics/
```

仅 180 帧建模集写入 Astra `packet.json`；500 帧集合严格标记为 evaluation-only。

## 验证与审计

1. 先运行一个四视图窗口的 smoke test，检查：
   - extrinsics 方向
   - 深度为正且有限
   - metric 标志
   - 尺度
   - 重投影
2. smoke test 通过后，再执行三个方法的完整任务。
3. 自动验证：
   - 三种方法使用完全相同的 180 帧和 500 帧集合
   - 两个集合交集为空
   - 每种方法 680/680 位姿命中
   - 旋转矩阵合法
   - 输出哈希完整
   - 重叠去重后每帧唯一
4. M2/M3 manifest 必须证明没有读取：
   - GT 位姿
   - GT 对齐后的轨迹
   - GT depth
5. M4 manifest 明确标记 GT 只作为相机位姿输入。
6. 扩展 `world_model_blog/src/evaluation/depth.py` 的既有指标逻辑，加入 MAE、δ2、δ3 和确定性 bootstrap。
7. 使用小型合成深度 fixture 验证：
   - optical-Z 定义
   - 缺失惩罚
   - 双线性像素映射
   - 中值尺度诊断

## 实施步骤

1. 实现共同覆盖区间的 180 帧建模清单和不重叠的 500 帧评测清单。
2. 实现三条轨迹的精确时间戳关联和坐标约定检查。
3. 实现 pose-conditioned DA3 四视图窗口推理、断点续跑和原子输出。
4. 按中心性去重，生成 M2/M3/M4 的 180 帧 Blender 建模深度包。
5. 为三个方法生成并冻结 500 帧 evaluation-only 预测。
6. 冻结预测哈希后，从 GT USD 场景生成 180/500 两套 optical-Z 真值。
7. 计算三种方法在两套数据上的深度指标、置信区间和汇总图。
8. 执行完整性、尺度、坐标和无 GT 泄漏审计。

## 与历史 World Lobby 流程的区别

- 历史 M2 使用 ViPE 的 UniDepth 深度；本次 M2/M3/M4 统一使用 pose-conditioned DA3。
- 历史 M3/M4 使用 MapAnything；本次统一为 DA3，以输入相机轨迹作为主要变量。
- 180 帧用于后续 Blender 建模；额外 500 帧仅用于深度泛化评测，不进入建模包。

## 实施进度（2026-09-30）

全部计划项已完成：

- [x] 保存并确认本实施计划。
- [x] 生成共同覆盖区间的 180 帧建模清单和不重叠的 500 帧评测清单。
- [x] 完成 ViPE、ORB-SLAM3、GT 三种位姿的精确时间戳关联；三种方法均命中 680/680 帧。
- [x] 实现并运行 pose-conditioned DA3-GIANT 四视图窗口推理、断点续跑和原子输出。
- [x] 按“最大中心性、平局取较早窗口”完成重叠去重。
- [x] 生成 `packets/M2`、`packets/M3`、`packets/M4` 三套 180 帧 Blender 建模深度包。
- [x] 生成三种方法的 500 帧 evaluation-only 深度预测。
- [x] 从 `lobby.usda` 通过 Blender BVH 直接射线求交生成 180/500 两套 GT optical-Z。
- [x] 计算无尺度拟合主指标、中值尺度诊断、逐帧指标和 paired bootstrap 置信区间。
- [x] 8 项单元测试通过，最终 `--require-results` 完整审计通过，无 linter 错误。

实际运行中发现 M4 的 `eval_500` 最后两个窗口相机中心完全静止，DA3 的 pose-scale 对齐会得到零尺度。实现对这两个窗口使用了有记录的远基线锚帧回退：

- `depth/m4_gt/eval_500/windows/window_0247/manifest.json`
- `depth/m4_gt/eval_500/windows/window_0248/manifest.json`

该回退不插值位姿、不读取 GT depth；只在同一 M4 评测集合内加入确定性的非零基线相机。

### 已生成产物

- 采样清单：`data/depth_samples/modeling_180.json`、`data/depth_samples/eval_500.json`
- DA3 窗口及去重结果：`depth/m2_vipe/`、`depth/m3_orb/`、`depth/m4_gt/`
- Blender 建模包：`packets/M2/`、`packets/M3/`、`packets/M4/`
- GT optical-Z：`evaluation/depth/gt/`
- 指标、逐帧 CSV、paired depth 和汇总图：`evaluation/depth/metrics/`
- 最终验证：`evaluation/depth/verification.json`
- 运行命令：`COMMANDS.md`

## 当前结果

主指标没有进行任何尺度拟合。

180 帧建模集：

- M2（ViPE）：RMSE 2.7339 m，AbsRel 0.1906，δ1 0.8289，覆盖率 99.56%。
- M3（ORB-SLAM3）：RMSE 2.7905 m，AbsRel 0.2038，δ1 0.8002，覆盖率 99.74%。
- M4（GT pose）：RMSE 2.8187 m，AbsRel 0.1887，δ1 0.8436，覆盖率 98.11%。

500 帧非建模评测集：

- M2（ViPE）：RMSE 2.8562 m，AbsRel 0.2162，δ1 0.7505，覆盖率 99.59%。
- M3（ORB-SLAM3）：RMSE 3.2678 m，AbsRel 0.2582，δ1 0.7375，覆盖率 99.30%。
- M4（GT pose）：RMSE 2.9699 m，AbsRel 0.2195，δ1 0.7665，覆盖率 98.19%。

每帧中值尺度校正仅作为诊断，不参与主排序。校正后：

- 180 帧 RMSE：M2 0.5152 m、M3 0.5157 m、M4 0.5150 m。
- 500 帧 RMSE：三者均约 0.54 m；M2 0.5413 m，M4 0.5403 m。

## 为什么 M4 pose 更准确，但原始 depth 指标没有优于 M2

相机位姿精度和最终深度精度不是单调对应关系。这里有四个具体原因：

1. **DA3 仍然是预测模型。** GT pose 只提供相机几何条件和尺度参考，不会把 DA3 的单帧语义偏差、边界误差、遮挡错误或网络固有深度偏差变成 GT depth。
2. **当前差异主要是每帧/每窗口尺度误差。** 中值尺度校正后，三种方法 RMSE 几乎完全相同，说明它们恢复的相对深度形状接近，主指标差异主要来自 DA3 将预测相机和输入轨迹做 Umeyama 尺度对齐时产生的尺度波动。
3. **M2 的轨迹尺度误差可能偶然补偿 DA3 的深度尺度偏差。** M2 pose 本身比 GT 差，但其局部平移尺度不一定只产生负面影响；当它与 DA3 原始尺度偏差方向相反时，无尺度拟合指标反而可能更低。这是误差抵消，不表示 M2 pose 比 GT 更正确。
4. **M4 覆盖率更低，并存在静止窗口。** M4 在 180/500 集的有效覆盖率分别约 98.11%/98.19%，低于 M2 的 99.56%/99.59%；末尾两个完全零基线窗口还需要锚帧回退。覆盖缺失和低基线会恶化 RMSE及缺失惩罚指标。

因此当前结果应解释为：

> GT pose 明显提高了相机轨迹真实性，但在 DA3-GIANT 的四视图尺度对齐机制下，它没有自动提高原始 metric depth；三种方法的相对深度形状几乎相同，主要差别来自局部尺度对齐、低基线窗口和有效覆盖率。M2 的较好原始 RMSE 包含误差抵消，不能据此判断其几何位姿优于 M4。
