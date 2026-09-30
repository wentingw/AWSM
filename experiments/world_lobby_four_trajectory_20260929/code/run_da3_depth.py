#!/usr/bin/env python3
"""Run pose-conditioned Depth Anything v3 in resumable four-view windows."""
from __future__ import annotations

import argparse
import functools
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

from depth_pipeline import (
    BASE,
    METHODS,
    ROOT,
    atomic_json,
    atomic_npz,
    calibration_matrix,
    pose_lookup,
    sha256,
    windows,
)


VENDOR = ROOT / "reconstruction/vendor/vipe_official_95a8816"
DEFAULT_WEIGHTS = (
    ROOT
    / "reconstruction/runtime/huggingface/hub/"
    "models--depth-anything--DA3-GIANT/snapshots/"
    "7cd62ae9315b9dff094d2d300e4ad012640607dd/model.safetensors"
)
MODEL_REPO = "depth-anything/DA3-GIANT"
MODEL_NAME = "da3-giant"


@functools.lru_cache(maxsize=None)
def cached_sha256(path: Path) -> str:
    return sha256(path)


def normalize_optional(value: object, count: int, shape: tuple[int, ...]) -> np.ndarray:
    if value is None:
        return np.empty((count,) + shape, dtype=np.float32)
    result = np.asarray(value)
    if result.shape[0] != count:
        raise ValueError(f"optional DA3 output has unexpected shape {result.shape}")
    return result


def window_identity(
    method_id: str,
    split: str,
    manifest: dict,
    indices: list[int],
    pose_source: Path,
    weights: Path,
    process_res: int,
) -> dict:
    frames = [manifest["frames"][index] for index in indices]
    return {
        "method_id": method_id,
        "split": split,
        "sample_indices": indices,
        "timestamps_ns": [frame["timestamp_ns"] for frame in frames],
        "selection_sha256": manifest["selection_sha256"],
        "pose_source": str(pose_source),
        "pose_source_sha256": sha256(pose_source),
        "weights": str(weights),
        "weights_sha256": cached_sha256(weights),
        "model_repo": MODEL_REPO,
        "model_name": MODEL_NAME,
        "process_res": process_res,
        "window_size": len(indices),
        "align_to_input_ext_scale": True,
        "input_pose_convention": "OpenCV RDF camera-to-world",
        "da3_extrinsics_convention": "world-to-camera",
    }


def load_model(weights: Path, device: str):
    if str(VENDOR) not in sys.path:
        sys.path.insert(0, str(VENDOR))
    import torch
    from vipe.priors.depth.dav3.api import DepthAnything3

    model = DepthAnything3.from_pretrained(
        MODEL_REPO, model_name=MODEL_NAME, weights_path=str(weights)
    )
    model = model.to(torch.device(device)).eval()
    model.device = torch.device(device)
    return model


def infer_window(
    model,
    method_id: str,
    split: str,
    manifest: dict,
    indices: list[int],
    window_index: int,
    output: Path,
    pose_source: Path,
    weights: Path,
    process_res: int,
) -> dict:
    nominal_indices = list(indices)
    window_dir = output / f"window_{window_index:04d}"
    manifest_path = window_dir / "manifest.json"
    nominal_identity = window_identity(
        method_id,
        split,
        manifest,
        nominal_indices,
        pose_source,
        weights,
        process_res,
    )
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text())
        if (
            existing.get("status") == "COMPLETE"
            and existing.get("identity") == nominal_identity
        ):
            for record in existing["frames"]:
                if not (window_dir / record["data"]).is_file():
                    raise FileNotFoundError(window_dir / record["data"])
            return existing
    nominal_timestamps = [
        manifest["frames"][index]["timestamp_ns"] for index in nominal_indices
    ]
    nominal_poses, _ = pose_lookup(method_id, nominal_timestamps)
    centers = nominal_poses[:, :3, 3]
    baseline = float(
        np.max(np.linalg.norm(centers[:, None] - centers[None, :], axis=-1))
    )
    baseline_fallback = None
    if baseline <= 1e-5:
        all_timestamps = [frame["timestamp_ns"] for frame in manifest["frames"]]
        all_poses, _ = pose_lookup(method_id, all_timestamps)
        distances = np.linalg.norm(
            all_poses[:, :3, 3] - centers.mean(axis=0), axis=1
        )
        distances[nominal_indices] = -np.inf
        anchor = int(np.argmax(distances))
        if not np.isfinite(distances[anchor]) or distances[anchor] <= 1e-5:
            raise ValueError("no non-degenerate pose anchor exists for DA3 scale")
        replace = -1 if nominal_indices[0] == 0 else 0
        indices = list(nominal_indices)
        replaced = indices[replace]
        indices[replace] = anchor
        baseline_fallback = {
            "reason": "nominal window camera centers have zero baseline",
            "nominal_indices": nominal_indices,
            "replaced_sample_index": replaced,
            "anchor_sample_index": anchor,
            "anchor_distance_m": float(distances[anchor]),
        }
    frames = [manifest["frames"][index] for index in indices]
    timestamps = [frame["timestamp_ns"] for frame in frames]
    camera_to_world, _ = pose_lookup(method_id, timestamps)
    world_to_camera = np.linalg.inv(camera_to_world)
    intrinsic, _ = calibration_matrix()
    intrinsics = np.broadcast_to(intrinsic, (len(indices), 3, 3)).copy()
    identity = window_identity(
        method_id, split, manifest, indices, pose_source, weights, process_res
    )
    if manifest_path.is_file():
        existing = json.loads(manifest_path.read_text())
        if existing.get("status") == "COMPLETE" and existing.get("identity") == identity:
            for record in existing["frames"]:
                if not (window_dir / record["data"]).is_file():
                    raise FileNotFoundError(window_dir / record["data"])
            return existing
        raise RuntimeError(f"incompatible existing window {window_dir}")

    prediction = model.inference(
        [frame["image"] for frame in frames],
        extrinsics=world_to_camera,
        intrinsics=intrinsics,
        align_to_input_ext_scale=True,
        process_res=process_res,
        process_res_method="upper_bound_resize",
    )
    depth = np.asarray(prediction.depth, dtype=np.float32)
    if depth.ndim == 2:
        depth = depth[None]
    if depth.shape[0] != len(indices):
        raise ValueError(f"DA3 depth shape {depth.shape} does not match window")
    if not np.isfinite(depth).any() or not np.any(depth > 0):
        raise ValueError("DA3 returned no finite positive depth")
    height, width = depth.shape[-2:]
    confidence = normalize_optional(
        prediction.conf, len(indices), (height, width)
    ).astype(np.float32)
    sky = normalize_optional(prediction.sky, len(indices), (height, width)).astype(
        bool
    )
    output_intrinsics = normalize_optional(
        prediction.intrinsics, len(indices), (3, 3)
    ).astype(np.float32)
    output_extrinsics = normalize_optional(
        prediction.extrinsics, len(indices), (3, 4)
    ).astype(np.float32)
    valid = np.isfinite(depth) & (depth > 0)
    if prediction.sky is not None:
        valid &= ~sky
    processed = (
        np.asarray(prediction.processed_images)
        if prediction.processed_images is not None
        else np.empty((len(indices), height, width, 3), dtype=np.uint8)
    )
    scale_factor = (
        np.asarray(prediction.scale_factor)
        if prediction.scale_factor is not None
        else np.asarray(np.nan)
    )

    records = []
    for local_index, (sample_index, frame) in enumerate(zip(indices, frames)):
        data_name = f"frame_{sample_index:04d}.npz"
        atomic_npz(
            window_dir / data_name,
            compressed=False,
            depth_z_m=depth[local_index],
            intrinsics=output_intrinsics[local_index],
            valid_mask=valid[local_index],
            confidence=confidence[local_index],
            sky=sky[local_index],
            input_camera_to_world=camera_to_world[local_index].astype(np.float32),
            input_world_to_camera=world_to_camera[local_index].astype(np.float32),
            predicted_world_to_camera=output_extrinsics[local_index],
            processed_rgb=processed[local_index],
            scale_factor=scale_factor,
            timestamp_ns=np.asarray(frame["timestamp_ns"], dtype=np.int64),
            source_index=np.asarray(frame["source_index"], dtype=np.int64),
            sample_index=np.asarray(sample_index, dtype=np.int64),
        )
        records.append(
            {
                "sample_index": sample_index,
                "source_index": frame["source_index"],
                "timestamp_ns": frame["timestamp_ns"],
                "local_index": local_index,
                "centrality": min(local_index, len(indices) - 1 - local_index),
                "data": data_name,
                "data_sha256": sha256(window_dir / data_name),
                "depth_shape": [height, width],
                "valid_fraction": float(valid[local_index].mean()),
            }
        )
    result = {
        "schema_version": 1,
        "status": "COMPLETE",
        "identity": identity,
        "method": METHODS[method_id],
        "window_index": window_index,
        "nominal_sample_indices": nominal_indices,
        "baseline_fallback": baseline_fallback,
        "depth_units": "metres",
        "depth_axis": "camera optical z",
        "model_is_metric": int(getattr(prediction, "is_metric", 0)),
        "frames": records,
    }
    atomic_json(manifest_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHODS), required=True)
    parser.add_argument("--split", choices=["modeling_180", "eval_500"], required=True)
    parser.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--process-res",
        type=int,
        default=392,
        help="392 fits four DA3-GIANT views on the available 10 GB GPU",
    )
    parser.add_argument("--window-index", type=int)
    parser.add_argument("--limit-windows", type=int)
    args = parser.parse_args()
    if not args.weights.is_file():
        raise FileNotFoundError(args.weights)

    manifest_path = BASE / f"data/depth_samples/{args.split}.json"
    manifest = json.loads(manifest_path.read_text())
    schedule = windows(manifest["frame_count"])
    selected = list(enumerate(schedule))
    if args.window_index is not None:
        if args.window_index < 0 or args.window_index >= len(schedule):
            raise ValueError("window index outside schedule")
        selected = [(args.window_index, schedule[args.window_index])]
    if args.limit_windows is not None:
        selected = selected[: args.limit_windows]
    timestamps = [frame["timestamp_ns"] for frame in manifest["frames"]]
    _, pose_source = pose_lookup(args.method, timestamps)
    output = (
        BASE
        / "depth"
        / METHODS[args.method]["slug"]
        / args.split
        / "windows"
    )
    output.mkdir(parents=True, exist_ok=True)
    weights = args.weights.expanduser()
    model = load_model(weights, args.device)
    started = time.monotonic()
    completed = []
    for window_index, indices in selected:
        result = infer_window(
            model,
            args.method,
            args.split,
            manifest,
            indices,
            window_index,
            output,
            pose_source,
            weights,
            args.process_res,
        )
        completed.append(result["window_index"])
        print(
            json.dumps(
                {
                    "method": args.method,
                    "split": args.split,
                    "window": window_index,
                    "completed": len(completed),
                    "requested": len(selected),
                }
            ),
            flush=True,
        )
    summary = {
        "status": "COMPLETE" if len(selected) == len(schedule) else "PARTIAL",
        "method_id": args.method,
        "split": args.split,
        "windows_total": len(schedule),
        "windows_requested": len(selected),
        "windows_completed": completed,
        "seconds": time.monotonic() - started,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "weights": str(weights),
        "weights_sha256": cached_sha256(weights),
        "device": args.device,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    atomic_json(output.parent / "run_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
