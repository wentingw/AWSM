#!/usr/bin/env python3
"""Freeze full-frame default ViPE camera output before GT evaluation."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "world_model_blog/experiments/world_lobby/four_trajectory_20260929/vipe_default_full"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
OUT = ROOT / "world_lobby_four_trajectory_20260929/frozen/vipe_default"
RUNNER = ROOT / "world_model_blog/src/vipe/run_full_vipe.py"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stage = json.loads((RUN / "keyframe_stage_complete.json").read_text())
    provenance = json.loads((RUN / "input_provenance.json").read_text())
    assert stage["status"] == "FULL_POSE_AND_KEYFRAME_DEPTH_COMPLETE_REST_PENDING"
    assert stage["pose_frames"] == 4499
    assert provenance["inference_inputs"] == "RGB PNG files only"
    assert len(provenance["source_frames"]) == 4499
    source = np.load(RUN / "camera.npz")
    transforms = np.asarray(source["camera_to_world"], dtype=float)
    timestamps = np.asarray(source["timestamps_ns"], dtype=np.int64)
    assert transforms.shape == (4499, 4, 4)
    assert np.isfinite(transforms).all() and np.all(np.diff(timestamps) > 0)
    rotation = transforms[:, :3, :3]
    assert np.allclose(rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=2e-4)
    assert np.allclose(np.linalg.det(rotation), 1.0, atol=2e-4)
    first_hash = sha256(Path(provenance["source_frames"][0]["path"]))
    last_hash = sha256(Path(provenance["source_frames"][-1]["path"]))
    assert first_hash == provenance["source_frames"][0]["sha256"]
    assert last_hash == provenance["source_frames"][-1]["sha256"]

    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUN / "camera.npz", OUT / "camera.npz")
    result = {
        "status": "COMPLETE",
        "estimator": "ViPE default RGB-only no_vda",
        "target_frames": 4499,
        "valid_frames": 4499,
        "coverage": 1.0,
        "camera_sha256": sha256(OUT / "camera.npz"),
        "source_camera_sha256": sha256(RUN / "camera.npz"),
        "input_provenance_sha256": sha256(RUN / "input_provenance.json"),
        "keyframe_stage_sha256": sha256(RUN / "keyframe_stage_complete.json"),
        "runner_sha256": sha256(RUNNER),
        "pipeline": "no_vda",
        "keyframe_depth": "unidepth-s",
        "depth_align_model": "adaptive_unidepth-s",
        "depth_status": "90 keyframe depths complete; remaining depths intentionally not required for pose comparison",
        "timestamp_policy": "all native camera timestamps, no interpolation",
        "input_policy": "4499 original PNG frames only; no IMU, external pose/depth, or truth",
        "ground_truth_read": False,
    }
    (OUT / "complete.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
