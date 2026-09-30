#!/usr/bin/env python3
"""Cross-check common timestamps, metrics, figures, and frozen provenance."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "world_lobby_four_trajectory_20260929"
EVAL = BASE / "evaluation"
CANVAS = (
    Path.home()
    / ".cursor/projects/home-hchen-Documents-astraBlenderTest/canvases"
    / "world-lobby-four-trajectory.canvas.tsx"
)
ARCHIVE_CANVAS = BASE / "world-lobby-four-trajectory.canvas.tsx"
MOTION_CANVAS = BASE / "orb-slam3-old-vs-new-motion.canvas.tsx"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    metrics = json.loads((EVAL / "metrics.json").read_text())
    assert metrics["common_frames"] == 4254
    assert metrics["common_first_source_index"] == 245
    assert metrics["common_last_source_index"] == 4498
    methods = metrics["methods"]
    assert set(methods) == {"ORB-SLAM3", "ViPE default", "OpenVINS"}
    assert methods["ORB-SLAM3"]["valid_frames"] == 4254
    assert methods["ViPE default"]["valid_frames"] == 4499
    assert methods["OpenVINS"]["valid_frames"] == 4442
    for method in methods.values():
        assert method["common_frames"] == 4254
        assert 0 < method["coverage"] <= 1
        assert method["se3"]["scale"] == 1.0
        assert method["sim3_diagnostic"]["scale"] > 0
        assert method["sim3_diagnostic"]["translation_m"]["rmse"] <= method["se3"]["translation_m"]["rmse"]

    prior_orb = json.loads(
        (ROOT / "stable_orbit_orb_success_20260929/evaluation/metrics.json").read_text()
    )
    assert abs(
        methods["ORB-SLAM3"]["se3"]["translation_m"]["rmse"]
        - prior_orb["se3"]["translation_m"]["rmse"]
    ) < 1e-12
    assert abs(
        methods["ORB-SLAM3"]["se3"]["rotation_deg"]["rmse"]
        - prior_orb["se3"]["rotation_deg"]["rmse"]
    ) < 1e-12

    with (EVAL / "per_frame_errors.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 3 * 4254
    for name in methods:
        selected = [row for row in rows if row["method"] == name]
        assert len(selected) == 4254
        timestamps = np.array([int(row["timestamp_ns"]) for row in selected], dtype=np.int64)
        assert np.all(np.diff(timestamps) > 0)
    first = [int(row["timestamp_ns"]) for row in rows if row["method"] == "ORB-SLAM3"]
    for name in ("ViPE default", "OpenVINS"):
        assert first == [int(row["timestamp_ns"]) for row in rows if row["method"] == name]

    arrays = np.load(EVAL / "aligned_common_trajectories.npz")
    assert arrays["timestamps_ns"].shape == (4254,)
    for key in ("gt_position", "orb_slam3_position", "vipe_default_position", "openvins_position"):
        assert arrays[key].shape == (4254, 3) and np.isfinite(arrays[key]).all()

    figures = {}
    for filename in ("figure14a_camera_trajectories.png", "trajectory_comparison.png"):
        path = EVAL / filename
        with Image.open(path) as image:
            assert image.width >= 900 and image.height >= 700
            figures[filename] = {"width": image.width, "height": image.height, "sha256": sha256(path)}
    html = (EVAL / "metrics_table.html").read_text()
    assert all(name in html for name in methods)
    assert "trajectory_comparison.png" in html
    canvas = CANVAS.read_text()
    assert all(name in canvas for name in ("ORB-SLAM3", "ViPE default", "OpenVINS"))
    assert "XY trajectories · common frames" in canvas
    assert ARCHIVE_CANVAS.read_text() == canvas
    assert "observability failure" in MOTION_CANVAS.read_text()

    frozen = {
        "ORB-SLAM3": ROOT / "stable_orbit_orb_success_20260929/frozen/complete.json",
        "ViPE default": BASE / "frozen/vipe_default/complete.json",
        "OpenVINS": BASE / "frozen/openvins/complete.json",
    }
    for name, path in frozen.items():
        value = json.loads(path.read_text())
        assert value["ground_truth_read"] is False
        assert metrics["sources"][name]["sha256"] == sha256(Path(metrics["sources"][name]["path"]))

    code_files = sorted((BASE / "code").glob("*.py"))
    result = {
        "status": "PASS",
        "common_timestamp_identity": True,
        "per_method_rows": 4254,
        "orb_independent_metric_reproduction": True,
        "frozen_before_gt": True,
        "figures": figures,
        "metrics_sha256": sha256(EVAL / "metrics.json"),
        "per_frame_errors_sha256": sha256(EVAL / "per_frame_errors.csv"),
        "report_sha256": sha256(EVAL / "REPORT.md"),
        "html_sha256": sha256(EVAL / "metrics_table.html"),
        "canvas_sha256": sha256(CANVAS),
        "archived_canvas_sha256": {
            ARCHIVE_CANVAS.name: sha256(ARCHIVE_CANVAS),
            MOTION_CANVAS.name: sha256(MOTION_CANVAS),
        },
        "code_sha256": {path.name: sha256(path) for path in code_files},
    }
    (BASE / "verification.json").write_text(json.dumps(result, indent=2) + "\n")

    artifacts = [
        BASE / "contract.json",
        BASE / "frozen/vipe_default/camera.npz",
        BASE / "frozen/vipe_default/complete.json",
        BASE / "frozen/openvins/camera.npz",
        BASE / "frozen/openvins/complete.json",
        EVAL / "metrics.json",
        EVAL / "per_frame_errors.csv",
        EVAL / "aligned_common_trajectories.npz",
        EVAL / "figure14a_camera_trajectories.png",
        EVAL / "trajectory_comparison.png",
        EVAL / "REPORT.md",
        EVAL / "metrics_table.html",
        BASE / "COMMANDS.md",
        ARCHIVE_CANVAS,
        MOTION_CANVAS,
        *code_files,
        BASE / "verification.json",
    ]
    with (BASE / "SHA256SUMS").open("w") as handle:
        for path in artifacts:
            handle.write(f"{sha256(path)}  {path.relative_to(BASE)}\n")
        handle.write(f"{sha256(CANVAS)}  {CANVAS}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
