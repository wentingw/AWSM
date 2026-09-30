#!/usr/bin/env python3
"""Freeze estimator-only inputs and configuration before any new GT evaluation."""
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "world_lobby_four_trajectory_20260929"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
ORB = ROOT / "stable_orbit_orb_success_20260929/frozen"
VIPE_RUNNER = ROOT / "world_model_blog/src/vipe/run_full_vipe.py"
OPENVINS_ROOT = ROOT / "stable_orbit_da3_rerun_20260923"
OPENVINS_RUNNER = OPENVINS_ROOT / "code/openvins/offline/offline_runner.cpp"
OPENVINS_CONFIG = OPENVINS_ROOT / "configs/openvins/openvins_maxclones31.yaml"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rows(path):
    with path.open(newline="") as handle:
        return [row for row in csv.reader(handle) if row and not row[0].startswith("#")]


def main():
    manifest = json.loads((SESSION / "manifest.json").read_text())
    calibration = json.loads((SESSION / "inputs/calibration.json").read_text())
    camera_rows = rows(SESSION / "inputs/cam0/data.csv")
    imu_rows = rows(SESSION / "inputs/imu0/data.csv")
    orb_meta = json.loads((ORB / "complete.json").read_text())
    assert manifest["finalized"] and manifest["frames"] == len(camera_rows) == 4499
    assert manifest["imu_samples"] == len(imu_rows) == 44999
    assert manifest["unmatched_frames"] == 0
    assert calibration["intrinsics"] == [762.8, 762.8, 640.0, 480.0]
    assert sha256(ORB / "camera.npz") == orb_meta["camera_sha256"]
    assert orb_meta["ground_truth_read"] is False
    assert all(int(a[0]) < int(b[0]) for a, b in zip(camera_rows, camera_rows[1:]))
    assert all(int(a[0]) < int(b[0]) for a, b in zip(imu_rows, imu_rows[1:]))

    contract = {
        "schema_version": 1,
        "status": "FROZEN_BEFORE_NEW_ESTIMATOR_GT_EVALUATION",
        "session": str(SESSION),
        "video": str(SESSION / manifest["video"]),
        "frames": len(camera_rows),
        "imu_samples": len(imu_rows),
        "camera_timestamp_range_ns": [int(camera_rows[0][0]), int(camera_rows[-1][0])],
        "imu_timestamp_range_ns": [int(imu_rows[0][0]), int(imu_rows[-1][0])],
        "calibration": calibration,
        "inputs": {
            "manifest_sha256": sha256(SESSION / "manifest.json"),
            "camera_csv_sha256": sha256(SESSION / "inputs/cam0/data.csv"),
            "imu_csv_sha256": sha256(SESSION / "inputs/imu0/data.csv"),
            "calibration_sha256": sha256(SESSION / "inputs/calibration.json"),
            "video_sha256": sha256(SESSION / manifest["video"]),
        },
        "estimators": {
            "orb_slam3": {
                "frozen_camera": str(ORB / "camera.npz"),
                "camera_sha256": orb_meta["camera_sha256"],
                "coverage": orb_meta["coverage"],
            },
            "vipe_default": {
                "runner": str(VIPE_RUNNER),
                "runner_sha256": sha256(VIPE_RUNNER),
                "pipeline": "no_vda",
                "keyframe_depth": "unidepth-s",
                "depth_align_model": "adaptive_unidepth-s",
                "slam_target_pixels": 98304,
                "input_policy": "all 4499 native PNG frames; RGB only",
            },
            "openvins": {
                "runner_source": str(OPENVINS_RUNNER),
                "runner_source_sha256": sha256(OPENVINS_RUNNER),
                "config": str(OPENVINS_CONFIG),
                "config_sha256": sha256(OPENVINS_CONFIG),
                "input_policy": "native camera CSV/PNG plus FRD IMU converted to FLU in runner",
            },
        },
        "evaluation_policy": {
            "primary": "strict timestamp intersection; one global SE3 per estimator; scale=1",
            "diagnostic": "one global Sim3 per estimator",
            "missing_poses": "remain missing; no interpolation or extrapolation",
            "ground_truth": "forbidden until ViPE and OpenVINS outputs are frozen",
        },
        "ground_truth_read": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "contract.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps({
        "status": contract["status"],
        "frames": contract["frames"],
        "imu_samples": contract["imu_samples"],
        "orb_coverage": contract["estimators"]["orb_slam3"]["coverage"],
    }, indent=2))


if __name__ == "__main__":
    main()
