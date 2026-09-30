# 新版 M1–M4：Astra 调用 Blender 语义建模计划

日期：2026-09-30。状态：本轮建模、独立审查、冻结和评测完成；仅发布 Table 9/10/11 指标。

工作目录：`/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929`。下文路径除另有说明外均相对该目录。

## 1. 目标与依据

依据 [blender_workflow.md](../world_model_blog/blender_workflow.md)，执行“独立输入包 → Astra 看图与几何测量 → 对象拆解和参数估计 → 编写 bpy 从空场景建模 → 输入相机渲染对照 → 独立审查与修订 → 导出冻结 → 独立 GT 评测”。四个方法均重新建模，包括 M1，统一输入 RGB 集合和预算。

方法定义采用 [Ooliva/world-lobby-exps-new](https://huggingface.co/spaces/Ooliva/world-lobby-exps-new) 的 M1–M4，并结合[深度计划](plan_depth.md)和四种方法的输入 packet。发布前重新核对远端版本并保存备份；凭据不得写入计划或发布产物。

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

## 3. 输入与准备工作

唯一会话：`../vio-reconstruction/sessions/lobby_orb_success_20260929T123153`，约 180 秒、4499 个原生 RGB 帧。共同有效源帧区间为 **245–4498**，共 4254 帧。

| 内容 | 计划使用的路径 |
|---|---|
| 建模采样 | `data/depth_samples/modeling_180.json`，180 帧 |
| 评测采样 | `data/depth_samples/eval_500.json`，500 帧，与建模集不重叠 |
| M2 位姿 | `frozen/vipe_default/camera.npz` |
| M3 位姿 | `../stable_orbit_orb_success_20260929/frozen/camera.npz` |
| M4 位姿 | 会话 `ground_truth/camera.csv`，只向 M4 提供 180 个采样相机 |
| 建模包 | `packets/M2/packet.json`、`packets/M3/packet.json`、`packets/M4/packet.json` |
| 建模深度 | `depth/m2_vipe|m3_orb|m4_gt/modeling_180/consolidated/` |
| M1 输入 | 待创建，只含相同 180 张 RGB、帧身份和公共标定 |
| Blender | `/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender`；执行前记录实际版本 |

公共原图为 1280×960，`fx=fy=762.8`、`cx=640`、`cy=480`，无畸变。深度反投影使用每份 NPZ 的处理后 `intrinsics`，不能对缩放后的深度直接套原图内参。

计划复用 DA3-GIANT 深度：4 视图、overlap=2、process resolution=392、`align_to_input_ext_scale=True`。重叠帧选择“最大窗口中心性，平局取较早窗口”。不为本轮建模重新推理；发现损坏时单独修复并记录新版本。

## 4. 任务隔离、工具与预算

四个方法分别在新的 **GPT-6 Astra** 会话中执行，记录实际模型标识。只提供本方法净化输入、无场景参数的公共工具、本轮建模契约和空输出目录。计划编写上下文已经接触发布和评测说明，不能直接作为声称未接触评测的建模作者；后续作者和审查者均使用新的方法专属上下文。

重写本轮 `modelling_contract.md`，不能照搬仍写着 OpenVINS / MapAnything 的旧约定。输入采用文件白名单，尽量实体复制到隔离目录，避免可遍历回完整数据树的软链接；M4 只给允许的采样相机矩阵，不开放整个 GT 目录。

作者禁止读取 GT 场景 / mesh / USD、GT depth、对象标签、评测图像和评分、500 集、GT 对齐轨迹、历史模型和场景专用参数、其他方法的结果。M4 的采样 GT 相机矩阵是明确例外。可以复用经检查的通用数学、网格、渲染与导出工具，不能复用旧场景尺寸、家具布局或材质赋值。

日志明确区分文件系统级隔离、工具访问记录与作者声明；环境不能强制隔离时披露限制，不能把访问声明当成完整审计。

| 每方法项目 | 统一上限或规则 |
|---|---|
| 完整场景版本 | 最多 5 版，含初版与修订 |
| RGB + 深度配对检查渲染 | 每版固定 10 个相机视角；每个视角同时输出 RGB 和 optical-Z 深度，二者合计一次配对检查。最多 5 版共 50 个配对视角，另保留最多 10 个有理由的局部补充视角；作者与审查者复用同一结果不重复计数 |
| 固定检查帧（修订协议） | 建模采样序号 33、61、74、82、91、100、108、118、129、155，四组使用同一帧身份 |
| 全量输入几何检查 | M2–M4 最多 3 次，每次 180 帧 BVH optical-Z 检查 |
| 独立审查 | 至少一次具体问题初审，并复审最终候选版本 |
| 超预算 | 停止修模，冻结并保留未解决项，标明质量限制 |

固定视角不是按帧序号等间隔选取。协调器以闭合 GT 相机中心轨迹的三维累计弧长和 180 帧联合可观测表面覆盖率选择建模采样序号 33、61、74、82、91、100、108、118、129、155，并将 RGB 副本、帧身份、哈希和选择审计放入 `fixed_check_views/`。GT 位姿和 GT 深度只允许协调器用于视角选择与覆盖审计，不把矩阵或深度放入作者检查视角包。

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

每个完整场景版本都在相同的 10 个固定相机视角执行一次 **RGB + 深度配对检查**：

1. 从当前 Blender 模型渲染 RGB，同时用同一相机、内参、分辨率、裁剪范围和几何版本渲染 optical-Z 深度。
2. RGB 与原始输入图对照，检查对象遗漏 / 重复、轮廓、遮挡、材质、光照、法线和穿插。
3. M2–M4 将模型深度与同视角 DA3 输入深度对齐到同一像素网格，生成深度并排图、绝对误差图、相对误差图、有效域 / 模型命中掩码和前景边界差异。
4. 结合 RGB 轮廓与深度残差定位误差来源：连续同号残差用于判断物体整体前后偏移；相对两侧边界的残差用于判断宽度、高度或厚度；遮挡边界错位用于判断对象间相对位置。只修改有多视角证据支持的对象尺寸、位置或朝向。
5. 修改后重建场景，并在同一组检查视角重新执行配对检查。不得通过逐帧移动相机、修改输入位姿、缩小有效域或仅删除高误差像素来改善结果。

每次配对检查至少保存逐视角 RGB 对照、模型深度、DA3 深度、误差可视化以及修改前后对象参数。汇总报告包含 AbsRel、RMSE、模型命中覆盖率、缺失惩罚和逐视角统计；同时记录每个尺寸 / 位置调整对应的视角、像素区域、深度残差和修改理由。视觉检查与深度检查属于同一次迭代，不等到冻结前才统一计算深度。

除上述逐版 10 视角检查外，M2–M4 在初版、主要修复后和冻结前各执行一次 180 帧全量 BVH optical-Z 检查。通过处理后内参采样 DA3 深度，且 BVH 沿射线距离必须转换为相机 Z；不能因模型未命中而缩小预先确定的输入有效域。

M1 没有输入深度：每次视觉检查仍输出模型 optical-Z，以检查模型自身的前后层次、遮挡和深度连续性，但不得与 M2–M4 的 DA3 深度一致性混称。M1 主要依据 RGB 对应、透视、轮廓、遮挡和相机覆盖率修订；深度定量指标记为 N/A。尽量保存 180 帧自身估计相机，对不可靠帧明确标记，不借其他方法相机补齐。

DA3 是建模输入而非 GT。深度残差只能用于提高模型对输入观测的一致性，不能表述为真实几何误差，也不能把逼近 DA3 当作逼近 GT 的证明。达到版本预算或修改在多视角间发生冲突时，停止修订并记录未解决项。

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

结果按下列口径组织；最终表号在发布前根据完整页面顺序统一编号。

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

- [ ] 历史工作流、深度计划与方法定义已核对并写入冻结协议。
- [ ] 180 / 500 采样身份互斥，RGB、几何、位姿、内参、单位和哈希检查通过。
- [ ] 四份方法专属净化输入完成，M1 不含外部位姿 / 深度，M2–M4 不含 GT 几何或评测结果。
- [ ] 四组分别完成 Astra 看图、对象清单、几何测量和从空场景语义建模。
- [ ] 每个模型版本均完成固定 10 视角 RGB + 深度配对检查；M2–M4 保存 DA3 深度误差图和指标，M1 深度定量项明确为 N/A。
- [ ] 所有物体尺寸、位置和朝向调整均能追溯到多视角 RGB / 深度证据，且未通过修改相机或有效域规避误差。
- [ ] M2–M4 按计划完成三次 180 帧全量输入深度检查，固定有效域、覆盖率和缺失惩罚均有记录。
- [ ] 完成独立初审、预算内修订和最终版本复审，保留全部遗留问题。
- [ ] 四套交付均可由所附程序生成，可加载、语义映射完整，并通过冻结哈希检查。
- [ ] 冻结后独立完成 180 / 500 模型评测，且评测结果没有反馈建模修订。
- [ ] 报告明确区分 Native depth、Model depth、Input consistency 和 RGB-only 检查。

交付标准是四组定义、输入、Astra 建模过程、语义模型、最终审查、冻结和独立评测均可追溯。仅有点云、融合网格或 Blender 包装文件不满足本计划的语义建模交付要求。


## 9. 本轮实际执行记录（覆盖旧执行记录）

本轮输出根目录为 `astra_blender2/`，保留上一轮 `astra_blender/`。
四组均使用新的 GPT-6 Astra 方法专属作者上下文，从本方法净化输入重新测量、语义建模；
独立初审与最终候选复审使用新的方法专属上下文。没有向作者提供 GT 评分。
输入实体复制，工具访问按方法限制并留记录；没有强制 OS 文件读取沙箱。

### 预算和审查

| 方法 | 完整版本 | 十视角配对检查累计 | 180帧输入BVH次数 | 最终独立复审 |
|---|---:|---:|---:|---|
| M1 | 2 | 20 | 0 | LIMITED |
| M2 | 3 | 30 | 3 | LIMITED |
| M3 | 3 | 30 | 3 | LIMITED |
| M4 | 2 | 20 | 3 | LIMITED |

固定检查样本33、61、74、82、91、100、108、118、129、155；每版保存RGB/模型深度，
M2–M4同时保存自身DA3深度、绝对/相对/有符号残差、有效域和边界对照。
M1仅有模型自身深度，不与DA3一致性混称。

- M1：最终质量与独立审查 `LIMITED`；场景 SHA256 `747b24362a5c0a2d71d24499a0e82cdc8a1f4595fc9e724a7da5c0d192708f63`。
- M2：最终质量与独立审查 `LIMITED`；场景 SHA256 `8f80d6299b98743be2151788827528ed8c4fa714ca8490f9797b52cc2c24177a`。
- M3：最终质量与独立审查 `LIMITED`；场景 SHA256 `5e6e6e373472762e0f96efecf4fa5a8912a3b4657cb1061842e0c34288bad15e`。
- M4：最终质量与独立审查 `LIMITED`；场景 SHA256 `a86c6656bfd7f3ff1435c037a48aecb1d503047b799d75c9fc5524baba5c5ec5`。

### Table 9/10/11

Table9双向表面距离单位米；Table10固定评测视角0/36/72/108/144，PSNR/SSIM/LPIPS；
Table11为20个同轨迹确定性扰动相机的光轴Z深度误差。十视角用于建模修订，五视角用于既定冻结后外观评分。

| 方法 | Model→GT(m) | ObservedGT→model(m) | PSNR(dB) | SSIM | LPIPS | 扰动视角AbsRel | RMSE(m) |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| M2 | 0.1547 | 0.1490 | 12.7912 | 0.3703 | 0.5409 | 8.25% | 1.1009 |
| M3 | 0.2304 | 0.1841 | 11.7982 | 0.3833 | 0.5511 | 8.99% | 1.2060 |
| M4 | 0.1998 | 0.1262 | 12.9371 | 0.3611 | 0.4849 | 6.13% | 0.9538 |

M1只在冻结RGB估计相机满足配准条件时进行GT相机辅助Sim(3)诊断，否则N/A；
M2/M3用180建模相机拟合一次SE(3)，scale1，M4按输入坐标关系。
GT来源是此前重新生成并验证的680视角GT。原目录已迁移，本轮使用HF快照中与原生成清单哈希完全一致的副本`astra_blender2/evaluation/gt_reference/`，来源及核验见`provenance/gt_reference_relocation.json`；
Table11扰动视角GT从原始USD本轮重新求交。没有使用旧legacy GT缓存。

### 本地交付和发布边界

- 新模型、脚本、参数、测量、配对图与审查：`astra_blender2/models/M1..M4/`。
- 全部冻结文件SHA256：各方法`freeze_manifest.json`与`SHA256SUMS`。
- 180/500模型深度：`astra_blender2/evaluation/depth/summary.json`。
- Table9/11：`astra_blender2/evaluation/blog_tables_456/tables_4_6.json`。
- Table10及逐视角CSV：同目录`table5_appearance.json`和CSV。
- 已观察到的CLI调用/token与工具统计：`astra_blender2/provenance/usage_accounting.json`；明确披露未获得的collaboration作者用量。
- HF本轮仅发布原Table9/10/11对应指标和相关数值/来源记录。发布前远端已重排为Table3/4/5，本轮保留最新编号并标注原表号。网页其他表格、三维模型、模型下载与渲染图仍属于此前轮次；没有上传新模型或新渲染图。
- HF完成提交与远端哈希验证记录：`astra_blender2/provenance/hf_upload.json`。

质量状态和未解决问题随结果保留。本轮为一次工程实验，不表述为重复建模方差或跨场景泛化。
