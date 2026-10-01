# Changelog

Release history for **AWSM — Agentic World Simulation and Mapping**.

## v0.1 — 2026-10-01

### Initial reconstruction release

- Published the [AWSM research blog](https://phygital-ai.github.io/agentic-world-simulation-and-mapping/), introducing geometry-grounded agentic scene reconstruction.
- Released the M1–M4 reconstruction implementations: RGB-only, ViPE + DA3, ORB-SLAM3 + DA3, and GT-pose-conditioned DA3.
- Included saved Blender scene builders, reconstruction evaluation tools, and [reproduction guidance](docs/AWSM_REPRODUCTION.md).
- Documented experiment provenance and the distinction between rebuilding saved scenes and rerunning the full pipeline.

**Scope:** reconstruction code and reproduction guidance. Embodied demo code, robot control, and task execution are deferred to a future release. External data, weights, and runtime dependencies remain subject to the reproduction guide's requirements.

### 中文摘要

2026 年 10 月 1 日发布 AWSM 研究博客与 v0.1 重建代码，包含四条重建路线、Blender 场景构建程序、评测工具与复现说明。本版聚焦重建；具身 demo、机器人控制与任务执行代码留待后续版本完善后发布。
