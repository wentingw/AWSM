#!/usr/bin/env python3
"""Evaluate frozen trajectories and render a Figure 14(a)-style comparison."""
import csv
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "world_lobby_four_trajectory_20260929"
OUT = BASE / "evaluation"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
SOURCES = {
    "ORB-SLAM3": ROOT / "stable_orbit_orb_success_20260929/frozen/camera.npz",
    "ViPE default": BASE / "frozen/vipe_default/camera.npz",
    "OpenVINS": BASE / "frozen/openvins/camera.npz",
}
COLORS = {"ORB-SLAM3": "#d95f02", "ViPE default": "#2878b5", "OpenVINS": "#c2674b"}
STYLES = {"ORB-SLAM3": "-", "ViPE default": "-.", "OpenVINS": "--"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    values = np.asarray(values, dtype=float)
    return {
        "count": int(len(values)),
        "mean": float(values.mean()),
        "rmse": float(np.sqrt(np.mean(values**2))),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "max": float(values.max()),
    }


def align(source, target, scale_fitting):
    sx = source - source.mean(axis=0)
    ty = target - target.mean(axis=0)
    u, singular, vt = np.linalg.svd(sx.T @ ty / len(source))
    diagonal = np.ones(3)
    diagonal[-1] = np.linalg.det(vt.T @ u.T)
    rotation = vt.T @ np.diag(diagonal) @ u.T
    scale = (
        float((singular * diagonal).sum() / np.mean(np.sum(sx * sx, axis=1)))
        if scale_fitting else 1.0
    )
    translation = target.mean(axis=0) - scale * rotation @ source.mean(axis=0)
    return scale, rotation, translation


def evaluate(transforms, gt_position, gt_rotation, scale_fitting):
    position = transforms[:, :3, 3]
    orientation = Rotation.from_matrix(transforms[:, :3, :3])
    scale, rotation, translation = align(position, gt_position, scale_fitting)
    aligned_position = scale * (position @ rotation.T) + translation
    aligned_rotation = Rotation.from_matrix(rotation) * orientation
    translation_error = np.linalg.norm(aligned_position - gt_position, axis=1)
    rotation_error = (gt_rotation.inv() * aligned_rotation).magnitude() * 180 / math.pi
    return {
        "scale": scale,
        "rotation": rotation.tolist(),
        "translation": translation.tolist(),
        "translation_m": stats(translation_error),
        "rotation_deg": stats(rotation_error),
    }, aligned_position, translation_error, rotation_error


def load_estimate(path):
    data = np.load(path)
    transforms = np.asarray(data["camera_to_world"], dtype=float)
    timestamps = np.asarray(data["timestamps_ns"], dtype=np.int64)
    if "source_indices" in data:
        source_indices = np.asarray(data["source_indices"], dtype=int)
    elif "indices" in data:
        source_indices = np.asarray(data["indices"], dtype=int)
    else:
        source_indices = np.arange(len(timestamps))
    assert len(transforms) == len(timestamps) == len(source_indices)
    assert np.isfinite(transforms).all() and np.all(np.diff(timestamps) > 0)
    rotation = transforms[:, :3, :3]
    assert np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=2e-4)
    return timestamps, source_indices, transforms


def fmt(value, digits=4):
    return f"{value:.{digits}f}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (SESSION / "ground_truth/camera.csv").open() as handle:
        gt_rows = [row for row in csv.reader(handle) if row and not row[0].startswith("#")]
    gt_timestamps = np.array([int(row[0]) for row in gt_rows], dtype=np.int64)
    gt_values = np.array([[float(value) for value in row[1:]] for row in gt_rows])

    loaded = {name: load_estimate(path) for name, path in SOURCES.items()}
    timestamp_sets = [set(value[0].tolist()) for value in loaded.values()]
    common_timestamps = np.array(sorted(set.intersection(*timestamp_sets)), dtype=np.int64)
    assert len(common_timestamps) > 0
    gt_lookup = {int(timestamp): index for index, timestamp in enumerate(gt_timestamps)}
    assert all(int(timestamp) in gt_lookup for timestamp in common_timestamps)
    gt_indices = np.array([gt_lookup[int(timestamp)] for timestamp in common_timestamps])
    gt_position = gt_values[gt_indices, :3]
    gt_rotation = Rotation.from_quat(gt_values[gt_indices, 3:7])

    result = {
        "schema_version": 1,
        "scope": "strict common native timestamps across ORB-SLAM3, ViPE default and OpenVINS",
        "target_frames": len(gt_timestamps),
        "common_frames": len(common_timestamps),
        "common_first_source_index": int(gt_indices[0]),
        "common_last_source_index": int(gt_indices[-1]),
        "common_timestamp_sha256": hashlib.sha256(common_timestamps.tobytes()).hexdigest(),
        "alignment": {
            "primary": "one global rigid SE3 per estimator; scale=1",
            "diagnostic": "one global Sim3 per estimator",
            "ground_truth_read_after_all_estimator_outputs_frozen": True,
        },
        "methods": {},
        "sources": {},
    }
    arrays = {"GT": gt_position}
    error_rows = []
    aligned = {}
    errors = {}
    for name, path in SOURCES.items():
        timestamps, source_indices, transforms = loaded[name]
        lookup = {int(timestamp): index for index, timestamp in enumerate(timestamps)}
        take = np.array([lookup[int(timestamp)] for timestamp in common_timestamps])
        selected = transforms[take]
        se3, aligned_position, translation_error, rotation_error = evaluate(
            selected, gt_position, gt_rotation, False
        )
        sim3, _, _, _ = evaluate(selected, gt_position, gt_rotation, True)
        result["methods"][name] = {
            "valid_frames": len(timestamps),
            "coverage": float(len(timestamps) / len(gt_timestamps)),
            "common_frames": len(common_timestamps),
            "se3": se3,
            "sim3_diagnostic": sim3,
        }
        result["sources"][name] = {
            "path": str(path),
            "sha256": sha256(path),
            "first_source_index": int(source_indices[0]),
            "last_source_index": int(source_indices[-1]),
        }
        aligned[name] = aligned_position
        errors[name] = (translation_error, rotation_error)
        arrays[name] = aligned_position
        for index, timestamp in enumerate(common_timestamps):
            error_rows.append({
                "method": name,
                "common_index": index,
                "source_index": int(gt_indices[index]),
                "timestamp_ns": int(timestamp),
                "elapsed_s": float((timestamp - common_timestamps[0]) / 1e9),
                "aligned_x_m": float(aligned_position[index, 0]),
                "aligned_y_m": float(aligned_position[index, 1]),
                "aligned_z_m": float(aligned_position[index, 2]),
                "translation_error_m": float(translation_error[index]),
                "rotation_error_deg": float(rotation_error[index]),
            })

    elapsed = (common_timestamps - common_timestamps[0]) / 1e9
    display = np.unique(np.linspace(0, len(common_timestamps) - 1, min(450, len(common_timestamps))).astype(int))
    fig = plt.figure(figsize=(16, 11), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    xy = fig.add_subplot(grid[0, 0])
    xyz = fig.add_subplot(grid[0, 1], projection="3d")
    trans = fig.add_subplot(grid[1, 0])
    rot = fig.add_subplot(grid[1, 1])
    xy.plot(gt_position[display, 0], gt_position[display, 1], color="black", lw=2.2, label="GT")
    xyz.plot(
        gt_position[display, 0], gt_position[display, 1], gt_position[display, 2],
        color="black", lw=2.2, label="GT",
    )
    for name in SOURCES:
        value = aligned[name]
        xy.plot(value[display, 0], value[display, 1], color=COLORS[name], ls=STYLES[name], lw=1.7, label=name)
        xyz.plot(
            value[display, 0], value[display, 1], value[display, 2],
            color=COLORS[name], ls=STYLES[name], lw=1.5, label=name,
        )
        trans.plot(elapsed, errors[name][0], color=COLORS[name], ls=STYLES[name], lw=1.3, label=name)
        rot.plot(elapsed, errors[name][1], color=COLORS[name], ls=STYLES[name], lw=1.3, label=name)
    xy.set(title="(a) Camera trajectories: XY projection", xlabel="world x (m)", ylabel="world y (m)")
    xy.set_aspect("equal", adjustable="datalim")
    xyz.set(
        title="(b) Camera trajectories: 3D",
        xlabel="world x (m)", ylabel="world y (m)", zlabel="world z (m)",
    )
    trans.set(title="(c) Translation error after SE(3)", xlabel="time since common start (s)", ylabel="error (m)")
    rot.set(title="(d) Rotation error after SE(3)", xlabel="time since common start (s)", ylabel="error (degrees)")
    for axis in (xy, xyz, trans, rot):
        axis.grid(alpha=0.22)
        axis.legend(fontsize=8, framealpha=0.9)
    trans.set_ylim(bottom=0)
    rot.set_ylim(bottom=0)
    fig.suptitle(
        "World Lobby 180 s: GT, ORB-SLAM3, ViPE default and OpenVINS\n"
        f"Identical {len(common_timestamps)} native frames; one rigid SE(3) alignment per estimator; no scale fitting",
        fontsize=13,
    )
    fig.savefig(OUT / "trajectory_comparison.png", dpi=180)
    fig.savefig(OUT / "trajectory_comparison.pdf")
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(9.5, 8), layout="constrained")
    axis.plot(gt_position[display, 0], gt_position[display, 1], color="black", lw=2.2, label="GT")
    for name in SOURCES:
        value = aligned[name]
        axis.plot(value[display, 0], value[display, 1], color=COLORS[name], ls=STYLES[name], lw=1.8, label=name)
    axis.set(
        title="Figure 14(a)-style camera trajectories: XY projection",
        xlabel="world x (m)", ylabel="world y (m)",
    )
    axis.set_aspect("equal", adjustable="datalim")
    axis.grid(alpha=0.22)
    axis.legend(framealpha=0.9)
    fig.savefig(OUT / "figure14a_camera_trajectories.png", dpi=200)
    fig.savefig(OUT / "figure14a_camera_trajectories.pdf")
    plt.close(fig)

    with (OUT / "per_frame_errors.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(error_rows[0]))
        writer.writeheader()
        writer.writerows(error_rows)
    np.savez_compressed(
        OUT / "aligned_common_trajectories.npz",
        timestamps_ns=common_timestamps,
        source_indices=gt_indices,
        gt_position=gt_position,
        orb_slam3_position=aligned["ORB-SLAM3"],
        vipe_default_position=aligned["ViPE default"],
        openvins_position=aligned["OpenVINS"],
    )
    (OUT / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")

    header = (
        "| Method | Coverage | Common | SE(3) ATE RMSE m | Median | P95 | Max | "
        "Rotation RMSE deg | Median | P95 | Max | Sim(3) scale | Sim(3) ATE RMSE m |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    )
    rows = []
    for name, method in result["methods"].items():
        t = method["se3"]["translation_m"]
        r = method["se3"]["rotation_deg"]
        s = method["sim3_diagnostic"]
        rows.append(
            f"| {name} | {method['coverage']:.2%} | {method['common_frames']} | "
            f"{fmt(t['rmse'])} | {fmt(t['median'])} | {fmt(t['p95'])} | {fmt(t['max'])} | "
            f"{fmt(r['rmse'])} | {fmt(r['median'])} | {fmt(r['p95'])} | {fmt(r['max'])} | "
            f"{s['scale']:.6f} | {fmt(s['translation_m']['rmse'])} |"
        )
    report = f"""# World Lobby four-trajectory comparison

Input: `{SESSION / 'simulation_vio.mp4'}`

Primary ranking uses {len(common_timestamps)} exact common native timestamps (source indices
{gt_indices[0]}–{gt_indices[-1]}). Each estimator receives one global SE(3) alignment with
scale fixed to 1. Sim(3) values are diagnostic only.

{header}{chr(10).join(rows)}

![Four trajectory comparison](trajectory_comparison.png)

All estimator outputs were frozen and hashed before ground truth was opened. Missing poses
were not interpolated or extrapolated.
"""
    (OUT / "REPORT.md").write_text(report)
    html_rows = []
    for name, method in result["methods"].items():
        t = method["se3"]["translation_m"]
        r = method["se3"]["rotation_deg"]
        s = method["sim3_diagnostic"]
        html_rows.append(
            "<tr>"
            f"<th>{name}</th><td>{method['coverage']:.2%}</td><td>{method['common_frames']}</td>"
            f"<td>{fmt(t['rmse'])}</td><td>{fmt(t['median'])}</td><td>{fmt(t['p95'])}</td><td>{fmt(t['max'])}</td>"
            f"<td>{fmt(r['rmse'])}</td><td>{fmt(r['median'])}</td><td>{fmt(r['p95'])}</td><td>{fmt(r['max'])}</td>"
            f"<td>{s['scale']:.6f}</td><td>{fmt(s['translation_m']['rmse'])}</td></tr>"
        )
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>World Lobby four-trajectory metrics</title>
<style>body{font:15px system-ui;margin:2rem;color:#1d2430}table{border-collapse:collapse;width:100%;min-width:1050px}
th,td{border:1px solid #ccd2da;padding:.55rem;text-align:right}th:first-child{text-align:left}
thead th{background:#eef1f5}.scroll{overflow:auto}img{max-width:100%;height:auto}small{color:#596273}</style></head><body>
<h1>World Lobby four-trajectory comparison</h1>
<p>Strict common native timestamps; one global SE(3) alignment per estimator; scale=1.</p>
<div class="scroll"><table><thead><tr><th>Method</th><th>Coverage</th><th>Common</th>
<th>ATE RMSE m</th><th>ATE median</th><th>ATE P95</th><th>ATE max</th>
<th>Rot RMSE deg</th><th>Rot median</th><th>Rot P95</th><th>Rot max</th>
<th>Sim(3) scale</th><th>Sim(3) ATE RMSE m</th></tr></thead><tbody>""" + "".join(html_rows) + """</tbody></table></div>
<p><img src="trajectory_comparison.png" alt="GT ORB-SLAM3 ViPE default and OpenVINS trajectories and errors"></p>
<small>Sim(3) is diagnostic only. Estimator outputs were frozen before GT access.</small></body></html>
"""
    (OUT / "metrics_table.html").write_text(html)
    print(json.dumps({
        name: {
            "coverage": method["coverage"],
            "se3_ate_rmse_m": method["se3"]["translation_m"]["rmse"],
            "rotation_rmse_deg": method["se3"]["rotation_deg"]["rmse"],
            "sim3_scale": method["sim3_diagnostic"]["scale"],
        }
        for name, method in result["methods"].items()
    }, indent=2))


if __name__ == "__main__":
    main()
