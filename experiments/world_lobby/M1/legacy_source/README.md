# Astra 纯视觉大堂重建

输入仅为指定目录中的 180 张 RGB PNG。由 GPT-6 Astra 观察代表性画面后，通过 Blender 5.2 Python API 从空场景创建几何和程序化材质。

未读取深度、相机真值或估计位姿、IMU、点云、原始场景或既有模型；未运行 SfM / SLAM / 深度预测。用户追加的真值评估在模型冻结之后单独执行，评估不会回写模型。

- `scene.blend`：可编辑 Blender 工程（纹理已打包）。
- `scene.glb`：含纹理的网页模型。
- `renders/`：四个 Cycles 渲染视角。
- `manual_cameras.json`：四个手工构图相机，与参考帧的近似关联。并非 180 帧估计轨迹。
- `scripts/build_scene.py`、`scripts/make_materials.py`：从零复现建模。
- `scripts/final_camera.py`：固定手工视角和参考帧关联。
- `site/`：独立交互网站。
- `freeze_manifest.json`：读取真值前固定的文件哈希。
- `evaluation/`：冻结后的真值评估。

所有尺寸均是视觉推断的近似设计单位；不可当作现场测量。场景遮挡和未见部分（尤其近端封闭墙）包含补全。重点复现大厅布局、物体类别、形状及材质感受，不保证摄影测量精度。

复现：

```bash
python scripts/make_materials.py
blender -b --factory-startup --python scripts/build_scene.py
blender -b scene.blend --python scripts/final_camera.py
blender -b scene.blend --python scripts/render_views.py
```

发布目标：`https://ooliva-world-lobby-vio-60s.hf.space/visual-recon/`。

## 后续新增：纯 RGB 180 帧相机求解

用户后续要求为本次 visual-recon 新增相机求解。此阶段在模型冻结后独立运行 RGB-only COLMAP SfM 与共享焦距自标定，未使用旧 SfM+IMU 位姿、IMU、深度、外部标定或四个展示相机。180/180 帧均直接登记，原 Blender 模型不变。

- 新轨迹：`camera_rgb180/solve_v1/camera_rgb180_native.tum`（原生任意尺度）。
- 新评估：`evaluation/rgb180/results.md`；CSV/JSON/PNG/PDF 位于同目录。
- Sim3 ATE RMSE：1.160309 m；姿态 RMSE：12.649238°。
- SE3 ATE RMSE：1.606435，采用任意原生单位按 1 米计算的约定，不能解读为真实公制尺度恢复。
- 帧 102、108、120 为严重离群位姿，均保留在全 180 帧统计中。
- 当前 HF 主指标已更新为此新 RGB 轨迹。原几何评估及四视角记录在 `site/evaluation/visual_model/`。
