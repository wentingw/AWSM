# M3 OpenVINS 360 s experiment

运行日期：2026-09-23（Asia/Hong_Kong）。本实验使用 World Lobby 的完整 RGB+IMU 输入，复制旧诊断中唯一验证过的 `max_clones: 31` 配置到本目录；未读取 ground truth 参与估计，未修改旧代码、旧运行或环境。

## 运行合同

- RGB 输入：8999 张、25 Hz；IMU：89999 个、250 Hz。
- 配置：`config_window31.yaml`，`max_clones=31`，原标定与噪声配置；哈希见 `FREEZE_MANIFEST.json`。
- 运行方式：`run_openvins.py ... --rate 1.0 --ros-domain-id 73`，OpenVINS 使用已安装的 `ov_jazzy_min` / `ov_msckf`，CPU 运行。
- ROS 日志：`ros_logs/`；估计输出：`output/`。
- OpenVINS 估计完成后才运行 `src/pose/evaluate_openvins.py` 读取 GT。

## 实际覆盖

OpenVINS 输出 `output/pose_cam.tum` 共 87,585 个原始 odometry 样本，时间覆盖约 351.356 s；首个输出相对录制真值起点约 8.600 s，覆盖到 359.956 s。与真值时间范围重叠的 raw 样本为 87,576。回放日志报告 `image_errors=0`。

将 raw odometry 以位置线性插值和四元数 SLERP 对齐到原始图像时间戳后，覆盖 8,784/8,999 张图像（97.6108%）。因此从采样序号 `0,50,...,8950` 请求的 180 帧中，只有 175 帧有有效 OpenVINS pose；`openvins_camera_pose_180.tum` 明确只写入这 175 帧，不填充虚假 pose。完整图像时间对齐结果在 `openvins_camera_pose_images.tum`。

## GT 评测结果

冻结后、使用首个可用相机 pose 的刚体旋转和平移对齐（与旧诊断相同口径）得到：位置 RMSE **3.196583 m**，中位数 0.820924 m，最大值 7.512755 m；姿态 RMSE **0.334220°**，中位数 0.290600°，最大值 0.728860°。60 s 位置误差为 0.010236 m、姿态误差 0.289931°；之后长期漂移，180 s 位置误差达到 6.791027 m。

这些结果证明 `max_clones=31` 在前 60 s 的改善可以复现，但没有把完整 360 s 变成稳定 metric trajectory。它不能直接作为完整 M3 建模输入；MapAnything 若要使用此结果，必须保留缺失帧、插值范围和漂移边界，并单独报告。

详见 `evaluation.json`。`FREEZE_MANIFEST.json` 保存冻结时的关键输出哈希；原始估计和插值产品分开保存，避免把插值 pose 误报成 OpenVINS 直接估计。
