# World Lobby: four trajectories and Astra/Blender reconstruction

This directory preserves the code from `world_lobby_four_trajectory_20260929`, including both saved Blender modelling runs. It is separate from the earlier `experiments/world_lobby/` experiment already in SceneWeft.

## 本次上传内容

| 路径 | 内容 |
| --- | --- |
| `code/` | 轨迹冻结与对比、180/500 采样、DA3 推理与输入包、GT 深度生成、指标与 HF 页面构建 |
| `astra_blender/models/M1..M4/` | 前一轮建模源码及小型参数、相机、语义与测量记录 |
| `astra_blender2/models/M1..M4/` | 固定十视角新版建模源码、参数、修订和独立审查代码 |
| `astra_blender2/tools/` | 净化输入、配对检查、重建验证、冻结、GT 评测及发布工具 |
| `astra_blender2/configs/` | 方法输入权限、固定视角、预算与评测协议 |
| `data/depth_samples/`, `packets/`, `astra_blender2/inputs/` | 小型采样清单和输入包元数据；图像与深度数组另行获取 |
| `fixed_check_views/` | 固定视角说明和选择清单；包含协调器选择审计，应遵守原建模输入隔离协议 |
| `publication/huggingface/space/`, `astra_blender2/report/space/` | 保存的网页 HTML/CSS/JS 源码；完整网站还需要外部媒体和模型资产 |
| `plan_*.md`, `COMMANDS.md` | 原计划、执行记录和历史运行命令 |
| `source_snapshot.json` | 本次逐文件来源、大小和 SHA256 |

原代码和参数按字节保存。日志、重复版本目录、原始 RGB、稠密深度、GT mesh/USD、模型二进制、渲染图、模型权重和运行环境未纳入此代码快照。`analysis/model_from_input.npy` 是前一轮 M3 的 256 字节坐标变换参数，作为构建依赖保留。

## Methods and evaluation

For this experiment, M1 is RGB-only with known common intrinsics; M2 uses ViPE native poses with pose-conditioned DA3; M3 uses ORB-SLAM3 native poses with DA3; M4 uses the permitted sampled GT poses with DA3. OpenVINS is part of the trajectory comparison, and is not the M1 or M3 modelling method here. These definitions differ from the earlier OpenVINS/MapAnything experiment in the repository.

The new run checks samples **33, 61, 74, 82, 91, 100, 108, 118, 129, 155**. Its modelling versions are M1/M2/M3/M4 = 2/3/3/2, with 20/30/30/20 paired checks. M2–M4 each completed three full 180-frame input checks. All four final reviews were `LIMITED`, with no unresolved technical/protocol blockers at freezing. M1 lacks reliable frozen RGB-only camera correspondences and was marked N/A in this run's independent GT evaluation.

Results: <https://huggingface.co/spaces/Ooliva/world-lobby-exps-new>. Original requested Tables 9/10/11 correspond to the page's renumbered Tables 3/4/5. See the preserved plans and evaluator code for the exact protocols. A code snapshot is not a replacement for a model/metric release, and later webpage changes may use different display numbering or diagnostic registrations.

## Verify this checkout

From the SceneWeft repository root:

```bash
python scripts/verify_source_snapshot.py
python -m pip install -r requirements-core.txt
python scripts/check_world_lobby_depth_math.py
```

The second command uses the existing core NumPy/SciPy requirements. Optional pipeline dependencies are listed in [`requirements-analysis.txt`](requirements-analysis.txt). Blender has its own Python runtime; DA3/ViPE, CUDA, LPIPS weights, and estimator environments must be provisioned separately. The commands above do not rerun inference or GT scoring.

## Rebuild a saved new scene program

The latest four builders can reconstruct geometry from the included layout, camera and measurement companions, without downloading RGB or predicted depth. Use Blender 5.2.0 and a fresh output directory:

```bash
python scripts/rebuild_world_lobby_scene.py \
  --method M4 --blender /path/to/blender \
  --output /tmp/sceneweft-world-lobby-M4
```

The helper copies the program and its small companions to the output directory, creates the required output folders, and runs Blender without rendering. It does not modify this source snapshot or re-execute Astra reasoning. Byte-identical `.blend` files are not expected after resaving. This helper targets `astra_blender2`; the earlier builders can require archived input packets and historical paths.

## Full pipeline and external assets

Historical commands and JSON metadata retain absolute `/home/hchen/...` paths. To rerun the full capture/estimator/evaluation pipeline, work in a new copy and relocate paths consistently. Several `code/` tools expect the experiment directory beside `vio-reconstruction/`, `stable_orbit_orb_success_20260929/`, `world_model_blog/`, `reconstruction/`, and `drone-web/`, rather than nested inside SceneWeft's `experiments/` directory. The source capture is `lobby_orb_success_20260929T123153`; original asset identities are recorded in `contract.json`.

Obtain the exact capture, native pose solutions, DA3 weights/depths, GT scene and verified fresh GT cache before using the corresponding stages. Review the source plans and input permissions; only after all candidate models freeze should independent GT evaluation begin. Do not run historical tools directly over frozen output directories. Publication tools write to external services when invoked; the GitHub upload does not invoke them.

The saved `astra_blender2/README.md` and plans describe the original complete working directory. Their references to omitted binaries, images, logs and evaluation outputs intentionally remain historical references. Third-party assets and upstream code retain their existing attribution and licensing; this snapshot introduces no new license.
