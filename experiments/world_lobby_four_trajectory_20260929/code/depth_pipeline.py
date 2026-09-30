#!/usr/bin/env python3
"""Shared contracts for the World Lobby DA3 depth pipeline."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "world_lobby_four_trajectory_20260929"
SESSION = ROOT / "vio-reconstruction/sessions/lobby_orb_success_20260929T123153"
ORB_CAMERA = ROOT / "stable_orbit_orb_success_20260929/frozen/camera.npz"
VIPE_CAMERA = BASE / "frozen/vipe_default/camera.npz"
GT_CAMERA = SESSION / "ground_truth/camera.csv"
CAMERA_CSV = SESSION / "inputs/cam0/data.csv"
CALIBRATION = SESSION / "inputs/calibration.json"

METHODS = {
    "M2": {"slug": "m2_vipe", "pose_kind": "vipe", "uses_gt_pose": False},
    "M3": {"slug": "m3_orb", "pose_kind": "orb", "uses_gt_pose": False},
    "M4": {"slug": "m4_gt", "pose_kind": "gt", "uses_gt_pose": True},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def atomic_npz(
    path: Path, *, compressed: bool = True, **arrays: np.ndarray
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("wb") as handle:
        writer = np.savez_compressed if compressed else np.savez
        writer(handle, **arrays)
    temporary.replace(path)


def camera_rows() -> list[dict]:
    rows = []
    with CAMERA_CSV.open(newline="") as handle:
        for row in csv.reader(handle):
            if not row or row[0].startswith("#"):
                continue
            source_index = len(rows)
            timestamp_ns = int(row[0])
            image = SESSION / "inputs/cam0/data" / row[1]
            rows.append(
                {
                    "source_index": source_index,
                    "timestamp_ns": timestamp_ns,
                    "image": str(image),
                }
            )
    if len(rows) != 4499:
        raise ValueError(f"expected 4499 camera rows, got {len(rows)}")
    timestamps = np.asarray([row["timestamp_ns"] for row in rows], dtype=np.int64)
    if not np.all(np.diff(timestamps) > 0):
        raise ValueError("camera timestamps are not strictly increasing")
    return rows


def calibration_matrix() -> tuple[np.ndarray, dict]:
    value = json.loads(CALIBRATION.read_text())
    fx, fy, cx, cy = value["intrinsics"]
    matrix = np.asarray([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])
    return matrix, value


def _validate_poses(timestamps: np.ndarray, poses: np.ndarray) -> None:
    if poses.shape != (len(timestamps), 4, 4):
        raise ValueError(f"invalid pose shape {poses.shape}")
    if not np.isfinite(poses).all() or not np.all(np.diff(timestamps) > 0):
        raise ValueError("poses or timestamps are invalid")
    rotation = poses[:, :3, :3]
    if not np.allclose(
        rotation @ rotation.transpose(0, 2, 1), np.eye(3), atol=2e-4
    ):
        raise ValueError("camera rotations are not orthonormal")
    if not np.allclose(np.linalg.det(rotation), 1.0, atol=2e-4):
        raise ValueError("camera rotations are not proper")


def load_pose_stream(method_id: str) -> tuple[np.ndarray, np.ndarray, Path]:
    if method_id not in METHODS:
        raise ValueError(f"unknown method {method_id}")
    kind = METHODS[method_id]["pose_kind"]
    if kind in {"vipe", "orb"}:
        path = VIPE_CAMERA if kind == "vipe" else ORB_CAMERA
        value = np.load(path)
        timestamps = np.asarray(value["timestamps_ns"], dtype=np.int64)
        poses = np.asarray(value["camera_to_world"], dtype=np.float64)
    else:
        path = GT_CAMERA
        rows = []
        with path.open(newline="") as handle:
            for row in csv.reader(handle):
                if not row or row[0].startswith("#"):
                    continue
                rows.append(row)
        timestamps = np.asarray([int(row[0]) for row in rows], dtype=np.int64)
        values = np.asarray([[float(item) for item in row[1:]] for row in rows])
        poses = np.broadcast_to(np.eye(4), (len(rows), 4, 4)).copy()
        quaternion = values[:, 3:7]
        norm = np.linalg.norm(quaternion, axis=1)
        if np.any(norm < 1e-12):
            raise ValueError("GT contains a zero quaternion")
        x, y, z, w = (quaternion / norm[:, None]).T
        poses[:, :3, :3] = np.stack(
            [
                1 - 2 * (y * y + z * z),
                2 * (x * y - z * w),
                2 * (x * z + y * w),
                2 * (x * y + z * w),
                1 - 2 * (x * x + z * z),
                2 * (y * z - x * w),
                2 * (x * z - y * w),
                2 * (y * z + x * w),
                1 - 2 * (x * x + y * y),
            ],
            axis=1,
        ).reshape(-1, 3, 3)
        poses[:, :3, 3] = values[:, :3]
    _validate_poses(timestamps, poses)
    return timestamps, poses, path


def pose_lookup(method_id: str, wanted: Iterable[int]) -> tuple[np.ndarray, Path]:
    timestamps, poses, source = load_pose_stream(method_id)
    lookup = {int(timestamp): index for index, timestamp in enumerate(timestamps)}
    wanted_array = np.asarray(list(wanted), dtype=np.int64)
    missing = [int(timestamp) for timestamp in wanted_array if int(timestamp) not in lookup]
    if missing:
        raise ValueError(f"{method_id} misses {len(missing)} requested poses")
    take = np.asarray([lookup[int(timestamp)] for timestamp in wanted_array])
    return poses[take], source


def evenly_spaced_indices(candidates: np.ndarray, count: int) -> np.ndarray:
    candidates = np.asarray(candidates, dtype=np.int64)
    if count <= 0 or count > len(candidates):
        raise ValueError("sample count is outside candidate range")
    positions = np.rint(np.linspace(0, len(candidates) - 1, count)).astype(int)
    selected = candidates[positions]
    if len(np.unique(selected)) != count:
        raise ValueError("even sampling produced duplicate source indices")
    return selected


def windows(frame_count: int, size: int = 4, stride: int = 2) -> list[list[int]]:
    if frame_count < size or size < 2 or stride < 1:
        raise ValueError("invalid window configuration")
    starts = list(range(0, frame_count - size + 1, stride))
    last = frame_count - size
    if starts[-1] != last:
        starts.append(last)
    return [list(range(start, start + size)) for start in starts]


def choose_central_observations(records: Iterable[dict]) -> dict[int, dict]:
    chosen: dict[int, dict] = {}
    for record in records:
        key = int(record["sample_index"])
        rank = int(record["centrality"])
        window_index = int(record["window_index"])
        previous = chosen.get(key)
        if previous is None or (rank, -window_index) > (
            int(previous["centrality"]),
            -int(previous["window_index"]),
        ):
            chosen[key] = record
    return chosen


def bilinear_sample(
    image: np.ndarray, x: np.ndarray, y: np.ndarray, valid: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    image = np.asarray(image, dtype=float)
    height, width = image.shape
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1 = x0 + 1
    y1 = y0 + 1
    inside = (x0 >= 0) & (y0 >= 0) & (x1 < width) & (y1 < height)
    result = np.full(x.shape, np.nan, dtype=float)
    support = inside.copy()
    if valid is not None:
        mask = np.asarray(valid, dtype=bool)
        support[inside] &= (
            mask[y0[inside], x0[inside]]
            & mask[y0[inside], x1[inside]]
            & mask[y1[inside], x0[inside]]
            & mask[y1[inside], x1[inside]]
        )
    use = np.flatnonzero(support)
    if len(use):
        dx = x[use] - x0[use]
        dy = y[use] - y0[use]
        result[use] = (
            image[y0[use], x0[use]] * (1 - dx) * (1 - dy)
            + image[y0[use], x1[use]] * dx * (1 - dy)
            + image[y1[use], x0[use]] * (1 - dx) * dy
            + image[y1[use], x1[use]] * dx * dy
        )
    support &= np.isfinite(result)
    return result, support


def depth_metrics(
    prediction: np.ndarray,
    truth: np.ndarray,
    domain: np.ndarray | None = None,
    missing_penalty_m: float = 30.0,
) -> dict:
    prediction = np.asarray(prediction, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if prediction.shape != truth.shape:
        raise ValueError("prediction and truth shapes differ")
    selected = np.isfinite(truth) & (truth >= 0.1) & (truth <= 30.0)
    if domain is not None:
        selected &= np.asarray(domain, dtype=bool)
    valid = selected & np.isfinite(prediction) & (prediction >= 0.1) & (
        prediction <= 30.0
    )
    if not selected.any():
        raise ValueError("no valid GT depth")
    error = np.abs(prediction[valid] - truth[valid])
    ratio = np.maximum(
        prediction[valid] / truth[valid], truth[valid] / prediction[valid]
    )
    penalized = np.full(int(selected.sum()), float(missing_penalty_m))
    penalized[np.asarray(valid[selected], dtype=bool)] = np.abs(
        prediction[selected][valid[selected]] - truth[selected][valid[selected]]
    )
    return {
        "pixels_domain": int(selected.sum()),
        "pixels_valid": int(valid.sum()),
        "valid_coverage": float(valid.sum() / selected.sum()),
        "invalid_rate": float(1.0 - valid.sum() / selected.sum()),
        "mae_m": float(error.mean()) if len(error) else None,
        "rmse_m": float(np.sqrt(np.mean(error**2))) if len(error) else None,
        "absrel": float(np.mean(error / truth[valid])) if len(error) else None,
        "delta1": float(np.mean(ratio < 1.25)) if len(error) else 0.0,
        "delta2": float(np.mean(ratio < 1.25**2)) if len(error) else 0.0,
        "delta3": float(np.mean(ratio < 1.25**3)) if len(error) else 0.0,
        "missing_penalty_mae_m": float(penalized.mean()),
    }
