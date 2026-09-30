#!/usr/bin/env python3
"""Consolidate overlapping DA3 windows and build modelling packets."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np

from depth_pipeline import (
    BASE,
    METHODS,
    atomic_json,
    choose_central_observations,
    pose_lookup,
    sha256,
    windows,
)


def consolidate(method_id: str, split: str) -> dict:
    sample_manifest_path = BASE / f"data/depth_samples/{split}.json"
    sample_manifest = json.loads(sample_manifest_path.read_text())
    window_root = (
        BASE / "depth" / METHODS[method_id]["slug"] / split / "windows"
    )
    expected_windows = windows(sample_manifest["frame_count"])
    observations = []
    window_hashes = []
    for window_index in range(len(expected_windows)):
        manifest_path = window_root / f"window_{window_index:04d}/manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(manifest_path)
        value = json.loads(manifest_path.read_text())
        if value.get("status") != "COMPLETE":
            raise ValueError(f"incomplete window {manifest_path}")
        if value["window_index"] != window_index:
            raise ValueError(f"window index mismatch in {manifest_path}")
        window_hashes.append(sha256(manifest_path))
        for frame in value["frames"]:
            record = dict(frame)
            record["window_index"] = window_index
            record["source_path"] = str(manifest_path.parent / frame["data"])
            observations.append(record)
    chosen = choose_central_observations(observations)
    if sorted(chosen) != list(range(sample_manifest["frame_count"])):
        raise ValueError("consolidated schedule is incomplete")

    output = BASE / "depth" / METHODS[method_id]["slug"] / split / "consolidated"
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    for sample_index in range(sample_manifest["frame_count"]):
        source = Path(chosen[sample_index]["source_path"])
        target = output / f"{sample_index:04d}_geometry.npz"
        temporary = target.with_suffix(".npz.partial")
        shutil.copyfile(source, temporary)
        temporary.replace(target)
        sample = sample_manifest["frames"][sample_index]
        value = np.load(target)
        if int(value["timestamp_ns"]) != sample["timestamp_ns"]:
            raise ValueError("consolidated timestamp mismatch")
        frames.append(
            {
                "sample_index": sample_index,
                "source_index": sample["source_index"],
                "timestamp_ns": sample["timestamp_ns"],
                "rgb": sample["image"],
                "rgb_sha256": sample["image_sha256"],
                "geometry": str(target),
                "geometry_sha256": sha256(target),
                "selected_window": chosen[sample_index]["window_index"],
                "window_local_index": chosen[sample_index]["local_index"],
                "window_centrality": chosen[sample_index]["centrality"],
                "depth_shape": chosen[sample_index]["depth_shape"],
                "valid_fraction": chosen[sample_index]["valid_fraction"],
            }
        )
    manifest = {
        "schema_version": 1,
        "status": "COMPLETE",
        "method_id": method_id,
        "method": METHODS[method_id],
        "split": split,
        "frame_count": len(frames),
        "selection_rule": "maximum window centrality; earliest window breaks ties",
        "sample_manifest": str(sample_manifest_path),
        "sample_manifest_sha256": sha256(sample_manifest_path),
        "window_manifest_sha256": window_hashes,
        "depth_units": "metres",
        "depth_axis": "camera optical z",
        "evaluation_only": split == "eval_500",
        "frames": frames,
    }
    manifest_path = output / "manifest.json"
    atomic_json(manifest_path, manifest)
    return manifest


def build_packet(method_id: str, manifest: dict) -> dict:
    if manifest["split"] != "modeling_180":
        raise ValueError("only the modelling split may become an Astra packet")
    timestamps = [frame["timestamp_ns"] for frame in manifest["frames"]]
    poses, pose_source = pose_lookup(method_id, timestamps)
    frames = []
    for frame, pose in zip(manifest["frames"], poses):
        record = dict(frame)
        record["camera_to_world"] = pose.tolist()
        record["pose_convention"] = "OpenCV RDF camera-to-world"
        record["units"] = "metres"
        frames.append(record)
    packet = {
        "schema_version": 1,
        "method_id": method_id,
        "status": "COMPLETE",
        "geometry_frames": len(frames),
        "rgb_frames": len(frames),
        "depth_source": "pose-conditioned Depth Anything v3 giant; 4-view windows overlap 2; aligned to native metric input-pose scale",
        "pose_source": str(pose_source),
        "pose_source_sha256": sha256(pose_source),
        "coordinate_frame": "native method camera world; no GT alignment",
        "allowed_inputs": (
            "sampled RGB + fixed intrinsics + native method poses + DA3 prediction"
        ),
        "ground_truth_pose_input": bool(METHODS[method_id]["uses_gt_pose"]),
        "ground_truth_depth_used": False,
        "evaluation_outputs_opened": False,
        "selection_rule": manifest["selection_rule"],
        "frames": frames,
    }
    output = BASE / "packets" / method_id / "packet.json"
    atomic_json(output, packet)
    return packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=sorted(METHODS), required=True)
    parser.add_argument(
        "--split", choices=["modeling_180", "eval_500", "both"], default="both"
    )
    args = parser.parse_args()
    splits = (
        ["modeling_180", "eval_500"] if args.split == "both" else [args.split]
    )
    result = {}
    for split in splits:
        manifest = consolidate(args.method, split)
        result[split] = {
            "frames": manifest["frame_count"],
            "manifest": str(
                BASE
                / "depth"
                / METHODS[args.method]["slug"]
                / split
                / "consolidated/manifest.json"
            ),
        }
        if split == "modeling_180":
            packet = build_packet(args.method, manifest)
            result[split]["packet_frames"] = packet["geometry_frames"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
