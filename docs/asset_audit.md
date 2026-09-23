# World-model blog asset audit

审计时间：2026-09-22 16:40（Asia/Hong_Kong）。本文只记录可在本机读取到的证据路径，不复制大文件、不启动实验，也不把旧目录改造成新版本。主项目为 `/home/hchen/Documents/astraBlenderTest`；详细机器可读清单见 `../manifests/legacy_assets.json`。

## 可作为同一套定量实验的数据

World Lobby 的主采集是 `vio-reconstruction/sessions/stable_orbit_20260921T044401`：360 s、8999 RGB 帧、89999 个 250 Hz IMU 样本；180 张关键帧在 `runs/stable_orbit_20260921T044401/keyframes_180/images/`。视频、原始图像、IMU、标定和 `ground_truth/camera_tum.txt` 都存在。真值只应在冻结模型之后用于评估。

纯视觉方法一的冻结目录是 [`visual-recon`](/home/hchen/Documents/astraBlenderTest/visual-recon)。其 README 和 freeze manifest 明确写明：Astra 只观察 180 张 RGB，未读取深度、位姿、IMU、点云、原场景或旧模型；输出 `scene.blend`、`scene.glb` 和四个手工视角渲染。尺寸是视觉推断设计单位，不能直接进入米制误差表。模型冻结后，目录又独立生成了 `camera_rgb180/solve_v1/camera_rgb180_native.tum`：180/180 帧 COLMAP 注册，Sim3 ATE 1.160309 m、旋转 12.649238°（见 `DELIVERY.json` 和 `checks/rgb180_numerical.json`）。这条轨迹是后验评估产物，不是 Astra 输出，也不是模型建图输入；因此不能据此声称 M1 已有可用于主表的 180 帧相机解。

方法二的 ViPE 原生推理确实存在：`runs/stable_orbit_20260921T044401/vipe_rgb_180_20260922/camera.npz` 和 `depth/`，结果记录于 `VIPE_EVALUATION_20260922.md`。它只处理约每 2 秒采样的 180 张 RGB，采用 no_vda 与 UniDepth-small 的近米制 learned prior，不能写成“全视频每帧 ViPE”。报告给出位姿 ATE 19.23 cm、旋转 0.3379°、深度 MAE 56.00 cm、RMSE 101.11 cm、AbsRel 7.78%。但 [`MODEL_REPRODUCTION_20260922.md`](/home/hchen/Documents/astraBlenderTest/vio-reconstruction/runs/stable_orbit_20260921T044401/MODEL_REPRODUCTION_20260922.md) 明确写明：模型的测量复用 SfM+IMU 与 MapAnything；对应模型路径为 `modelling/reproduction_20260922/final/scene.blend`。所以该模型不能直接当作“纯 ViPE pose/depth + Astra”模型，必须重建后才可用于方法二的模型误差。

方法三所需的 MapAnything 180 帧深度目录存在于 `depth_windows8/`，对应的已接受建模链路位于 `accepted_estimate/metric_camera.tum` → `depth_windows8` → `modelling/draft_v5/scene.blend`。关键边界是：OpenVINS 全程输出已被拒绝，`evaluation/openvins_rejected.json` 显示 ATE 2153.165 m、旋转 179.193°；draft_v5 实际采用的是 SfM + IMU 定尺度轨迹。因此它可作为“现有成功链路”展示，但不能诚实标成 OpenVINS 结果。另有修正版诊断 `evaluation/openvins_diagnosis_20260922/window31_first62s`：只把 `max_clones` 从 11 改为 31，在 60 s 位置误差 0.010511 m、姿态 0.290891°；README 明确说只覆盖前 62 s，未验证完整 360 s，不能升级为已完成方法三。

方法四（GT camera pose + MapAnything + Astra）尚未发现完成产物。GT pose 和同一 RGB/IMU 采集已存在，MapAnything checkout 在 `/home/hchen/Documents/map-anything`，但需要单独运行、记录输入哈希、输出 metric depth、建模和评估。

## 位姿基线的可信边界

`batch_vio_20260922/README.md` 记录了一个新的全程联合视觉惯性估计：360 keyframes，位置 ATE 0.342311 m、姿态 RMSE 0.052007°。这是比旧 SfM+IMU 的 0.366447 m / 0.081914° 更好的位姿候选，但只完成了 MapAnything dry-run 输入同步检查；没有基于该轨迹重跑深度或 Blender 模型。不要把它和已有模型误差拼成完整方法三结果。

稳定成功模型的真实来源与报告在 `results_sfm_imuscale.md` 和 `RESULTS.json`：SfM 任意尺度 → 原始 IMU 尺度恢复 → MapAnything → Astra。报告给出模型独立验收 `metric_consistency=QUALIFIED`、`appearance=PARTIAL`、`completeness=PARTIAL`，并明确尺度约有 10% 不确定性。量化表应把位姿误差、深度误差、模型表面误差分开，同时标出是否使用真值、是否尺度拟合。

## 仿真与下游资产

World Lobby 的 Isaac/Web 仿真资产存在：`drone-web/scenes/world_lobby/Collected_World_Lobby/World_Lobby.usd`；可部署控制与参考视图在 `/home/hchen/Documents/drone-downloads/home_drone_deploy_20260914`。已有稳定相机录制脚本、FPV/场景截图和视频，足以支持无人机重拍任务的实验准备。现有审计没有找到完成的“目标图搜索并重拍”结果，也没有找到 Unitree G1 模型或语言导航运行记录；G1 下游任务仍是待补实验，不能在 blog 中写成已完成。

## 必须排除的旧资产

`reconstruction/`、`IMG_0755.mp4`、`office_cafe_reconstruction.blend` 与 `.publish/office-cafe-*` 是另一条 office-cafe/IMG_0755 轨迹，虽然包含 ViPE、扫描、Blender、碰撞和网页产物，但不是 World Lobby 360 s 数据。它们可作工程参考，不能进入本次六项比较表，也不能与 World Lobby 的 M1/M2/M3/M4 混画。

## 结论

现阶段可立即写入 blog 的强证据是：同一 World Lobby 视频/关键帧的 M1 纯 RGB Astra 模型、ViPE 原生 pose/depth 指标、SfM+IMU+MapAnything+Astra 成功模型、GT 轨迹及仿真模型资产。定量比较应明确为六项：M1、M2、M3、M4、ViPE native、MapAnything native；其中 M3/M4 模型结果仍待完成，OpenVINS 62 s 修正版只能作为诊断。batch VIO 仅完成 pose 评估；M2 的现有模型 provenance 不纯。下一步应先固定 180 个时间对齐视角和统一 metric frame，再补跑 M4，并重建 provenance 纯净的 M2/M3 模型后制作 5×4 图、轨迹图和六项表格。
