#!/usr/bin/env python3
"""Create disjoint 180-frame modelling and 500-frame evaluation schedules."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from depth_pipeline import (
    BASE,
    CAMERA_CSV,
    METHODS,
    atomic_json,
    camera_rows,
    evenly_spaced_indices,
    load_pose_stream,
    sha256,
)


OUT = BASE / "data/depth_samples"


def selection_hash(indices: np.ndarray, timestamps: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.asarray(indices, dtype=np.int64).tobytes())
    digest.update(np.asarray(timestamps, dtype=np.int64).tobytes())
    return digest.hexdigest()


def build_manifest(name: str, selected: np.ndarray, rows: list[dict]) -> dict:
    records = []
    for sample_index, source_index in enumerate(selected):
        row = rows[int(source_index)]
        image = Path(row["image"])
        if not image.is_file():
            raise FileNotFoundError(image)
        records.append(
            {
                "sample_index": sample_index,
                "source_index": int(source_index),
                "timestamp_ns": int(row["timestamp_ns"]),
                "image": str(image),
                "image_sha256": sha256(image),
            }
        )
    timestamps = np.asarray([record["timestamp_ns"] for record in records])
    return {
        "schema_version": 1,
        "status": "COMPLETE",
        "name": name,
        "selection": "rounded linspace over eligible source indices",
        "frame_count": len(records),
        "common_source_range": [245, 4498],
        "camera_csv": str(CAMERA_CSV),
        "camera_csv_sha256": sha256(CAMERA_CSV),
        "selection_sha256": selection_hash(selected, timestamps),
        "methods": list(METHODS),
        "frames": records,
    }


def main() -> None:
    rows = camera_rows()
    session_timestamps = np.asarray([row["timestamp_ns"] for row in rows], dtype=np.int64)
    timestamp_sets = []
    pose_sources = {}
    for method_id in METHODS:
        timestamps, _, source = load_pose_stream(method_id)
        timestamp_sets.append(set(timestamps.tolist()))
        pose_sources[method_id] = {
            "path": str(source),
            "sha256": sha256(source),
            "timestamp_count": len(timestamps),
        }
    common = set.intersection(*timestamp_sets)
    eligible = np.asarray(
        [
            source_index
            for source_index, timestamp in enumerate(session_timestamps)
            if int(timestamp) in common
        ],
        dtype=np.int64,
    )
    if not np.array_equal(eligible, np.arange(245, 4499)):
        raise ValueError(
            f"unexpected common schedule {eligible[0]}..{eligible[-1]} ({len(eligible)})"
        )

    modelling = evenly_spaced_indices(eligible, 180)
    remainder = eligible[~np.isin(eligible, modelling)]
    evaluation = evenly_spaced_indices(remainder, 500)
    if np.intersect1d(modelling, evaluation).size:
        raise ValueError("modelling and evaluation schedules overlap")

    model_manifest = build_manifest("modeling_180", modelling, rows)
    eval_manifest = build_manifest("eval_500", evaluation, rows)
    for value in (model_manifest, eval_manifest):
        value["pose_sources"] = pose_sources
    atomic_json(OUT / "modeling_180.json", model_manifest)
    atomic_json(OUT / "eval_500.json", eval_manifest)
    summary = {
        "status": "COMPLETE",
        "eligible_frames": len(eligible),
        "eligible_source_range": [int(eligible[0]), int(eligible[-1])],
        "modeling_frames": len(modelling),
        "evaluation_frames": len(evaluation),
        "overlap": int(np.intersect1d(modelling, evaluation).size),
        "modeling_selection_sha256": model_manifest["selection_sha256"],
        "evaluation_selection_sha256": eval_manifest["selection_sha256"],
        "pose_sources": pose_sources,
    }
    atomic_json(OUT / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
