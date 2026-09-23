#!/usr/bin/env python3
"""Freeze and evaluate an isolated OpenVINS run after estimation completes."""
import argparse, csv, hashlib, json, re
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_tum(p):
    x = np.loadtxt(p)
    return x.reshape(1, -1) if x.ndim == 1 else x

def interp_pose(x, ts):
    ts = np.asarray(ts)
    keep = (ts >= x[0, 0]) & (ts <= x[-1, 0])
    t = ts[keep]
    p = np.column_stack([np.interp(t, x[:, 0], x[:, k]) for k in (1, 2, 3)])
    q = Slerp(x[:, 0], Rotation.from_quat(x[:, 4:8]))(t).as_quat()
    return np.column_stack([t, p, q]), keep

def evaluate(est, truth):
    est, _ = interp_pose(est, truth[:, 0])
    gt, _ = interp_pose(truth, est[:, 0])
    er = Rotation.from_quat(est[:, 4:8]); gr = Rotation.from_quat(gt[:, 4:8])
    # Same first-pose rigid alignment as the prior OpenVINS diagnosis.
    align_r = gr[0] * er[0].inv()
    align_t = gt[0, 1:4] - align_r.apply(est[0, 1:4])
    ep = align_r.apply(est[:, 1:4]) + align_t
    pos = np.linalg.norm(ep - gt[:, 1:4], axis=1)
    ang = np.rad2deg((gr.inv() * align_r * er).magnitude())
    return {
        "matched_samples": int(len(est)),
        "first_elapsed_s": float(est[0, 0] - truth[0, 0]),
        "last_elapsed_s": float(est[-1, 0] - truth[0, 0]),
        "position_rmse_m": float(np.sqrt(np.mean(pos ** 2))),
        "position_median_m": float(np.median(pos)),
        "position_max_m": float(np.max(pos)),
        "orientation_rmse_deg": float(np.sqrt(np.mean(ang ** 2))),
        "orientation_median_deg": float(np.median(ang)),
        "orientation_max_deg": float(np.max(ang)),
        "timeline": {
            str(s): {"position_error_m": float(pos[np.argmin(abs(est[:, 0] - (truth[0, 0] + s))) ]),
                     "orientation_error_deg": float(ang[np.argmin(abs(est[:, 0] - (truth[0, 0] + s)))])}
            for s in (10, 20, 30, 40, 60, 120, 180, 240, 300, 359)
            if truth[0, 0] + s <= est[-1, 0]
        },
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--truth", type=Path, required=True)
    a = ap.parse_args(); exp = a.experiment.resolve(); out = exp / "output"
    est = load_tum(out / "pose_cam.tum"); truth = load_tum(a.truth.resolve())
    # Preserve raw-estimator coverage separately from image-time interpolation.
    cam_rows = []
    with (a.inputs / "cam0/data.csv").open() as f:
        for row in csv.reader(f):
            if row and not row[0].startswith("#"): cam_rows.append(int(row[0]) / 1e9)
    cam_ts = np.asarray(cam_rows)
    sampled_ts = cam_ts[::50]
    sampled, sample_keep = interp_pose(est, sampled_ts)
    np.savetxt(exp / "openvins_camera_pose_180.tum", sampled, fmt="%.9f")
    dense, dense_keep = interp_pose(est, cam_ts)
    np.savetxt(exp / "openvins_camera_pose_images.tum", dense, fmt="%.9f")
    # Read GT only in this post-estimation evaluator.
    metrics = evaluate(est, truth)
    lines = out.joinpath("openvins.log").read_text(errors="replace")
    # INFO logs do not contain DEBUG feature-count records.
    def count(pattern):
        n = len(re.findall(pattern, lines))
        return n if n else None
    report = {
        "status": "evaluated_after_estimation",
        "estimator_truth_read": False,
        "evaluator_truth_read": True,
        "method": "OpenVINS MSCKF, max_clones=31, original calibration, full 360 s RGB+IMU",
        "input": {"root": str(a.inputs.resolve()), "rgb_rows": int(len(cam_ts)), "imu_rows": sum(1 for r in csv.reader((a.inputs / "imu0/data.csv").open()) if r and not r[0].startswith("#"))},
        "raw_estimator_output": {"file": str(out / "pose_cam.tum"), "samples": int(len(est)), "first_timestamp": float(est[0,0]), "last_timestamp": float(est[-1,0]), "coverage_s": float(est[-1,0]-est[0,0]), "truth_overlap_samples": int(np.sum((est[:,0]>=truth[0,0])&(est[:,0]<=truth[-1,0])))},
        "image_pose_interpolation": {"file": str(exp / "openvins_camera_pose_images.tum"), "input_images": int(len(cam_ts)), "interpolated_rows": int(len(dense)), "covered_fraction": float(np.mean(dense_keep))},
        "sampled_180": {"file": str(exp / "openvins_camera_pose_180.tum"), "requested": 180, "written": int(len(sampled)), "sampling": "input camera rows 0,50,...,8950; pose linearly interpolated + quaternion SLERP from raw OpenVINS odometry"},
        "metrics_first_pose_se3_alignment": metrics,
        "diagnostic_log_counts": {"status": "unavailable_info_log_no_debug_records", "msckf_update": count(r"MSCKF update \\(\\d+ feats\\)"), "slam_update": count(r"SLAM update \\(\\d+ feats\\)"), "slam_delayed_init": count(r"SLAM delayed init \\(\\d+ feats\\)")},
        "hashes": {str(p): sha(p) for p in [out / "pose_cam.tum", out / "pose_imu.tum", out / "openvins.log", exp / "config_window31.yaml", exp / "kalibr_imu_smooth.yaml", exp / "kalibr_imucam_smooth.yaml", a.truth.resolve()]},
        "limitations": ["The ROS launcher needed SIGTERM during shutdown after replay completion; all 8999 images reported image_errors=0.", "Metrics use the established first-pose rigid alignment and are not a full-trajectory optimized SE(3) ATE.", "Raw estimator output is ~250 Hz odometry; image and 180-frame files are interpolated products and are labeled separately."]
    }
    (exp / "evaluation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    (exp / "FREEZE_MANIFEST.json").write_text(json.dumps({"status":"outputs_fingerprinted_after_run","experiment":str(exp),"gt_evaluation_already_completed":True,"files":report["hashes"]}, indent=2) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
if __name__ == "__main__": main()
