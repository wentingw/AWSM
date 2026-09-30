#!/usr/bin/env python3
"""Build the private static Space and Dataset release bundles."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "world_lobby_four_trajectory_20260929"
EVAL = BASE / "evaluation"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
ORB = ROOT / "stable_orbit_orb_success_20260929/frozen"
RELEASE = BASE / "publication/huggingface"
SPACE = RELEASE / "space"
DATASET = RELEASE / "dataset"
DATASET_URL = "https://huggingface.co/datasets/Ooliva/world-lobby-exps-new"
DEPTH_EVAL = BASE / "evaluation/depth"
DEPTH_METHODS = {
    "M2": "m2_vipe",
    "M3": "m3_orb",
    "M4": "m4_gt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def moving_average(values: np.ndarray, width: int = 25) -> np.ndarray:
    if width <= 1:
        return values
    kernel = np.ones(width, dtype=float) / width
    pad = width // 2
    padded = np.pad(values, (pad, width - 1 - pad), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def load_errors() -> dict[str, dict[str, np.ndarray]]:
    grouped: dict[str, dict[str, list[float]]] = {}
    with (EVAL / "per_frame_errors.csv").open() as handle:
        for row in csv.DictReader(handle):
            method = row["method"]
            value = grouped.setdefault(
                method, {"elapsed_s": [], "translation_error_m": [], "rotation_error_deg": []}
            )
            for key in value:
                value[key].append(float(row[key]))
    return {
        method: {key: np.asarray(values) for key, values in fields.items()}
        for method, fields in grouped.items()
    }


def build_figure14() -> None:
    arrays = np.load(EVAL / "aligned_common_trajectories.npz")
    errors = load_errors()
    names = ["ORB-SLAM3", "ViPE default", "OpenVINS"]
    position_keys = {
        "GT": "gt_position",
        "ORB-SLAM3": "orb_slam3_position",
        "ViPE default": "vipe_default_position",
        "OpenVINS": "openvins_position",
    }
    colors = {
        "GT": "#111827",
        "ORB-SLAM3": "#d97706",
        "ViPE default": "#2563eb",
        "OpenVINS": "#dc2626",
    }
    styles = {"GT": "-", "ORB-SLAM3": "-", "ViPE default": "--", "OpenVINS": "-."}

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10})
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), constrained_layout=True)

    ax = axes[0]
    for name, key in position_keys.items():
        p = arrays[key]
        ax.plot(p[:, 0], p[:, 1], styles[name], color=colors[name], lw=1.7, label=name)
    ax.set_title("(a) Camera trajectories · XY projection")
    ax.set_xlabel("World x (m)")
    ax.set_ylabel("World y (m)")
    ax.axis("equal")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1]
    for name in names:
        item = errors[name]
        ax.plot(
            item["elapsed_s"],
            moving_average(item["translation_error_m"]),
            color=colors[name],
            lw=1.5,
            label=name,
        )
    ax.set_title("(b) Translation error · 1 s moving average")
    ax.set_xlabel("Time since common interval start (s)")
    ax.set_ylabel("Translation error (m)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[2]
    for name in names:
        item = errors[name]
        ax.plot(
            item["elapsed_s"],
            moving_average(item["rotation_error_deg"]),
            color=colors[name],
            lw=1.5,
            label=name,
        )
    ax.set_title("(c) Rotation error · 1 s moving average")
    ax.set_xlabel("Time since common interval start (s)")
    ax.set_ylabel("Rotation error (degrees)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle(
        "Figure 14. World Lobby pose comparison · 4,254 exact common frames · one global SE(3), scale=1",
        fontsize=13,
    )
    for extension in ("png", "pdf"):
        fig.savefig(SPACE / f"assets/figure14_abc.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)

    titles = {
        "a": "(a) Camera trajectories · XY projection",
        "b": "(b) Translation error · 1 s moving average",
        "c": "(c) Rotation error · 1 s moving average",
    }
    for label in ("a", "b", "c"):
        fig, ax = plt.subplots(figsize=(8.4, 5.6), constrained_layout=True)
        if label == "a":
            for name, key in position_keys.items():
                p = arrays[key]
                ax.plot(p[:, 0], p[:, 1], styles[name], color=colors[name], lw=1.8, label=name)
            ax.set_xlabel("World x (m)")
            ax.set_ylabel("World y (m)")
            ax.axis("equal")
        else:
            field = "translation_error_m" if label == "b" else "rotation_error_deg"
            unit = "m" if label == "b" else "degrees"
            for name in names:
                item = errors[name]
                ax.plot(
                    item["elapsed_s"],
                    moving_average(item[field]),
                    color=colors[name],
                    lw=1.6,
                    label=name,
                )
            ax.set_xlabel("Time since common interval start (s)")
            ax.set_ylabel(f"{'Translation' if label == 'b' else 'Rotation'} error ({unit})")
        ax.set_title(titles[label])
        ax.grid(alpha=0.25)
        ax.legend()
        fig.savefig(SPACE / f"assets/figure14{label}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def load_depth_reports() -> dict[str, dict]:
    return {
        split: json.loads((DEPTH_EVAL / f"metrics/{split}/metrics.json").read_text())
        for split in ("modeling_180", "eval_500")
    }


def depth_values(reports: dict[str, dict], split: str, method: str) -> dict[str, float]:
    report = reports[split]["methods"][method]
    primary = report["primary_no_scale_fit"]
    return {
        **primary,
        "median_frame_absrel": float(
            np.median(
                [
                    frame["absrel"]
                    for frame in report["per_frame"]
                    if frame["absrel"] is not None
                ]
            )
        ),
    }


def build_space(metrics: dict, depth_reports: dict[str, dict]) -> None:
    reset_dir(SPACE)
    (SPACE / "assets").mkdir()
    build_figure14()

    orb = metrics["methods"]["ORB-SLAM3"]["se3"]
    vipe = metrics["methods"]["ViPE default"]["se3"]
    modeling = {
        method: depth_values(depth_reports, "modeling_180", method)
        for method in DEPTH_METHODS
    }
    novel = {
        method: depth_values(depth_reports, "eval_500", method)
        for method in DEPTH_METHODS
    }
    readme = """---
title: World Lobby Experiments New
emoji: 📐
colorFrom: gray
colorTo: blue
sdk: static
app_file: index.html
pinned: false
short_description: Private World Lobby pose comparison and evidence
---

# World Lobby experiments · new 180 s capture

Private static report for the frozen World Lobby trajectory comparison.
Machine-readable artifacts are stored in the matching private Dataset:
`Ooliva/world-lobby-exps-new`.
"""
    (SPACE / "README.md").write_text(readme)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="World Lobby 新 180 秒序列位姿对比">
  <title>World Lobby · 新序列几何链路对比</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
<header>
  <p class="eyebrow">WORLD LOBBY / FROZEN POSE EVALUATION / 2026-09-29</p>
  <h1>从视频与 IMU 到可编辑世界</h1>
  <p class="lede">新 180 秒轨迹上的 GT、ORB-SLAM3、ViPE default 与 OpenVINS 对比。
  位姿输出先冻结，之后才读取 GT；所有主指标使用 4,254 个严格共同时间戳。</p>
  <nav><a href="#methods">方法</a><a href="#metrics">位姿与深度</a><a href="#native-novel">非建模视角</a><a href="#figure14">Figure 14</a><a href="#model-novel">模型评测状态</a><a href="#evidence">证据</a></nav>
</header>
<main>
  <section class="notice">
    <strong>发布范围：</strong>M2–M4 的 pose-conditioned DA3-GIANT 原生深度已在同一 180 张建模帧和互斥的 500 张非建模帧上完成。
    新的 M1–M4 Astra/Blender 场景尚未生成，因此所有“Model depth”与模型输入一致性指标明确保留为“待建模”，不以 DA3 原生深度代填。
  </section>

  <section id="methods">
    <p class="eyebrow">01 / PIPELINES</p>
    <h2>Table 1. M1–M4 方法与输入信息</h2>
    <div class="scroll"><table>
      <thead><tr><th>方法</th><th>位姿来源</th><th>下游深度与建模</th><th>本次状态</th></tr></thead>
      <tbody>
        <tr><th>M1 · 纯视觉 + Astra</th><td>无原生米制轨迹</td><td>RGB → Astra / Blender</td><td>方法定义；本次未建模</td></tr>
        <tr><th>M2 · ViPE + DAV3 + Astra</th><td>ViPE default，RGB-only</td><td>DA3-GIANT（ViPE pose-conditioned）→ Astra / Blender</td><td>位姿与 DA3 已完成；Blender 待运行</td></tr>
        <tr><th>M3 · ORB-SLAM3 + DAV3 + Astra</th><td>ORB-SLAM3 monocular-inertial</td><td>DA3-GIANT（ORB-SLAM3 pose-conditioned）→ Astra / Blender</td><td>位姿与 DA3 已完成；Blender 待运行</td></tr>
        <tr><th>M4 · GT pose + DAV3 + Astra</th><td>仿真 GT camera pose</td><td>DA3-GIANT（GT pose-conditioned）→ Astra / Blender</td><td>GT 位姿条件与 DA3 已完成；Blender 待运行</td></tr>
      </tbody>
    </table></div>
  </section>

  <section id="metrics">
    <p class="eyebrow">02 / POSE METRICS</p>
    <h2>Table 2. M1–M4 位姿与深度指标</h2>
    <p>位姿使用一次全局刚性 SE(3) 对齐、scale=1；M2/M3 使用 4,254 个严格共同时间戳。Native depth 使用 180 张建模帧上的 DA3 optical-Z 与独立 GT optical-Z 直接比较，不做尺度拟合。</p>
    <div class="scroll"><table>
      <thead><tr><th>方法</th><th>ATE (m) ↓</th><th>Rotation (°) ↓</th><th>Native depth AbsRel ↓</th><th>Model depth AbsRel ↓</th></tr></thead>
      <tbody>
        <tr><th>M1 · 纯视觉 + Astra</th><td>—</td><td>—</td><td>—</td><td class="pending">待建模</td></tr>
        <tr><th>M2 · ViPE + DAV3 + Astra</th><td>{vipe["translation_m"]["rmse"]:.4f}</td><td>{vipe["rotation_deg"]["rmse"]:.4f}</td><td>{modeling["M2"]["absrel"]:.2%}</td><td class="pending">待建模</td></tr>
        <tr><th>M3 · ORB-SLAM3 + DAV3 + Astra</th><td>{orb["translation_m"]["rmse"]:.4f}</td><td>{orb["rotation_deg"]["rmse"]:.4f}</td><td>{modeling["M3"]["absrel"]:.2%}</td><td class="pending">待建模</td></tr>
        <tr><th>M4 · GT pose + DAV3 + Astra</th><td>GT 输入</td><td>GT 输入</td><td>{modeling["M4"]["absrel"]:.2%}</td><td class="pending">待建模</td></tr>
      </tbody>
    </table></div>
    <p><strong>Native depth AbsRel</strong>：DA3 直接输出与 GT 深度在有效 GT 像素上的平均相对绝对误差
    <code>mean(|D_DA3−D_GT| / D_GT)</code>，衡量建模器收到的深度本身是否准确。
    <strong>Model depth AbsRel</strong>：从冻结 Blender 场景按统一 GT 相机射线求交得到的模型深度与 GT 深度的同一误差，衡量最终模型几何；它不能由 Native depth 推导。</p>
  </section>

  <section id="native-novel">
    <p class="eyebrow">03 / HELD-OUT NATIVE DEPTH</p>
    <h2>Table 3. 同一场景非建模视角的原生 DA3 深度误差</h2>
    <p>500 张图像与 180 张建模帧严格互斥；这是 DA3 深度泛化评测，不是 Blender 模型的新视角评测。M1 没有原生深度，因此不适用。</p>
    <div class="scroll"><table>
      <thead><tr><th>方法</th><th>RMSE (m) ↓</th><th>整体 AbsRel ↓</th><th>逐帧 AbsRel 中位数 ↓</th><th>有效覆盖率 ↑</th><th>缺失惩罚 MAE (m) ↓</th></tr></thead>
      <tbody>
        <tr><th>M1 · 纯视觉 + Astra</th><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>
        <tr><th>M2 · ViPE + DAV3 + Astra</th><td>{novel["M2"]["rmse_m"]:.4f}</td><td>{novel["M2"]["absrel"]:.2%}</td><td>{novel["M2"]["median_frame_absrel"]:.2%}</td><td>{novel["M2"]["valid_coverage"]:.2%}</td><td>{novel["M2"]["missing_penalty_mae_m"]:.4f}</td></tr>
        <tr><th>M3 · ORB-SLAM3 + DAV3 + Astra</th><td>{novel["M3"]["rmse_m"]:.4f}</td><td>{novel["M3"]["absrel"]:.2%}</td><td>{novel["M3"]["median_frame_absrel"]:.2%}</td><td>{novel["M3"]["valid_coverage"]:.2%}</td><td>{novel["M3"]["missing_penalty_mae_m"]:.4f}</td></tr>
        <tr><th>M4 · GT pose + DAV3 + Astra</th><td>{novel["M4"]["rmse_m"]:.4f}</td><td>{novel["M4"]["absrel"]:.2%}</td><td>{novel["M4"]["median_frame_absrel"]:.2%}</td><td>{novel["M4"]["valid_coverage"]:.2%}</td><td>{novel["M4"]["missing_penalty_mae_m"]:.4f}</td></tr>
      </tbody>
    </table></div>
  </section>

  <section id="figure14">
    <p class="eyebrow">04 / TRAJECTORY DIAGNOSTICS</p>
    <h2>Figure 14. 轨迹、平移误差与旋转误差</h2>
    <figure><a href="assets/figure14a.png"><img src="assets/figure14a.png" alt="Figure 14a 相机轨迹"></a>
      <figcaption>Figure 14(a). GT、ORB-SLAM3、ViPE default 与 OpenVINS 的 XY 轨迹；每个估计器一次 SE(3) 对齐。</figcaption></figure>
    <div class="figure-grid">
      <figure><a href="assets/figure14b.png"><img src="assets/figure14b.png" alt="Figure 14b 平移误差"></a>
        <figcaption>Figure 14(b). 平移误差；曲线为 1 秒移动平均，表中 RMSE 使用全部原始逐帧误差。</figcaption></figure>
      <figure><a href="assets/figure14c.png"><img src="assets/figure14c.png" alt="Figure 14c 旋转误差"></a>
        <figcaption>Figure 14(c). 旋转误差；曲线为 1 秒移动平均，表中 RMSE 使用全部原始逐帧误差。</figcaption></figure>
    </div>
    <p class="caption-note">OpenVINS 保留在 Figure 14 作为“以上四轨迹对比”的诊断曲线，但按要求不加入仅保留 M1–M4 的 Table 2。</p>
  </section>

  <section id="model-novel">
    <p class="eyebrow">05 / MODEL-DEPENDENT EVALUATION</p>
    <h2>Table 4. 同一场景新视角的模型深度误差</h2>
    <div class="notice"><strong>状态：待建模。</strong>该表要求从 M1–M4 冻结 Blender 网格在统一新视角下射线求交。当前只有 DA3 原生深度，不能科学地代替模型深度。</div>
    <div class="scroll"><table>
      <thead><tr><th>方法</th><th>Novel depth AbsRel ↓</th><th>RMSE (m) ↓</th><th>Coverage ↑</th><th>Penalized MAE (m) ↓</th></tr></thead>
      <tbody>
        <tr><th>M1 · 纯视觉 + Astra</th><td colspan="4" class="pending">待 M1 Blender 模型冻结</td></tr>
        <tr><th>M2 · ViPE + DAV3 + Astra</th><td colspan="4" class="pending">待 M2 Blender 模型冻结</td></tr>
        <tr><th>M3 · ORB-SLAM3 + DAV3 + Astra</th><td colspan="4" class="pending">待 M3 Blender 模型冻结</td></tr>
        <tr><th>M4 · GT pose + DAV3 + Astra</th><td colspan="4" class="pending">待 M4 Blender 模型冻结</td></tr>
      </tbody>
    </table></div>

    <h2>Table 5. 全部建模视角的输入一致性</h2>
    <p>该表比较每个冻结 Blender 模型的射线深度与该方法自己的建模输入深度。较低误差只表示模型更贴近自身输入，不等于更接近 GT。</p>
    <div class="scroll"><table>
      <thead><tr><th>方法</th><th>深度 RMSE (m) ↓</th><th>整体 AbsRel ↓</th><th>逐帧 AbsRel 中位数 ↓</th><th>表面覆盖率 ↑</th></tr></thead>
      <tbody>
        <tr><th>M1 · 纯视觉 + Astra</th><td colspan="4" class="pending">M1 无原生深度；待定义 RGB-only 模型检查口径</td></tr>
        <tr><th>M2 · ViPE + DAV3 + Astra</th><td colspan="4" class="pending">待 M2 Blender 模型冻结</td></tr>
        <tr><th>M3 · ORB-SLAM3 + DAV3 + Astra</th><td colspan="4" class="pending">待 M3 Blender 模型冻结</td></tr>
        <tr><th>M4 · GT pose + DAV3 + Astra</th><td colspan="4" class="pending">待 M4 Blender 模型冻结</td></tr>
      </tbody>
    </table></div>
  </section>

  <section id="evidence">
    <p class="eyebrow">06 / EVIDENCE</p>
    <h2>冻结数据与复现</h2>
    <div class="cards">
      <article><h3>输入</h3><p>4,499 RGB 帧、44,999 IMU 样本，25 Hz / 250 Hz；同一 Isaac 仿真时钟。</p></article>
      <article><h3>共同区间</h3><p>源帧 245–4498；位姿使用 4,254 个严格共同时间戳，深度使用 180 个建模帧与互斥的 500 个评测帧。</p></article>
      <article><h3>数据仓库</h3><p><a href="{DATASET_URL}">打开私有 Dataset</a>，下载视频、轨迹、DA3 深度、GT optical-Z、逐帧指标与复现代码。</p></article>
    </div>
  </section>
</main>
<footer>World Lobby · frozen outputs · private release</footer>
</body>
</html>
"""
    (SPACE / "index.html").write_text(html)

    css = """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f1ea;color:#17211c;font:16px/1.65 Inter,ui-sans-serif,system-ui,sans-serif}header,main,footer{max-width:1180px;margin:auto;padding:28px}header{padding-top:64px;border-bottom:1px solid #aeb9b1}h1{font-family:Georgia,serif;font-size:clamp(42px,7vw,82px);line-height:1.02;margin:.15em 0;color:#173f34}h2{font-family:Georgia,serif;font-size:clamp(28px,4vw,44px);line-height:1.15}h3{margin-bottom:.25em}.eyebrow{letter-spacing:.16em;text-transform:uppercase;font-size:12px;font-weight:750;color:#586b61}.lede{font-size:20px;max-width:820px}nav{display:flex;gap:18px;flex-wrap:wrap;margin-top:24px}a{color:#145c49;text-decoration-thickness:1px;text-underline-offset:3px}section{padding:44px 0;border-bottom:1px solid #c8cfc9}.notice{margin-top:30px;padding:20px 24px;background:#e3ece6;border-left:4px solid #1f6a54}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;background:#fbfaf6}th,td{padding:13px 15px;border-bottom:1px solid #d5d9d5;text-align:left;vertical-align:top}thead th{background:#193f35;color:white}.best{background:#e2efe8}.pending{color:#8a4b13;background:#fff3dc;font-weight:650}.figure-grid,.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.cards{grid-template-columns:repeat(3,minmax(0,1fr))}.cards article{background:#fbfaf6;border:1px solid #c8cfc9;padding:18px}figure{margin:24px 0}img{display:block;width:100%;height:auto;background:white;border:1px solid #c8cfc9}figcaption,.caption-note{color:#53635b;font-size:14px;margin-top:8px}code{background:#e8e8e1;padding:.1em .3em;border-radius:3px}footer{color:#66756d;font-size:14px}@media(max-width:760px){.figure-grid,.cards{grid-template-columns:1fr}header,main,footer{padding:20px}header{padding-top:42px}}"""
    (SPACE / "styles.css").write_text(css)


def build_dataset() -> None:
    reset_dir(DATASET)
    selected = {
        SESSION / "simulation_vio.mp4": DATASET / "input/simulation_vio.mp4",
        SESSION / "manifest.json": DATASET / "input/manifest.json",
        SESSION / "inputs/calibration.json": DATASET / "input/calibration.json",
        SESSION / "inputs/cam0/data.csv": DATASET / "input/cam0/data.csv",
        SESSION / "inputs/imu0/data.csv": DATASET / "input/imu0/data.csv",
        SESSION / "ground_truth/camera_tum.txt": DATASET / "ground_truth/camera_tum.txt",
        SESSION / "ground_truth/generator.json": DATASET / "ground_truth/generator.json",
        EVAL / "metrics.json": DATASET / "evaluation/metrics.json",
        EVAL / "per_frame_errors.csv": DATASET / "evaluation/per_frame_errors.csv",
        EVAL / "aligned_common_trajectories.npz": DATASET / "evaluation/aligned_common_trajectories.npz",
        EVAL / "trajectory_comparison.png": DATASET / "evaluation/trajectory_comparison.png",
        EVAL / "figure14a_camera_trajectories.png": DATASET / "evaluation/figure14a_camera_trajectories.png",
        EVAL / "REPORT.md": DATASET / "evaluation/REPORT.md",
        BASE / "data/depth_samples/modeling_180.json": DATASET / "depth/samples/modeling_180.json",
        BASE / "data/depth_samples/eval_500.json": DATASET / "depth/samples/eval_500.json",
        DEPTH_EVAL / "verification.json": DATASET / "depth/evaluation/verification.json",
        DEPTH_EVAL / "metrics/modeling_180/metrics.json": DATASET / "depth/evaluation/modeling_180/metrics.json",
        DEPTH_EVAL / "metrics/modeling_180/per_frame_metrics.csv": DATASET / "depth/evaluation/modeling_180/per_frame_metrics.csv",
        DEPTH_EVAL / "metrics/eval_500/metrics.json": DATASET / "depth/evaluation/eval_500/metrics.json",
        DEPTH_EVAL / "metrics/eval_500/per_frame_metrics.csv": DATASET / "depth/evaluation/eval_500/per_frame_metrics.csv",
        DEPTH_EVAL / "gt/modeling_180/manifest.json": DATASET / "depth/ground_truth/modeling_180/manifest.json",
        DEPTH_EVAL / "gt/modeling_180/gt_depth_modeling_180.npz": DATASET / "depth/ground_truth/modeling_180/gt_depth_modeling_180.npz",
        DEPTH_EVAL / "gt/eval_500/manifest.json": DATASET / "depth/ground_truth/eval_500/manifest.json",
        DEPTH_EVAL / "gt/eval_500/gt_depth_eval_500.npz": DATASET / "depth/ground_truth/eval_500/gt_depth_eval_500.npz",
        BASE / "contract.json": DATASET / "provenance/contract.json",
        BASE / "verification.json": DATASET / "provenance/verification.json",
        BASE / "COMMANDS.md": DATASET / "provenance/COMMANDS.md",
        BASE / "四轨迹统一对比_c01acd21.plan.md": DATASET / "provenance/四轨迹统一对比_c01acd21.plan.md",
        BASE / "frozen/vipe_default/camera.npz": DATASET / "trajectories/vipe_default/camera.npz",
        BASE / "frozen/vipe_default/complete.json": DATASET / "trajectories/vipe_default/complete.json",
        BASE / "frozen/openvins/camera.npz": DATASET / "trajectories/openvins/camera.npz",
        BASE / "frozen/openvins/complete.json": DATASET / "trajectories/openvins/complete.json",
        ORB / "camera.npz": DATASET / "trajectories/orb_slam3/camera.npz",
        ORB / "complete.json": DATASET / "trajectories/orb_slam3/complete.json",
        ORB / "inertial_evidence.json": DATASET / "trajectories/orb_slam3/inertial_evidence.json",
        SPACE / "assets/figure14_abc.png": DATASET / "figures/figure14_abc.png",
        SPACE / "assets/figure14_abc.pdf": DATASET / "figures/figure14_abc.pdf",
        SPACE / "assets/figure14a.png": DATASET / "figures/figure14a.png",
        SPACE / "assets/figure14b.png": DATASET / "figures/figure14b.png",
        SPACE / "assets/figure14c.png": DATASET / "figures/figure14c.png",
    }
    for source, destination in selected.items():
        copy(source, destination)
    for method, slug in DEPTH_METHODS.items():
        copy(BASE / f"packets/{method}/packet.json", DATASET / f"depth/packets/{method}/packet.json")
        for split in ("modeling_180", "eval_500"):
            source = BASE / f"depth/{slug}/{split}/consolidated"
            destination = DATASET / f"depth/predictions/{method}/{split}"
            shutil.copytree(source, destination)
    release_scripts = (
        "build_hf_release.py",
        "evaluate_and_plot.py",
        "freeze_contract.py",
        "freeze_openvins.py",
        "freeze_vipe.py",
        "generate_canvas.py",
        "verify_results.py",
        "build_depth_packets.py",
        "depth_pipeline.py",
        "evaluate_da3_depth.py",
        "generate_gt_depth_blender.py",
        "prepare_depth_samples.py",
        "run_da3_depth.py",
        "test_depth_pipeline.py",
        "verify_depth_pipeline.py",
    )
    for filename in release_scripts:
        script = BASE / "code" / filename
        copy(script, DATASET / "code" / filename)

    readme = """---
license: other
tags:
- robotics
- visual-inertial-odometry
- simulation
- trajectory-evaluation
---

# World Lobby experiments · new 180 s capture

Private evidence bundle backing the matching Space
[`Ooliva/world-lobby-exps-new`](https://huggingface.co/spaces/Ooliva/world-lobby-exps-new).

## Scope

- Input: 180 s H.264 video, camera/IMU timestamp tables, calibration and GT camera trajectory.
- Frozen estimates: ORB-SLAM3, ViPE default and OpenVINS.
- Evaluation: 4,254 exact common timestamps; one global SE(3), scale fixed to 1.
- Pose-conditioned DA3-GIANT depth: M2=ViPE, M3=ORB-SLAM3, M4=GT pose.
- Depth evaluation: 180 modelling frames plus a disjoint 500-frame held-out set,
  with GT optical-Z, consolidated predictions, per-frame metrics and provenance.
- Figures: Figure 14(a)(b)(c), full comparison, JSON metrics and per-frame CSV.
- Provenance: commands, contract, verification, plan and source scripts.

The 16 GB directory of 4,499 lossless source PNG files is intentionally not duplicated
in this result repository. The video and all sensor/evaluation records are included.
The original local run used those source PNGs, as recorded by the frozen contract.

## Important method-status note

M2–M4 DAV3 depth is complete. New M1–M4 Astra/Blender models have not been built,
so model-depth, novel-view model-depth and model-to-input consistency cells remain
explicitly pending in the Space. Native DAV3 metrics are never presented as model metrics.
"""
    (DATASET / "README.md").write_text(readme)

    files = sorted(path for path in DATASET.rglob("*") if path.is_file())
    manifest = {
        "schema_version": 1,
        "space": "Ooliva/world-lobby-exps-new",
        "dataset": "Ooliva/world-lobby-exps-new",
        "visibility_requested": "private",
        "scope": "new 180 s capture pose and pose-conditioned DA3 depth evidence",
        "files": {
            str(path.relative_to(DATASET)): {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        },
    }
    (DATASET / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    files = sorted(path for path in DATASET.rglob("*") if path.is_file())
    with (DATASET / "SHA256SUMS").open("w") as handle:
        for path in files:
            handle.write(f"{sha256(path)}  {path.relative_to(DATASET)}\n")


def main() -> None:
    metrics = json.loads((EVAL / "metrics.json").read_text())
    depth_reports = load_depth_reports()
    build_space(metrics, depth_reports)
    build_dataset()
    print(json.dumps({
        "space_dir": str(SPACE),
        "dataset_dir": str(DATASET),
        "dataset_bytes": sum(p.stat().st_size for p in DATASET.rglob("*") if p.is_file()),
        "space_bytes": sum(p.stat().st_size for p in SPACE.rglob("*") if p.is_file()),
    }, indent=2))


if __name__ == "__main__":
    main()
