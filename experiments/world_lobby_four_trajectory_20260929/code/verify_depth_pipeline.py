#!/usr/bin/env python3
"""Audit schedules, predictions, packets, GT caches, and depth metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from depth_pipeline import BASE, METHODS, atomic_json, sha256, windows


def verify_schedule() -> list[str]:
    checks = []
    manifests = {
        name: json.loads((BASE / f"data/depth_samples/{name}.json").read_text())
        for name in ("modeling_180", "eval_500")
    }
    if manifests["modeling_180"]["frame_count"] != 180:
        raise ValueError("modelling schedule is not 180 frames")
    if manifests["eval_500"]["frame_count"] != 500:
        raise ValueError("evaluation schedule is not 500 frames")
    indices = {
        name: {frame["source_index"] for frame in manifest["frames"]}
        for name, manifest in manifests.items()
    }
    if indices["modeling_180"] & indices["eval_500"]:
        raise ValueError("modelling and evaluation schedules overlap")
    for manifest in manifests.values():
        for frame in manifest["frames"]:
            image = Path(frame["image"])
            if sha256(image) != frame["image_sha256"]:
                raise ValueError(f"RGB hash mismatch: {image}")
    checks.append("180/500 schedules are disjoint and RGB hashes match")
    return checks


def verify_predictions(require_results: bool) -> list[str]:
    checks = []
    for method_id, method in METHODS.items():
        for split, count in (("modeling_180", 180), ("eval_500", 500)):
            root = BASE / "depth" / method["slug"] / split
            manifests = sorted((root / "windows").glob("window_*/manifest.json"))
            expected = len(windows(count))
            if len(manifests) != expected:
                if require_results:
                    raise ValueError(
                        f"{method_id}/{split} has {len(manifests)}/{expected} windows"
                    )
                continue
            for manifest_path in manifests:
                manifest = json.loads(manifest_path.read_text())
                if manifest["status"] != "COMPLETE":
                    raise ValueError(f"incomplete {manifest_path}")
                for frame in manifest["frames"]:
                    data = manifest_path.parent / frame["data"]
                    if sha256(data) != frame["data_sha256"]:
                        raise ValueError(f"prediction hash mismatch: {data}")
            consolidated = root / "consolidated/manifest.json"
            if not consolidated.is_file():
                if require_results:
                    raise FileNotFoundError(consolidated)
                continue
            value = json.loads(consolidated.read_text())
            if value["frame_count"] != count:
                raise ValueError(f"wrong consolidated count in {consolidated}")
            if split == "eval_500" and not value["evaluation_only"]:
                raise ValueError("500-frame outputs are not evaluation-only")
        packet_path = BASE / "packets" / method_id / "packet.json"
        if not packet_path.is_file():
            if require_results:
                raise FileNotFoundError(packet_path)
            continue
        packet = json.loads(packet_path.read_text())
        if packet["geometry_frames"] != 180 or packet["ground_truth_depth_used"]:
            raise ValueError(f"invalid packet {packet_path}")
        if method_id in {"M2", "M3"} and packet["ground_truth_pose_input"]:
            raise ValueError(f"GT pose leaked into {method_id}")
        if method_id == "M4" and not packet["ground_truth_pose_input"]:
            raise ValueError("M4 does not declare GT pose input")
    checks.append("available DA3 windows, consolidated outputs, and packets pass audit")
    return checks


def verify_evaluation(require_results: bool) -> list[str]:
    checks = []
    for split, count in (("modeling_180", 180), ("eval_500", 500)):
        gt = (
            BASE
            / "evaluation/depth/gt"
            / split
            / f"gt_depth_{split}.npz"
        )
        metrics = BASE / "evaluation/depth/metrics" / split / "metrics.json"
        if not gt.is_file() or not metrics.is_file():
            if require_results:
                raise FileNotFoundError(gt if not gt.is_file() else metrics)
            continue
        truth = np.load(gt)
        if truth["truth_z_m"].shape != (count, 19200):
            raise ValueError(f"unexpected GT shape in {gt}")
        report = json.loads(metrics.read_text())
        if report["frame_count"] != count or report["primary_scale_fit"]:
            raise ValueError(f"invalid metric protocol in {metrics}")
        for method_id in METHODS:
            primary = report["methods"][method_id]["primary_no_scale_fit"]
            for key in (
                "mae_m",
                "rmse_m",
                "absrel",
                "delta1",
                "delta2",
                "delta3",
                "valid_coverage",
                "missing_penalty_mae_m",
            ):
                if primary[key] is None or not np.isfinite(primary[key]):
                    raise ValueError(f"non-finite {method_id}/{split}/{key}")
    checks.append("available GT caches and 180/500 metric reports pass audit")
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-results", action="store_true")
    args = parser.parse_args()
    checks = []
    checks.extend(verify_schedule())
    checks.extend(verify_predictions(args.require_results))
    checks.extend(verify_evaluation(args.require_results))
    result = {
        "status": "PASS",
        "require_results": args.require_results,
        "checks": checks,
    }
    atomic_json(BASE / "evaluation/depth/verification.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
