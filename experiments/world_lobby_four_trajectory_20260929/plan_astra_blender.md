# 新版 M1–M4：Astra 调用 Blender 语义建模计划

日期：2026-09-30。状态：四组模型已完成独立建模、修订、最终复审与冻结；统一 GT 评测、本地网页验收、HF 上传及远端模型/指标哈希核验均完成。用户已明确授权完成后上传指定 HF Space。

工作目录：`/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929`。下文路径除另有说明外均相对该目录。

## 1. 目标与依据

依据 [blender_workflow.md](../world_model_blog/blender_workflow.md)，执行“独立输入包 → Astra 看图与几何测量 → 对象拆解和参数估计 → 编写 bpy 从空场景建模 → 输入相机渲染对照 → 独立审查与修订 → 导出冻结 → 独立 GT 评测”。四个方法均重新建模，包括 M1，统一输入 RGB 集合和预算。

方法定义替换为 [Ooliva/world-lobby-exps-new](https://huggingface.co/spaces/Ooliva/world-lobby-exps-new) 的 M1–M4。本次已通过认证只读访问线上 Space，并核对[本地发布页面](publication/huggingface/space/index.html)、[发布清单](publication/huggingface/dataset/release_manifest.json)、[深度计划](plan_depth.md)、[四轨迹统一对比计划](四轨迹统一对比_c01acd21.plan.md)和现有 packet。

线上核验日期：2026-09-30。私有 Space 的 commit 为 `9aaa67504e2a16dc51f7ba71a58c50d2d90c181c`，线上 `index.html` 的 SHA256 为 `537b6f5b3955f77b3bc9c71137726a9094fc1d2887b7ad4c2f85c23404701198`；本地页面 SHA256 为 `eb3832e5944c9d262cf0261fb0fdf057f7550927bd87c36e935c1021ad877108`。

**线上与本地进度不同：**线上 Table 1 的 M1–M4 定义与本计划一致，但页面仍写“只发布位姿，下游 DAV3 / Astra 未运行”；本地 `plan_depth.md` 已记录 DA3 完成，且有三套 packet。故方法定义依据线上，深度输入和完成状态依据本地证据，不能将本地深度结果描述为已经发布到线上。此轮只读核验，没有修改 HF 内容；凭据不写入本计划。

执行时追加核验（2026-09-30 04:30 香港时间）：Space 已更新至 `f310ff4e8f38521d1fa42fec1379fd7c22400476`，线上 index 哈希为 `eb3832e5944c9d262cf0261fb0fdf057f7550927bd87c36e935c1021ad877108`，与本地深度版页面一致。上述差异是编写计划时的历史状态，现已消除。发布前仍会再次核对远端版本并保存备份。

四轨迹计划中的 GT、ORB-SLAM3、ViPE、OpenVINS 是位姿对比集合，不能将其中四条曲线直接对应建模 M1–M4。建模集合保留线上定义，OpenVINS 不作为 M1。

## 2. 固定新版方法

| 方法 | Astra 的输入 | 位姿与尺度 |
|---|---|---|
| M1：纯视觉 + Astra | 同一组 180 张 RGB、帧身份、公共相机标定 | 无外部位姿和深度，从 RGB 推断布局、检查相机与假设尺度 |
| M2：ViPE + DAV3 + Astra | 180 张 RGB + ViPE 原生位姿 + ViPE pose-conditioned DA3-GIANT 预测深度 | 保留 ViPE 原生米制尺度，不做 GT 对齐 |
| M3：ORB-SLAM3 + DAV3 + Astra | 180 张 RGB + ORB-SLAM3 monocular-inertial 原生位姿 + 对应 DA3-GIANT 预测深度 | 保留 ORB-SLAM3 原生米制尺度，不做 GT 对齐 |
| M4：GT pose + DAV3 + Astra | 180 张 RGB + 允许使用的 GT 相机位姿 + 对应 DA3-GIANT 预测深度 | GT 只提供相机位姿，不提供 GT 深度或场景几何 |

M1 方法说明显式写为“RGB-only，已知公共内参”；标定不提供场景尺寸。M1 不暗中运行 ViPE、ORB-SLAM3、COLMAP 或预测深度管线改变基线定义。

历史 M2 的建模深度由 UniDepth 改为 DA3；ViPE 上游轨迹生成保留其既有配置。历史 M3 的 OpenVINS + MapAnything 改为 ORB-SLAM3 + DA3；M4 的 MapAnything 改为 DA3。OpenVINS 仅保留在已有轨迹诊断图中。TSDF 如需保留，应作为独立传统基线，不是本轮语义建模的必要前置步骤。

## 3. 已有输入与准备工作

唯一会话：`../vio-reconstruction/sessions/lobby_orb_success_20260929T123153`，约 180 秒、4499 个原生 RGB 帧。共同有效源帧区间为 **245–4498**，共 4254 帧。

| 内容 | 路径与当前状态 |
|---|---|
| 建模采样 | `data/depth_samples/modeling_180.json`，180 帧 |
| 评测采样 | `data/depth_samples/eval_500.json`，500 帧，与建模集不重叠 |
| M2 位姿 | `frozen/vipe_default/camera.npz` |
| M3 位姿 | `../stable_orbit_orb_success_20260929/frozen/camera.npz` |
| M4 位姿 | 会话 `ground_truth/camera.csv`，只向 M4 提供 180 个采样相机 |
| 已有建模包 | `packets/M2/packet.json`、`packets/M3/packet.json`、`packets/M4/packet.json`，均声明 180 RGB / 180 geometry、COMPLETE |
| 建模深度 | `depth/m2_vipe|m3_orb|m4_gt/modeling_180/consolidated/` |
| M1 输入 | 待创建，只含相同 180 张 RGB、帧身份和公共标定 |
| Blender | 已发现 `/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender`，执行前记录实际版本 |

本次仅核对文档、文件位置及 packet 字段；完整哈希与数值审计放在阶段 A，不能提前声明全部通过。

公共原图为 1280×960，`fx=fy=762.8`、`cx=640`、`cy=480`，无畸变。深度反投影使用每份 NPZ 的处理后 `intrinsics`，不能对缩放后的深度直接套原图内参。

沿用已经生成的 DA3-GIANT 深度：4 视图、overlap=2、process resolution=392、`align_to_input_ext_scale=True`。重叠帧选择“最大窗口中心性，平局取较早窗口”。不为本轮建模重新推理；发现损坏时单独修复并记录新版本。

## 4. 任务隔离、工具与预算

四个方法分别在新的 **GPT-6 Astra** 会话中执行，记录实际模型标识。只提供本方法净化输入、无场景参数的公共工具、本轮建模契约和空输出目录。计划编写上下文已经接触发布和评测说明，不能直接作为声称未接触评测的建模作者；后续作者和审查者均使用新的方法专属上下文。

重写本轮 `modelling_contract.md`，不能照搬仍写着 OpenVINS / MapAnything 的旧约定。输入采用文件白名单，尽量实体复制到隔离目录，避免可遍历回完整数据树的软链接；M4 只给允许的采样相机矩阵，不开放整个 GT 目录。

作者禁止读取 GT 场景 / mesh / USD、GT depth、对象标签、评测图像和评分、500 集、GT 对齐轨迹、历史模型和场景专用参数、其他方法的结果。M4 的采样 GT 相机矩阵是明确例外。可以复用经检查的通用数学、网格、渲染与导出工具，不能复用旧场景尺寸、家具布局或材质赋值。

日志明确区分文件系统级隔离、工具访问记录与作者声明；环境不能强制隔离时披露限制，不能把访问声明当成完整审计。

| 每方法项目 | 统一上限或规则 |
|---|---|
| 完整场景版本 | 最多 5 版，含初版与修订 |
| 视觉检查渲染（修订协议） | 每版固定 10 张；最多 5 版共 50 张，并保留最多 10 张有理由的局部补充检查；作者与审查者复用同一图像不重复计数 |
| 固定检查帧（修订协议） | 建模采样序号 33、61、74、82、91、100、108、118、129、155，四组使用同一帧身份 |
| 全量输入几何检查 | M2–M4 最多 3 次，每次 180 帧 BVH optical-Z 检查 |
| 独立审查 | 至少一次具体问题初审，并复审最终候选版本 |
| 超预算 | 停止修模，冻结并保留未解决项，标明质量限制 |

修订后的 10 个固定视角不是按帧序号等间隔选取。协调器使用闭合 GT 相机中心轨迹的三维累计弧长，在所有确定性等弧长相位中选择对 180 帧联合可观测场景表面覆盖率最高的一组，再以间隔误差破平局。闭环总长为 44.5266 m，理想间隔为 4.4527 m，实际间隔为 4.3090、4.7641、4.0985、4.4041、4.7171、4.4633、4.6113、4.3039、4.3735、4.4817 m，最大间隔误差为 0.3541 m。

以 0.25 m 世界坐标体素统计，10 个视角覆盖 11,812 / 14,719 个 180 帧联合可观测表面体素（80.25%）。人工检查确认其共同覆盖镜面墙、中央座椅与花槽、玻璃门窗、接待台、大厅纵深、主要地面与顶灯区域。受固定 10 个透视视角和遮挡限制，不能把“看到整个场景”解释为 100% 表面体素或隐藏表面覆盖；如要求同一体素定义下严格 100%，实测至少需要当前确定性覆盖程序保留 120 个视角。选择结果、10 张 RGB 副本、时间戳、哈希、覆盖审计和可复现脚本分别保存在 `fixed_check_views/` 与 `code/select_fixed_check_views.py`。GT 位姿和 GT 深度只由协调器用于选择与覆盖审计，不把矩阵或深度放入检查视角包。

该修订用于下一次重跑。已经冻结并发布的本轮 M1–M4 模型实际使用的是历史检查序号 0、45、90、135、179；本次修改不追溯改写既有渲染计数、审查记录、模型或评测结果。

全量 BVH 检查不做材质着色，独立记录射线量、耗时和次数；不能用该名义隐藏额外视觉渲染。GT 评测在冻结后另计，结果不反馈修模。记录模型 token（可获得时）、工具次数、耗时及失败重试。本轮是一次工程实验，不宣称重复建模统计结论。

## 5. 分阶段实施

### A. 协议冻结与独立输入包

1. 保存新版方法、预算、检查帧、阈值、有效域、缺失处理和随机种子至 `astra_blender/configs/run_contract.json`。
2. 数据准备程序核对 180 / 500 的源索引、时间戳、互斥性和 RGB 哈希；作者只拿 180 集。
3. 校验 M2–M4 每帧 RGB / geometry SHA256、旋转矩阵、单位、内参、深度轴和有效掩码。packet 位姿须与 NPZ 的 `input_camera_to_world` 一致；不能用 `predicted_world_to_camera` 替代方法原生轨迹。
4. 保留现有 packet 原件，在 `astra_blender/inputs/M1..M4/` 创建净化输入；M1 不含外部 pose / depth 字段。
5. 每帧记录 `sample_index`、`source_index`、`timestamp_ns` 和哈希；M2–M4 提供 `depth_z_m`、`intrinsics`、`valid_mask`、`confidence`、`sky`、原生位姿和窗口来源。
6. 做通用相机投影与尺度冒烟检查，验证通过后冻结输入清单。

验收：四组 RGB 身份一致；M2–M4 均有 180 个合法输入相机；500 集、GT 评分与其他方法信息不进入作者包。

### B. Astra 看图、识别对象和测量

1. 查看覆盖全部 180 帧的联系图，并检查关键帧原图；建立对象清单和证据帧。
2. 先确定建筑边界、门窗和通行空间，再识别本次图像中的家具、植物、镜面、吊灯等，不继承历史对象数量或尺寸。
3. M2–M4 调用深度反投影、平面拟合、三角化、射线与平面求交和跨视角重投影，估计对象参数。
4. M1 从透视、消失点、RGB 对应、遮挡和物体比例推断布局与检查相机，显式记录尺度假设和不确定性；不声称恢复唯一真实米制尺度。
5. 保存像素测量、帧、方法、残差、置信度与冲突；镜中内容不当作真实空间，隐藏背面、厚度和细节标为推断。

输出 `object_inventory.json`、`measurements.json`、`layout.json`、`camera_checks.json`。难以解释的帧保留失败或低置信度记录，不删除困难样本。

### C. Astra 编写 bpy，从空场景创建模型

按照结构、主要家具、装饰细部、材质灯光的顺序创建参数化语义对象。每个对象有稳定 ID、类别、组件、尺寸、证据和空间关系；一个对象可包含多个 mesh。材质使用程序化参数或本方法 RGB 信息，隐藏结构、BRDF、光照和物理参数的近似须声明。

M2–M4 保持输入尺度，可采用有记录的刚性坐标 / 重力归一化，统一缩放为 1。列向量约定如下：

```text
p_cam_cv = depth_z_m × inverse(K_depth) × [u_depth, v_depth, 1]^T
p_input  = input_camera_to_world × homogeneous(p_cam_cv)
p_model  = model_from_input × p_input

cv_from_blender_camera = diag(1, -1, -1, 1)
model_from_blender_camera = model_from_input
                           × input_camera_to_world
                           × cv_from_blender_camera
```

明确 `model_from_input` 的方向；验证 Blender lens、shift、pixel aspect 和分辨率的实际像素投影，不逐帧移动 M2–M4 相机掩盖模型误差。

执行阶段的命令示例（下列程序届时创建）：

```bash
/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender \
  --background --factory-startup --threads 4 \
  --python-exit-code 1 \
  --python astra_blender/models/M2/build_scene.py
```

四组运行各自程序。记录 Blender、渲染后端和硬件；资源不足时使用统一的较低分辨率或 CPU 配置并留档。

### D. 输入对照与修订

每版渲染固定 5 个输入视角，对照 RGB 检查对象遗漏 / 重复、轮廓、尺寸、遮挡、法线、穿插、材质和光照；必要时在 60 张预算内增加局部检查并说明原因。

M2–M4 在初版、主要修复后和冻结前各做一次全量输入检查：用本方法 180 个相机对模型射线求交，计算 optical-Z；通过处理后内参采样 DA3 深度。报告 RMSE、AbsRel、逐帧统计、模型命中覆盖率及缺失惩罚，不能因模型未命中缩小原定输入有效域。BVH 的沿射线距离必须转换为相机 Z。

M1 无输入深度，深度一致性记为 N/A；检查 RGB 对应重投影、透视、轮廓、遮挡和相机覆盖率。尽量保存 180 帧自身估计相机，对不可靠帧明确标记，不借其他方法相机补齐。

用 RGB 与输入测量定位冲突，不能把逼近 DA3 当作逼近 GT 的证明。每版记录修改依据、检查结果、预算和未解决项。

### E. 独立审查与最终复审

审查者只看允许输入和当前模型，按对象 ID、证据帧、问题和修复建议返回清单。覆盖图像对应、相机、缺失对象、法线、严重穿插、支撑、门洞通行、碰撞代理、语义记录、尺度与输入权限。

作者在预算内修正后，最终候选版再次复审。不能沿用旧版审查结论认证最终修复。预算耗尽仍有缺陷时，记录 `quality_status=limited`；冻结用于评分与质量验收通过是不同状态。

### F. 导出和冻结

每组交付：`scene.blend`、`scene.glb`、`build_scene.py` 与模块 / 参数、`objects.json`、`colliders.json`、`cameras.json`、`input_access_log.json`、`iteration_log.json`、`modelling_manifest.json`、测量记录、检查图片、独立审查和 `SHA256SUMS`。

对象表包含类别、组件、尺寸、关系、证据帧与观测 / 推断来源。manifest 包含模型标识、输入哈希、坐标方向、尺度、预算和未解决项。验证 Blender 可打开、程序可重建、GLB 可加载且语义 ID 可映射，打包所需资源并记录 Blender / GLB 材质差异。

冻结状态为 `frozen_for_independent_GT_evaluation`，另记质量状态。评分使用完整模型；展示用剖切或优化副本另存。脚本可重建不意味着重新调用 Astra 会产生完全相同的推理或模型，也不要求重新保存的 .blend 字节哈希一致。

## 6. 冻结后独立评测

### 配准

全部方法冻结后，独立评测程序才读取 GT。M2 / M3 在同一 180 个建模时间戳上，用输入轨迹与 GT 轨迹求一次全局 SE(3)，scale=1，固定应用于 180 / 500 集；M4 使用其输入 GT 坐标关系。

```text
GT_from_model = GT_from_input × inverse(model_from_input)
```

不通过 GT 表面 ICP、逐帧对齐或主结果尺度拟合优化评分。评测前后校验冻结文件哈希，评测结果不反馈本轮建模。

M1 无可验证的米制尺度。如有足够的冻结 RGB 估计相机，仅在 180 集上以相机对应拟合一次 Sim(3)，记录尺度、残差和退化检查，固定后评测 500 集。结果单列为“GT 相机辅助 Sim(3) 后的形状诊断”，不与 M2–M4 的 scale=1 主结果混排。对应不足或配准退化时标不可评，不使用 GT 几何手动摆齐。

### 三类结果与网页表格

以下表号参照本地扩展页面与后续报告布局；当前线上版本只展示位姿相关表格，尚无 Table 3–5，不能将本地占位表描述成线上现状。

| 结果 | 比较内容 | 对应展示 |
|---|---|---|
| Native depth | 原有 DA3 预测 vs GT 深度 | 保留 Table 2 / 3 的定义与来源 |
| Model depth / novel depth | 冻结 Blender 模型射线深度 vs GT 深度 | 180 集填 Table 2；500 集填 Table 4 |
| Input consistency | 模型深度 vs 自身输入 DA3 深度 | Table 5；M1 深度列 N/A，另报 RGB 检查 |

复用已有 GT optical-Z 协议：固定原图 160×120 网格、每帧 19,200 条射线、GT 有效 Z 为 `[0.1, 30] m`。报告 MAE、RMSE、AbsRel、δ1/δ2/δ3、逐帧统计、覆盖率和既有 30 m 缺失惩罚 MAE；声明交集误差的有效域，同时保留固定 GT 域的缺失惩罚。

180 / 500 结果分别输出，按帧配对 bootstrap 仅反映本场景帧间不确定性，不代表重复建模方差。500 集来自同一场景和会话，不称为跨场景泛化。固定评测相机的 RGB 图像在冻结后生成。附加 GT 表面距离评测须事先固定采样和可见性规则。

生成本地模型对比、表格和下载清单；远端发布单独处理。不得将 DA3 原生深度指标填为 Blender 模型指标，也不预设 M4 必须胜出。

## 7. 目录与执行顺序

下列内容均为待创建：

```text
astra_blender/
├── configs/             # 新版契约、权限、预算、视角和阈值
├── provenance/          # 输入哈希、来源、模型与工具版本
├── inputs/M1..M4/       # 各方法净化输入
├── tools/               # 无场景参数的通用工具
├── models/M1..M4/       # 程序、参数、模型、语义和日志
│   ├── analysis/
│   ├── checks/
│   └── independent_review/
├── evaluation/          # 冻结后独立评测，作者不可读
└── report/              # 本地表格、预览与下载清单
```

新增输入净化、相机适配、BVH 输入检查、场景验证和冻结工具。旧评测入口含固定历史路径和方法，必须先适配本轮会话、180 / 500 清单及 M1 规则，不直接执行旧入口。

顺序为 A 公共准备 → 四组独立执行 B–F → 全部冻结 → GT 评测 → 本地展示。可串行调度控制 GPU 占用，始终保持方法上下文和输出隔离。

## 8. 验收清单

- [x] 阅读历史工作流、深度与四轨迹计划，核对线上及本地新版方法定义。
- [x] 核对采样清单、M2–M4 packet 字段和 Blender 文件位置。
- [x] 核验线上 commit 与页面哈希，记录线上 / 本地进度差异。
- [x] 完整数据哈希与数值检查：680 张 RGB、540 份建模几何及三条位姿来源校验通过。
- [x] 新版协议冻结，四份独立净化输入准备完成，见 `astra_blender/provenance/input_audit.json`。
- [x] 四组各自完成 Astra 看图、对象清单与几何测量。
- [x] 四组均从空场景完成语义对象建模及预算内修订。
- [x] 完成独立初审和最终版本复审，保留全部遗留问题。
- [x] 四套交付由所附程序生成，可加载且语义映射完整；模型与程序冻结。
- [x] 独立完成 180 / 500 模型评测，M1 因有效相机不足标为不可评。
- [x] 本地报告明确区分 Native depth、Model depth 和 Input consistency。

交付标准是四组定义、输入、Astra 建模过程、语义模型、最终审查、冻结和独立评测均可追溯。仅有点云、融合网格或 Blender 包装文件不满足本计划的语义建模交付要求。

## 9. 本次实际执行记录（2026-09-30）

- 四组均由 GPT-6 Astra 独立方法上下文编写 bpy；Blender 5.2.0 LTS 从空场景构建。最终初审/复审均存入方法目录，最终质量状态全部为 `LIMITED`，不声称视觉复刻通过。
- 最终版本：M1 v2，M2 v2，M3 v3，M4 v3；检查渲染累计分别为 10/10/15/15 张，输入 BVH 检查为 N/A/2/3/3 次。
- M1 所有相机仍 `valid=false`，五个假设相机仅用于 RGB 检查，定量配准和 GT 模型深度标为不可评。
- M3/M4 v2 作者通过全局进程列表意外接触其他会话命令参数。v2 最终被拒绝并从候选中撤出；新的独立作者只拿原始 v1 脚本、原始自身测量与初审意见，在独立目录重新修订 v3。未向新作者提供 v2 代码、模型或结果。新的最终复审没有技术/输入协议阻塞。事件与补救记录：`astra_blender/provenance/process_scope_incident.json`。
- M1 v2 的单独修复说明由协调者依据作者脚本/日志及独立复审整理，明确标注来源，未冒称原作者陈述。
- 所有最终文件、预算、审查哈希和 GLB 语义组件映射检查均通过冻结门禁。被拒绝候选保存在 `astra_blender/rejected_candidates/`，不用于 GT 评分。
- 统一 GT 评测已在所有冻结完成后完成，文件哈希复核未改变；结果未返回建模作者。

### 冻结后 500 视角指标

| 方法 | AbsRel | RMSE (m) | Coverage | 缺失惩罚 MAE (m) |
|---|---:|---:|---:|---:|
| M1 | N/A | N/A | N/A | N/A |
| M2 | 9.2971% | 1.1567 | 99.7978% | 0.6087 |
| M3 | 8.3631% | 1.1040 | 99.9115% | 0.4995 |
| M4 | 10.7691% | 1.2798 | 99.9470% | 0.6450 |

完整 180/500 指标、逐帧结果、配准和配对 bootstrap 见 `astra_blender/evaluation/summary.json`。以上为一次工程建模实验，不代表重复建模方差或跨场景泛化。

### 发布完成

已上传到 https://huggingface.co/spaces/Ooliva/world-lobby-exps-new ，提交 `c0f13bbe500bb037b69633c39df82fa0c49d83f3`。Space 保持私有，四套 GLB/Blender、源程序与审查证据、原生/模型/输入一致性指标、180/500 逐帧 CSV 和深度 NPZ、图表及交互展示均已发布。重新下载首页、四个 GLB 和全部指标 JSON/CSV 校验一致。桌面 1440px、手机 390px 浏览器检查通过，四模型和完整/室内预览切换均能加载，无 JS/HTTP 错误或横向溢出。发布记录：`astra_blender/provenance/hf_upload.json`。

### 图表编号更新

按用户要求为报告补齐全部表格、图和子图编号；延续原报告 Table 1–5 / Figure 14，同一主页面的 Astra/Blender 区域为 Table 6–8、Figure 15–23，不再使用“位姿与原生深度报告”子页面。输入和渲染视角使用 (a)–(e) 子图编号。原 Figure 24 深度汇总图和 Figure 25 逐帧曲线已从发布页面及发布资产中移除，数值结果仍保留在 Table 6 和可下载的逐帧指标文件中。


### Table 6 新 GT 重算（2026-09-30，批次 20260930T021632Z）

按新要求，180 个建模视角、500 个互斥非建模视角的 GT 均由 Blender 从原始 USD 重新生成并保存；没有读取旧 GT 深度缓存。预测值来自最终冻结的完整 Blender 网格在同一 GT 相机与像素上的光轴 Z 深度。M2/M3 的一次 SE(3)、M4 输入坐标变换及全部模型文件保持不变；M1 相机配准不可验证，仍为 N/A。

- 新 GT：`astra_blender/gt_fresh_20260930T021632Z/`，包含 680 个逐视角 NPZ、两个集合 NPZ、相机与像素对应、SHA256 和生成记录。
- 新模型深度与指标：`astra_blender/evaluation_fresh_20260930T021632Z/summary.json`，模型深度也在本轮重新求交。
- 验证记录：`astra_blender/provenance/table6_fresh_gt_20260930T021632Z/`。USD / Blender 的可见网格、三角面数和世界边界一致；5120 条独立射线检查通过；独立 float64 指标复算及冻结哈希检查通过。
- 500 视角 AbsRel / RMSE：M2 9.2971% / 1.1567 m；M3 8.3631% / 1.1040 m；M4 10.7691% / 1.2798 m。重算汇总值与历史记录一致，本轮结果以新 GT 来源记录为准。
- Table 7 仍为模型对自身 DA3 输入一致性；Table 8 是原批次 DA3 深度评测，本轮未重算这两类指标。
- 发布包新增 GT 集合、逐视角 ZIP、生成与验证清单、复算脚本及说明。发布后的 HF 提交记录见该批次目录中的 `hf_upload.json`。
