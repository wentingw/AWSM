#!/usr/bin/env python3
"""Compute blog Table 2/3 model-depth metrics for astra_blender/models/M4."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from depth_math import metrics


ROOT = Path("/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929")
EVAL = ROOT / "astra_blender2/evaluation/blog_tables_1_6_current_m4"
PREDICTION = EVAL / "modeling_180/depth.npz"
GROUND_TRUTH = (
    ROOT / "astra_blender2/report/space/results/fresh_gt/modeling_180/"
    "gt_depth_modeling_180.npz"
)
MODEL = ROOT / "astra_blender/models/M4/scene.blend"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prediction = np.load(PREDICTION)
    ground_truth = np.load(GROUND_TRUTH)
    if not np.array_equal(prediction["pixel_uv"], ground_truth["pixel_uv"]):
        raise RuntimeError("Pixel grids differ")
    if not np.array_equal(prediction["timestamps_ns"], ground_truth["timestamps_ns"]):
        raise RuntimeError("Frame timestamps differ")
    predicted_z = prediction["prediction_z_m"]
    truth_z = ground_truth["truth_z_m"]
    domain = ground_truth["valid_domain"]
    rows = [
        {
            "sample_index": index,
            "timestamp_ns": int(prediction["timestamps_ns"][index]),
            **metrics(predicted_z[index], truth_z[index], domain[index]),
        }
        for index in range(len(predicted_z))
    ]
    report = {
        "status": "COMPLETE",
        "method": "M4",
        "split": "modeling_180",
        "model_sha256": sha256(MODEL),
        "prediction_sha256": sha256(PREDICTION),
        "ground_truth_sha256": sha256(GROUND_TRUTH),
        "registration": json.loads((EVAL / "registration.json").read_text()),
        "aggregate": metrics(predicted_z, truth_z, domain),
        "per_frame": rows,
    }
    (EVAL / "modeling_180/metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (EVAL / "modeling_180/per_frame.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
