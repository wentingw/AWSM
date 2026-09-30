#!/usr/bin/env python3
"""Evaluate consolidated DA3 predictions against fixed GT optical-Z rays."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from depth_pipeline import (
    BASE,
    METHODS,
    atomic_json,
    atomic_npz,
    bilinear_sample,
    calibration_matrix,
    depth_metrics,
    sha256,
)


METRIC_KEYS = [
    "valid_coverage",
    "invalid_rate",
    "mae_m",
    "rmse_m",
    "absrel",
    "delta1",
    "delta2",
    "delta3",
    "missing_penalty_mae_m",
]


def bootstrap(values: np.ndarray, seed: int = 20260930, repeats: int = 2000) -> dict:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        return {"mean": None, "ci95": [None, None], "frames": 0}
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(values), size=(repeats, len(values)))
    means = values[draws].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci95": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        "frames": len(values),
        "repeats": repeats,
        "seed": seed,
    }


def sample_prediction(
    geometry: Path, uv: np.ndarray, original_intrinsic: np.ndarray
) -> np.ndarray:
    value = np.load(geometry)
    depth = np.asarray(value["depth_z_m"], dtype=float)
    valid = np.asarray(value["valid_mask"], dtype=bool)
    intrinsic = np.asarray(value["intrinsics"], dtype=float)
    rays = np.column_stack(
        [
            (uv[:, 0] - original_intrinsic[0, 2]) / original_intrinsic[0, 0],
            (uv[:, 1] - original_intrinsic[1, 2]) / original_intrinsic[1, 1],
            np.ones(len(uv)),
        ]
    )
    pixels = rays @ intrinsic.T
    x = pixels[:, 0] / pixels[:, 2]
    y = pixels[:, 1] / pixels[:, 2]
    prediction, supported = bilinear_sample(depth, x, y, valid)
    prediction[~supported] = np.nan
    return prediction


def method_predictions(method_id: str, split: str, uv: np.ndarray) -> tuple[np.ndarray, Path]:
    manifest_path = (
        BASE
        / "depth"
        / METHODS[method_id]["slug"]
        / split
        / "consolidated/manifest.json"
    )
    manifest = json.loads(manifest_path.read_text())
    intrinsic, _ = calibration_matrix()
    predictions = [
        sample_prediction(Path(frame["geometry"]), uv, intrinsic)
        for frame in manifest["frames"]
    ]
    return np.asarray(predictions, dtype=np.float32), manifest_path


def evaluate_method(
    method_id: str,
    split: str,
    prediction: np.ndarray,
    truth: np.ndarray,
    domain: np.ndarray,
    manifest_path: Path,
) -> dict:
    per_frame = [
        {
            "sample_index": index,
            **depth_metrics(prediction[index], truth[index], domain[index], 30.0),
        }
        for index in range(len(truth))
    ]
    scales = np.ones(len(truth), dtype=float)
    scaled = prediction.copy().astype(float)
    for index in range(len(truth)):
        good = (
            domain[index]
            & np.isfinite(prediction[index])
            & (prediction[index] >= 0.1)
            & (prediction[index] <= 30.0)
        )
        if good.any():
            scales[index] = float(
                np.median(truth[index][good] / prediction[index][good])
            )
            scaled[index] *= scales[index]
    scale_diagnostic = depth_metrics(scaled, truth, domain, 30.0)
    macro_bootstrap = {
        key: bootstrap(
            np.asarray(
                [
                    frame[key] if frame[key] is not None else np.nan
                    for frame in per_frame
                ]
            )
        )
        for key in METRIC_KEYS
    }
    return {
        "method_id": method_id,
        "split": split,
        "prediction_manifest": str(manifest_path),
        "prediction_manifest_sha256": sha256(manifest_path),
        "primary_no_scale_fit": depth_metrics(prediction, truth, domain, 30.0),
        "per_frame": per_frame,
        "macro_frame_bootstrap": macro_bootstrap,
        "median_scale_diagnostic": {
            "metrics": scale_diagnostic,
            "scale_median": float(np.median(scales)),
            "scale_p05": float(np.percentile(scales, 5)),
            "scale_p95": float(np.percentile(scales, 95)),
            "ranking_role": "diagnostic_only",
        },
    }


def paired_differences(reports: dict[str, dict]) -> dict:
    result = {}
    pairs = [("M2", "M3"), ("M2", "M4"), ("M3", "M4")]
    for left, right in pairs:
        result[f"{left}_minus_{right}"] = {}
        for key in METRIC_KEYS:
            left_values = np.asarray(
                [frame[key] for frame in reports[left]["per_frame"]], dtype=float
            )
            right_values = np.asarray(
                [frame[key] for frame in reports[right]["per_frame"]], dtype=float
            )
            result[f"{left}_minus_{right}"][key] = bootstrap(
                left_values - right_values
            )
    return result


def write_csv(path: Path, reports: dict[str, dict]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["method_id", "sample_index"] + METRIC_KEYS
    temporary = path.with_suffix(".csv.partial")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for method_id, report in reports.items():
            for frame in report["per_frame"]:
                writer.writerow(
                    {
                        "method_id": method_id,
                        "sample_index": frame["sample_index"],
                        **{key: frame[key] for key in METRIC_KEYS},
                    }
                )
    temporary.replace(path)


def plot_summary(path: Path, reports: dict[str, dict], split: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = list(reports)
    keys = ["absrel", "rmse_m", "delta1", "valid_coverage"]
    fig, axes = plt.subplots(1, len(keys), figsize=(14, 3.8), layout="constrained")
    for axis, key in zip(axes, keys):
        values = [reports[label]["primary_no_scale_fit"][key] for label in labels]
        axis.bar(labels, values)
        axis.set_title(key)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle(f"DA3 depth vs GT optical-Z: {split}")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["modeling_180", "eval_500"], required=True)
    args = parser.parse_args()
    gt_path = (
        BASE
        / "evaluation/depth/gt"
        / args.split
        / f"gt_depth_{args.split}.npz"
    )
    gt_manifest = gt_path.parent / "manifest.json"
    gt = np.load(gt_path)
    truth = np.asarray(gt["truth_z_m"], dtype=np.float32)
    uv = np.asarray(gt["pixel_uv"], dtype=float)
    domain = np.asarray(gt["valid_domain"], dtype=bool)
    reports = {}
    paired_arrays = {"ground_truth_z_m": truth, "pixel_uv": uv, "valid_domain": domain}
    for method_id in METHODS:
        prediction, manifest_path = method_predictions(method_id, args.split, uv)
        if prediction.shape != truth.shape:
            raise ValueError(
                f"{method_id} prediction {prediction.shape} != GT {truth.shape}"
            )
        reports[method_id] = evaluate_method(
            method_id,
            args.split,
            prediction,
            truth,
            domain,
            manifest_path,
        )
        paired_arrays[f"{method_id}_prediction_z_m"] = prediction
    output = BASE / "evaluation/depth/metrics" / args.split
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": 1,
        "status": "COMPLETE",
        "split": args.split,
        "frame_count": len(truth),
        "rays_per_frame": truth.shape[1],
        "depth_axis": "camera optical z",
        "units": "metres",
        "primary_scale_fit": False,
        "gt_domain": "finite optical-Z in [0.1, 30] m; prediction-independent",
        "missing_prediction_penalty_m": 30.0,
        "gt_cache": str(gt_path),
        "gt_cache_sha256": sha256(gt_path),
        "gt_manifest_sha256": sha256(gt_manifest),
        "methods": reports,
        "paired_macro_frame_differences": paired_differences(reports),
    }
    atomic_json(output / "metrics.json", result)
    atomic_npz(output / "paired_depth.npz", **paired_arrays)
    write_csv(output / "per_frame_metrics.csv", reports)
    plot_summary(output / "summary.png", reports, args.split)
    print(
        json.dumps(
            {
                method_id: report["primary_no_scale_fit"]
                for method_id, report in reports.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
