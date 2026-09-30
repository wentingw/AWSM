#!/usr/bin/env python3
"""Convert native OpenVINS TUM output to an immutable exact camera schedule."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "world_lobby_four_trajectory_20260929/openvins/full"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
OUT = ROOT / "world_lobby_four_trajectory_20260929/frozen/openvins"
CONFIG = ROOT / "stable_orbit_da3_rerun_20260923/configs/openvins/openvins_maxclones31.yaml"
RUNNER = ROOT / "stable_orbit_da3_rerun_20260923/code/openvins/offline/offline_runner.cpp"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    metadata = json.loads((RUN / "metadata.json").read_text())
    assert metadata["gt_used"] is False
    native = np.loadtxt(RUN / "pose_cam.tum")
    assert native.ndim == 2 and native.shape[1] == 8 and len(native) > 0
    native_ns = np.rint(native[:, 0] * 1e9).astype(np.int64)
    assert np.all(np.diff(native_ns) > 0)
    rotation = Rotation.from_quat(native[:, 4:8]).as_matrix()
    assert np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=1e-7)
    transforms = np.broadcast_to(np.eye(4), (len(native), 4, 4)).copy()
    transforms[:, :3, :3] = rotation
    transforms[:, :3, 3] = native[:, 1:4]

    with (SESSION / "inputs/cam0/data.csv").open() as handle:
        rows = [row for row in csv.reader(handle) if row and not row[0].startswith("#")]
    target_ns = np.array([int(row[0]) for row in rows], dtype=np.int64)
    index = np.searchsorted(target_ns, native_ns)
    assert np.all(index < len(target_ns))
    assert np.array_equal(target_ns[index], native_ns)
    valid = np.zeros(len(target_ns), dtype=bool)
    valid[index] = True
    schedule = np.full((len(target_ns), 4, 4), np.nan)
    schedule[index] = transforms
    calibration = json.loads((SESSION / "inputs/calibration.json").read_text())
    fx, fy, cx, cy = calibration["intrinsics"]
    intrinsics = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=float)

    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT / "camera.npz",
        timestamps_ns=native_ns,
        camera_to_world=transforms,
        source_indices=index,
        intrinsics=intrinsics,
    )
    np.savez_compressed(
        OUT / "camera_schedule.npz",
        timestamps_ns=target_ns,
        camera_to_world=schedule,
        valid=valid,
        intrinsics=intrinsics,
    )
    result = {
        "status": "COMPLETE_WITH_MISSING_INITIALIZATION_POSES",
        "estimator": "OpenVINS offline mono-inertial",
        "target_frames": len(target_ns),
        "valid_frames": int(valid.sum()),
        "coverage": float(valid.mean()),
        "first_valid_source_index": int(index[0]),
        "last_valid_source_index": int(index[-1]),
        "contiguous_valid_schedule": bool(np.array_equal(index, np.arange(index[0], index[-1] + 1))),
        "camera_sha256": sha256(OUT / "camera.npz"),
        "schedule_sha256": sha256(OUT / "camera_schedule.npz"),
        "native_tum_sha256": sha256(RUN / "pose_cam.tum"),
        "state_sha256": sha256(RUN / "state.txt"),
        "metadata_sha256": sha256(RUN / "metadata.json"),
        "config_sha256": sha256(CONFIG),
        "runner_source_sha256": sha256(RUNNER),
        "conversion": "native OpenVINS T_WC; exact rounded nanosecond match to camera CSV",
        "missing_policy": "pre-initialization poses remain invalid; no interpolation",
        "ground_truth_read": False,
    }
    (OUT / "complete.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
