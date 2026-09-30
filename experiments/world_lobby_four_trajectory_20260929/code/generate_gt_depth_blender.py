#!/usr/bin/env python3
"""Generate exact GT optical-Z samples by ray casting the World Lobby USD."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from depth_pipeline import (  # noqa: E402
    BASE,
    ROOT,
    atomic_json,
    atomic_npz,
    calibration_matrix,
    pose_lookup,
    sha256,
)


GT_USD = ROOT / "drone-web/scenes/world_lobby/lobby.usda"
EXPECTED_TRIANGLES = 9_984_967


def collect_meshes() -> tuple[np.ndarray, np.ndarray]:
    vertices = []
    triangles = []
    offset = 0
    dependencies = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(dependencies)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        local_vertices = np.empty((len(mesh.vertices), 3), np.float32)
        mesh.vertices.foreach_get("co", local_vertices.ravel())
        world = np.asarray(evaluated.matrix_world, dtype=float)
        local_vertices = local_vertices @ world[:3, :3].T + world[:3, 3]
        local_triangles = np.empty((len(mesh.loop_triangles), 3), np.int32)
        mesh.loop_triangles.foreach_get("vertices", local_triangles.ravel())
        vertices.append(local_vertices)
        triangles.append(local_triangles + offset)
        offset += len(local_vertices)
        evaluated.to_mesh_clear()
    if not vertices:
        raise RuntimeError("GT USD contains no mesh objects")
    return np.vstack(vertices), np.vstack(triangles)


def pixel_grid() -> np.ndarray:
    u = np.arange(4, 1280, 8, dtype=np.int32)
    v = np.arange(4, 960, 8, dtype=np.int32)
    if len(u) != 160 or len(v) != 120:
        raise AssertionError("unexpected GT pixel grid")
    uu, vv = np.meshgrid(u, v)
    return np.column_stack([uu.ravel(), vv.ravel()])


def cast_depth(
    bvh: BVHTree, camera_to_world: np.ndarray, uv: np.ndarray, intrinsic: np.ndarray
) -> np.ndarray:
    optical = np.column_stack(
        [
            (uv[:, 0] - intrinsic[0, 2]) / intrinsic[0, 0],
            (uv[:, 1] - intrinsic[1, 2]) / intrinsic[1, 1],
            np.ones(len(uv)),
        ]
    )
    ray_norm = np.linalg.norm(optical, axis=1)
    unit_camera = optical / ray_norm[:, None]
    unit_world = unit_camera @ camera_to_world[:3, :3].T
    origin = Vector(camera_to_world[:3, 3])
    depth = np.full(len(uv), np.nan, dtype=np.float32)
    for index, direction in enumerate(unit_world):
        hit = bvh.ray_cast(origin, Vector(direction), 50.0)
        if hit[0] is not None:
            depth[index] = float(hit[3] / ray_norm[index])
    return depth


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["modeling_180", "eval_500"], required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    args = parser.parse_args(arguments)
    sample_manifest_path = BASE / f"data/depth_samples/{args.split}.json"
    sample_manifest = json.loads(sample_manifest_path.read_text())
    timestamps = [frame["timestamp_ns"] for frame in sample_manifest["frames"]]
    poses, pose_source = pose_lookup("M4", timestamps)
    stop = (
        min(len(timestamps), args.start + args.count)
        if args.count is not None
        else len(timestamps)
    )
    selected = range(args.start, stop)
    if args.start < 0 or args.start >= stop:
        raise ValueError("empty GT frame range")

    output = BASE / "evaluation/depth/gt" / args.split
    frames_dir = output / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    intrinsic, calibration = calibration_matrix()
    uv = pixel_grid()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(
        filepath=str(GT_USD),
        import_materials=False,
        import_cameras=False,
        import_lights=False,
    )
    vertices, triangles = collect_meshes()
    if len(triangles) != EXPECTED_TRIANGLES:
        raise RuntimeError(
            f"GT triangle count {len(triangles)} != {EXPECTED_TRIANGLES}"
        )
    bvh = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    started = time.monotonic()
    for sample_index in selected:
        target = frames_dir / f"{sample_index:04d}.npz"
        if target.is_file():
            value = np.load(target)
            if int(value["timestamp_ns"]) != timestamps[sample_index]:
                raise ValueError(f"stale GT frame {target}")
            continue
        truth = cast_depth(bvh, poses[sample_index], uv, intrinsic)
        atomic_npz(
            target,
            truth_z_m=truth,
            pixel_uv=uv,
            timestamp_ns=np.asarray(timestamps[sample_index], dtype=np.int64),
            source_index=np.asarray(
                sample_manifest["frames"][sample_index]["source_index"],
                dtype=np.int64,
            ),
        )
        print(
            json.dumps(
                {
                    "split": args.split,
                    "sample_index": sample_index,
                    "valid_rays": int(np.isfinite(truth).sum()),
                }
            ),
            flush=True,
        )

    complete = all(
        (frames_dir / f"{index:04d}.npz").is_file()
        for index in range(len(timestamps))
    )
    result = {
        "status": "COMPLETE" if complete else "PARTIAL",
        "split": args.split,
        "requested_range": [args.start, stop],
        "frame_count": len(timestamps),
        "rays_per_frame": len(uv),
        "pixel_grid_shape": [120, 160],
        "depth_axis": "camera optical z",
        "units": "metres",
        "valid_domain_m": [0.1, 30.0],
        "gt_usd": str(GT_USD),
        "gt_usd_sha256": sha256(GT_USD),
        "gt_triangles": len(triangles),
        "pose_source": str(pose_source),
        "pose_source_sha256": sha256(pose_source),
        "sample_manifest": str(sample_manifest_path),
        "sample_manifest_sha256": sha256(sample_manifest_path),
        "calibration": calibration,
        "seconds": time.monotonic() - started,
    }
    if complete:
        truth = []
        for index in range(len(timestamps)):
            value = np.load(frames_dir / f"{index:04d}.npz")
            truth.append(np.asarray(value["truth_z_m"], dtype=np.float32))
        cache = output / f"gt_depth_{args.split}.npz"
        atomic_npz(
            cache,
            truth_z_m=np.asarray(truth),
            pixel_uv=uv,
            timestamps_ns=np.asarray(timestamps, dtype=np.int64),
            source_indices=np.asarray(
                [frame["source_index"] for frame in sample_manifest["frames"]],
                dtype=np.int64,
            ),
            valid_domain=(
                np.isfinite(truth)
                & (np.asarray(truth) >= 0.1)
                & (np.asarray(truth) <= 30.0)
            ),
        )
        result["cache"] = str(cache)
        result["cache_sha256"] = sha256(cache)
    atomic_json(output / "manifest.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
