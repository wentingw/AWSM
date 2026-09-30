#!/usr/bin/env python3
"""Select ten position-uniform views with broad observed-surface coverage."""
from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np

from depth_pipeline import BASE, atomic_json, calibration_matrix, pose_lookup, sha256


SAMPLE_MANIFEST = BASE / "data/depth_samples/modeling_180.json"
OUTPUT = BASE / "fixed_check_views"
GT_CACHE = BASE / "evaluation/depth/gt/modeling_180/gt_depth_modeling_180.npz"
ANCHOR_COUNT = 10
VOXEL_SIZE_M = 0.25


def circular_distance(values: np.ndarray, targets: np.ndarray, period: float) -> np.ndarray:
    delta = np.abs(values[:, None] - targets[None, :])
    return np.minimum(delta, period - delta)


def observed_surface_voxels(
    poses: np.ndarray, truth: np.ndarray, uv: np.ndarray
) -> tuple[list[set[tuple[int, int, int]]], set[tuple[int, int, int]]]:
    intrinsic, _ = calibration_matrix()
    rays = np.column_stack(
        [
            (uv[:, 0] - intrinsic[0, 2]) / intrinsic[0, 0],
            (uv[:, 1] - intrinsic[1, 2]) / intrinsic[1, 1],
            np.ones(len(uv)),
        ]
    )
    per_frame = []
    universe: set[tuple[int, int, int]] = set()
    for pose, frame_depth in zip(poses, truth):
        valid = (
            np.isfinite(frame_depth)
            & (frame_depth >= 0.1)
            & (frame_depth <= 30.0)
        )
        camera_points = rays[valid] * frame_depth[valid, None]
        world_points = camera_points @ pose[:3, :3].T + pose[:3, 3]
        quantized = np.unique(
            np.floor(world_points / VOXEL_SIZE_M).astype(np.int32), axis=0
        )
        frame_voxels = {tuple(int(item) for item in row) for row in quantized}
        per_frame.append(frame_voxels)
        universe.update(frame_voxels)
    return per_frame, universe


def choose_views(
    arcs: np.ndarray,
    total_length: float,
    frame_voxels: list[set[tuple[int, int, int]]],
) -> tuple[np.ndarray, float, int]:
    spacing = total_length / ANCHOR_COUNT
    phases = np.unique(np.mod(arcs, spacing))
    best: (
        tuple[tuple[int, float, float, tuple[int, ...]], np.ndarray, float, int]
        | None
    ) = None
    for phase in phases:
        targets = np.mod(phase + np.arange(ANCHOR_COUNT) * spacing, total_length)
        distances = circular_distance(arcs, targets, total_length)
        selected = np.asarray(
            [
                min(
                    range(len(arcs)),
                    key=lambda index: (float(distances[index, target]), index),
                )
                for target in range(ANCHOR_COUNT)
            ],
            dtype=int,
        )
        if len(np.unique(selected)) != ANCHOR_COUNT:
            continue
        selected_arcs = np.sort(arcs[selected])
        gaps = np.diff(np.r_[selected_arcs, selected_arcs[0] + total_length])
        errors = gaps - spacing
        visible = set().union(*(frame_voxels[int(index)] for index in selected))
        objective = (
            -len(visible),
            float(np.max(np.abs(errors))),
            float(np.sqrt(np.mean(errors**2))),
            tuple(int(index) for index in sorted(selected)),
        )
        if best is None or objective < best[0]:
            best = (objective, selected, float(phase), len(visible))
    if best is None:
        raise RuntimeError("failed to find five unique closed-loop views")
    return np.sort(best[1]), best[2], best[3]


def extend_to_full_coverage(
    anchors: np.ndarray,
    arcs: np.ndarray,
    total_length: float,
    frame_voxels: list[set[tuple[int, int, int]]],
    universe: set[tuple[int, int, int]],
) -> tuple[np.ndarray, list[dict]]:
    selected = [int(index) for index in anchors]
    covered = set().union(*(frame_voxels[index] for index in selected))
    trace = []
    while covered != universe:
        uncovered = universe - covered
        candidates = [index for index in range(len(arcs)) if index not in selected]
        ranked = []
        for index in candidates:
            gain = len(frame_voxels[index] & uncovered)
            if not gain:
                continue
            selected_arcs = arcs[np.asarray(selected, dtype=int)]
            distances = np.abs(selected_arcs - arcs[index])
            circular = np.minimum(distances, total_length - distances)
            nearest_selected_m = float(circular.min()) if len(circular) else total_length
            ranked.append((gain, nearest_selected_m, -index, index))
        if not ranked:
            raise RuntimeError(f"cannot cover {len(uncovered)} observed voxels")
        gain, nearest_selected_m, _, index = max(ranked)
        selected.append(index)
        covered.update(frame_voxels[index])
        trace.append(
            {
                "sample_index": index,
                "new_voxels": gain,
                "nearest_previous_view_m": nearest_selected_m,
                "cumulative_coverage": len(covered) / len(universe),
            }
        )
    return np.asarray(sorted(selected), dtype=int), trace


def prune_redundant_views(
    selected: np.ndarray,
    anchors: np.ndarray,
    arcs: np.ndarray,
    total_length: float,
    frame_voxels: list[set[tuple[int, int, int]]],
) -> tuple[np.ndarray, list[int]]:
    kept = {int(index) for index in selected}
    protected = {int(index) for index in anchors}
    counts = Counter(
        voxel for index in kept for voxel in frame_voxels[index]
    )
    removed = []
    while True:
        removable = [
            index
            for index in kept - protected
            if all(counts[voxel] > 1 for voxel in frame_voxels[index])
        ]
        if not removable:
            break
        ranked = []
        for index in removable:
            others = np.asarray(sorted(kept - {index}), dtype=int)
            distances = np.abs(arcs[others] - arcs[index])
            nearest = float(np.minimum(distances, total_length - distances).min())
            ranked.append((-nearest, len(frame_voxels[index]), index))
        _, _, index = min(ranked)
        kept.remove(index)
        removed.append(index)
        for voxel in frame_voxels[index]:
            counts[voxel] -= 1
    return np.asarray(sorted(kept), dtype=int), removed


def main() -> None:
    samples = json.loads(SAMPLE_MANIFEST.read_text())
    frames = samples["frames"]
    timestamps = [int(frame["timestamp_ns"]) for frame in frames]
    poses, pose_source = pose_lookup("M4", timestamps)
    positions = poses[:, :3, 3]
    gt = np.load(GT_CACHE)
    truth = np.asarray(gt["truth_z_m"], dtype=np.float32)
    uv = np.asarray(gt["pixel_uv"], dtype=np.float64)
    if truth.shape != (len(frames), len(uv)):
        raise ValueError(f"unexpected GT depth shape {truth.shape}")
    frame_voxels, observed_universe = observed_surface_voxels(poses, truth, uv)

    segment_lengths = np.linalg.norm(np.roll(positions, -1, axis=0) - positions, axis=1)
    if not np.all(np.isfinite(segment_lengths)) or not np.all(segment_lengths >= 0):
        raise ValueError("invalid GT camera path")
    total_length = float(segment_lengths.sum())
    if total_length <= 0:
        raise ValueError("degenerate GT camera loop")
    arcs = np.r_[0.0, np.cumsum(segment_lengths[:-1])]
    anchors, phase, _ = choose_views(
        arcs, total_length, frame_voxels
    )
    selected = anchors
    coverage_trace: list[dict] = []
    pruned_views: list[int] = []
    visible_voxels = set().union(*(frame_voxels[int(index)] for index in selected))
    visible_voxel_count = len(visible_voxels)

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    selected_arcs = arcs[selected]
    ordered_arcs = np.sort(selected_arcs)
    circular_gaps = np.diff(np.r_[ordered_arcs, ordered_arcs[0] + total_length])
    records = []
    for order, sample_index in enumerate(selected):
        frame = frames[int(sample_index)]
        source = Path(frame["image"])
        destination = OUTPUT / (
            f"view_{order:02d}_sample_{sample_index:04d}"
            f"_source_{int(frame['source_index']):04d}{source.suffix.lower()}"
        )
        shutil.copy2(source, destination)
        records.append(
            {
                "view_order": order,
                "sample_index": int(sample_index),
                "source_index": int(frame["source_index"]),
                "timestamp_ns": int(frame["timestamp_ns"]),
                "image": destination.name,
                "image_sha256": sha256(destination),
                "closed_loop_arclength_fraction": float(arcs[sample_index] / total_length),
            }
        )

    manifest = {
        "schema_version": 1,
        "status": "COMPLETE",
        "purpose": "future visual check renders; not used by the already frozen run",
        "selection": (
            "select exactly ten position-uniform closed-loop views; among all "
            "deterministic equal-arclength phases, maximize union coverage of the "
            "scene surface observed by all 180 GT depth views, then minimize gap error"
        ),
        "selection_scope": (
            "coordinator-only GT pose used to choose frame identities; pose matrices "
            "are not copied into this view package"
        ),
        "sample_manifest": str(SAMPLE_MANIFEST),
        "sample_manifest_sha256": sha256(SAMPLE_MANIFEST),
        "pose_source": str(pose_source),
        "pose_source_sha256": sha256(pose_source),
        "gt_depth_cache": str(GT_CACHE),
        "gt_depth_cache_sha256": sha256(GT_CACHE),
        "anchor_count": ANCHOR_COUNT,
        "anchor_sample_indices": [int(index) for index in anchors],
        "view_count": len(selected),
        "loop_length_m": total_length,
        "target_gap_m": total_length / len(selected),
        "selection_phase_m": phase,
        "actual_circular_gaps_m": [float(value) for value in circular_gaps],
        "max_gap_error_m": float(
            np.max(np.abs(circular_gaps - total_length / len(selected)))
        ),
        "coverage_definition": (
            "union of 0.25 m world-space surface voxels hit by the selected "
            "GT depth views divided by the union hit by all 180 modeling views"
        ),
        "coverage_limit": (
            "covers the scene surface observable in the 180-view input, not hidden "
            "or fully occluded GT surfaces"
        ),
        "surface_voxel_size_m": VOXEL_SIZE_M,
        "observed_surface_voxels_all_180": len(observed_universe),
        "observed_surface_voxels_selected_views": visible_voxel_count,
        "observed_surface_coverage": (
            visible_voxel_count / len(observed_universe)
            if observed_universe
            else 0.0
        ),
        "views": records,
    }
    atomic_json(OUTPUT / "manifest.json", manifest)
    (OUTPUT / "README.md").write_text(
        "# Fixed visual check views\n\n"
        f"{len(selected)} RGB views selected at approximately equal 3D arclength "
        "intervals on the closed trajectory, with deterministic phase chosen for "
        "maximum union coverage of 0.25 m scene-surface voxels observable in all "
        "180 GT depth views. This does not claim visibility of hidden or fully "
        "occluded surfaces. These files define a revised protocol for a future "
        "rerun; the already frozen M1–M4 models used the historical "
        "0/45/90/135/179 checks.\n"
    )
    print(json.dumps({"selected_sample_indices": selected.tolist(), **manifest}, indent=2))


if __name__ == "__main__":
    main()
