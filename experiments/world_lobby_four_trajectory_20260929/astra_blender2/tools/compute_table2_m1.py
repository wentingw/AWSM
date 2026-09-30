"""Compute Table 2 M1 model-depth metrics from the Tables 9-11 Sim(3)."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from depth_math import metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prediction", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    prediction = np.load(args.prediction)
    ground_truth = np.load(args.ground_truth)
    if not np.array_equal(prediction["pixel_uv"], ground_truth["pixel_uv"]):
        raise ValueError("Prediction and GT pixel grids differ")
    if not np.array_equal(
        prediction["timestamps_ns"], ground_truth["timestamps_ns"]
    ):
        raise ValueError("Prediction and GT timestamps differ")
    predicted_z = prediction["prediction_z_m"]
    truth_z = ground_truth["truth_z_m"]
    domain = ground_truth["valid_domain"]
    aggregate = metrics(predicted_z, truth_z, domain)
    rows = [
        {
            "sample_index": index,
            "source_index": int(ground_truth["source_indices"][index]),
            "timestamp_ns": int(ground_truth["timestamps_ns"][index]),
            **metrics(predicted_z[index], truth_z[index], domain[index]),
        }
        for index in range(len(predicted_z))
    ]
    report = {
        "status": "COMPLETE_DIAGNOSTIC",
        "method": "M1",
        "split": "modeling_180",
        "table": 2,
        "metric": "Model depth AbsRel",
        "ranking_role": "GT-assisted Sim3 diagnostic; not native metric recovery",
        "registration": json.loads(args.registration.read_text()),
        "aggregate": aggregate,
        "per_frame": rows,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.out / "per_frame.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
