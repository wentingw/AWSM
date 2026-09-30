#!/usr/bin/env python3
"""Recompute blog Table 4 geometry and Table 6 novel-depth metrics."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collect(objects, transform=None):
    vertices = []
    triangles = []
    offset = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        verts = np.empty((len(mesh.vertices), 3), np.float32)
        mesh.vertices.foreach_get("co", verts.ravel())
        world = np.asarray(evaluated.matrix_world, dtype=float)
        verts = verts @ world[:3, :3].T + world[:3, 3]
        if transform is not None:
            verts = verts @ transform[:3, :3].T + transform[:3, 3]
        tris = np.empty((len(mesh.loop_triangles), 3), np.int32)
        mesh.loop_triangles.foreach_get("vertices", tris.ravel())
        vertices.append(verts)
        triangles.append(tris + offset)
        offset += len(verts)
        evaluated.to_mesh_clear()
    if not vertices:
        raise RuntimeError("no mesh objects")
    return np.vstack(vertices), np.vstack(triangles)


def sample_surface(vertices, triangles, count, seed):
    rng = np.random.default_rng(seed)
    tri = vertices[triangles]
    area = 0.5 * np.linalg.norm(
        np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1
    )
    cumulative = np.cumsum(area)
    indices = np.searchsorted(cumulative, rng.random(count) * cumulative[-1])
    selected = tri[indices]
    u = np.sqrt(rng.random(count))
    v = rng.random(count)
    return (
        selected[:, 0]
        + u[:, None] * (1 - v)[:, None] * (selected[:, 1] - selected[:, 0])
        + u[:, None] * v[:, None] * (selected[:, 2] - selected[:, 0])
    )


def distance_summary(distances):
    return {
        "count": int(len(distances)),
        "mean_m": float(np.mean(distances)),
        "rmse_m": float(np.sqrt(np.mean(distances**2))),
        "median_m": float(np.median(distances)),
        "p90_m": float(np.percentile(distances, 90)),
    }


def depth_metrics(truth, prediction):
    domain = np.isfinite(truth) & (truth >= 0.1) & (truth <= 30)
    valid = (
        domain
        & np.isfinite(prediction)
        & (prediction >= 0.1)
        & (prediction <= 30)
    )
    count = int(domain.sum())
    valid_count = int(valid.sum())
    error = np.abs(prediction[valid] - truth[valid])
    return {
        "pixels_domain": count,
        "pixels_valid": valid_count,
        "valid_coverage": valid_count / count,
        "absrel": float(np.mean(error / truth[valid])),
        "mae_m": float(np.mean(error)),
        "rmse_m": float(np.sqrt(np.mean(error**2))),
        "missing_penalty_mae_m": float(
            (error.sum() + 30 * (count - valid_count)) / count
        ),
    }


def rotation_z(angle):
    cosine, sine = np.cos(angle), np.sin(angle)
    return np.array(
        [[cosine, -sine, 0], [sine, cosine, 0], [0, 0, 1.0]]
    )


def novel_views(cameras):
    selected = np.linspace(0, len(cameras["frames"]) - 1, 20, dtype=int)
    views = []
    for order, index in enumerate(selected):
        camera_to_world = np.asarray(
            cameras["frames"][int(index)]["camera_to_world"], dtype=float
        )
        position = camera_to_world[:3, 3]
        rotation = camera_to_world[:3, :3]
        perturbed_position = (
            position
            + 0.20 * rotation[:, 0]
            - 0.08 * rotation[:, 1]
            + np.array([0, 0, 0.04 * ((order % 3) - 1)])
        )
        perturbed_rotation = (
            rotation_z(np.deg2rad((order % 5 - 2) * 2.0)) @ rotation
        )
        views.append(
            {
                "view_id": f"holdout_{order:02d}",
                "source_sample_index": int(index),
                "camera_position_world_m": perturbed_position.tolist(),
                "camera_rotation_world_from_optical": perturbed_rotation.tolist(),
            }
        )
    return views


def cast_depth(bvh, views, pixel_uv):
    optical = np.column_stack(
        [
            (pixel_uv[:, 0] - 320) / 381.4,
            (pixel_uv[:, 1] - 240) / 381.4,
            np.ones(len(pixel_uv)),
        ]
    )
    norms = np.linalg.norm(optical, axis=1)
    camera_directions = optical / norms[:, None]
    result = np.full((len(views), len(pixel_uv)), np.nan, np.float32)
    for view_index, view in enumerate(views):
        rotation = np.asarray(view["camera_rotation_world_from_optical"])
        origin = Vector(view["camera_position_world_m"])
        for ray_index, direction in enumerate(camera_directions @ rotation.T):
            hit = bvh.ray_cast(origin, Vector(direction), 50)
            if hit[0] is not None:
                result[view_index, ray_index] = hit[3] / norms[ray_index]
    return result


def observed_gt_points(depth_cache, cameras, count):
    cached = np.load(depth_cache)
    truth = np.asarray(cached["truth_z_m"], dtype=np.float32)
    uv = np.asarray(cached["pixel_uv"], dtype=np.float64)
    valid = np.isfinite(truth) & (truth >= 0.1) & (truth <= 30)
    flat = np.flatnonzero(valid)
    rng = np.random.default_rng(20260925)
    chosen = rng.choice(flat, min(count, len(flat)), replace=False)
    frame_indices, pixel_indices = np.unravel_index(chosen, truth.shape)
    rays = np.column_stack(
        [
            (uv[pixel_indices, 0] - 640) / 762.8,
            (uv[pixel_indices, 1] - 480) / 762.8,
            np.ones(len(pixel_indices)),
        ]
    )
    points = np.empty_like(rays)
    for frame_index in np.unique(frame_indices):
        mask = frame_indices == frame_index
        pose = np.asarray(cameras["frames"][int(frame_index)]["camera_to_world"])
        camera_points = (
            rays[mask] * truth[frame_index, pixel_indices[mask], None]
        )
        points[mask] = camera_points @ pose[:3, :3].T + pose[:3, 3]
    return points


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--gt-usd", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gt-depth",type=Path,required=True)
    parser.add_argument("--model-root", type=Path)
    parser.add_argument("--methods", default="M1,M2,M3,M4")
    parser.add_argument("--registrations", type=Path)
    parser.add_argument("--cameras", type=Path)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    )
    started = time.monotonic()
    args.out.mkdir(parents=True, exist_ok=True)
    registration_path = args.registrations or (args.run / "evaluation/depth/registrations.json")
    camera_path = args.cameras or (args.run / "evaluation/depth/gt_cameras_modeling_180.json")
    registrations = json.loads(registration_path.read_text())
    cameras = json.loads(camera_path.read_text())
    depth_cache = args.gt_depth
    requested = [item.strip() for item in args.methods.split(",") if item.strip()]
    methods = [m for m in requested if registrations[m]["status"]=="COMPLETE"]
    model_root = args.model_root or (args.run / "models")
    frozen = {}
    for method in methods:
        directory = model_root / method
        freeze_path = directory / "freeze_manifest.json"
        final_freeze_path = directory / "final_freeze.json"
        if freeze_path.exists():
            frozen[method] = json.loads(freeze_path.read_text())
            for name, digest in frozen[method]["files"].items():
                assert sha256(directory / name) == digest
        elif final_freeze_path.exists():
            frozen[method] = json.loads(final_freeze_path.read_text())
            for name, record in frozen[method]["artifacts"].items():
                assert sha256(directory / name) == record["sha256"]
        else:
            raise FileNotFoundError(f"No freeze manifest for {method}: {directory}")
    models = {
        method: model_root / method / "scene.blend" for method in methods
    }

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(
        filepath=str(args.gt_usd),
        import_materials=False,
        import_cameras=False,
        import_lights=False,
        support_scene_instancing=False,
    )
    gt_vertices, gt_triangles = collect(
        [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render and not obj.get("exclude_from_evaluation",False)]
    )
    if len(gt_triangles) != 9_984_967:
        raise RuntimeError(f"unexpected GT triangle count: {len(gt_triangles)}")
    gt_bvh = BVHTree.FromPolygons(
        gt_vertices, gt_triangles, all_triangles=True
    )

    observed_points = observed_gt_points(depth_cache, cameras, 100_000)
    views = novel_views(cameras)
    rng = np.random.default_rng(23)
    pixel_uv = np.column_stack(
        [rng.integers(0, 640, 5000), rng.integers(0, 480, 5000)]
    )
    novel_truth = cast_depth(gt_bvh, views, pixel_uv)
    np.savez_compressed(
        args.out / "novel_gt_samples.npz",
        pixel_uv=pixel_uv,
        optical_z_m=novel_truth,
        seed=23,
    )

    report = {
        "status": "COMPLETE",
        "reference_protocol": "wentingw astra-world-model-blog Tables 4 and 6",
        "m1": registrations.get("M1"),
        "frozen_models_verified":True,
        "observed_gt_depth_sha256":sha256(depth_cache),
        "gt": {
            "usd": str(args.gt_usd),
            "sha256": sha256(args.gt_usd),
            "triangles": int(len(gt_triangles)),
        },
        "table4": {
            "samples_each": 100_000,
            "model_surface_seed": 20260923,
            "observed_gt_seed": 20260925,
            "observed_sampling": (
                "uniform over valid GT image-ray hits across 180 frames; "
                "observation-frequency weighted"
            ),
            "rows": [],
        },
        "table6": {
            "scope": (
                "20 deterministic perturbations of the same modeling trajectory; "
                "not a new scene"
            ),
            "ray_seed": 23,
            "rays_per_view": 5000,
            "resolution_wh": [640, 480],
            "intrinsics": [381.4, 381.4, 320, 240],
            "views": views,
            "rows": [],
        },
    }

    for method in methods:
        registration = registrations[method]
        transform = np.asarray(registration["transform"], dtype=float)
        bpy.ops.wm.open_mainfile(filepath=str(models[method]))
        model_vertices, model_triangles = collect(
            [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render and not obj.get("exclude_from_evaluation",False)],
            transform,
        )
        model_bvh = BVHTree.FromPolygons(
            model_vertices, model_triangles, all_triangles=True
        )

        sampled_model = sample_surface(
            model_vertices, model_triangles, 100_000, 20260923
        )
        model_to_gt = np.asarray(
            [gt_bvh.find_nearest(Vector(point))[3] for point in sampled_model]
        )
        observed_to_model = np.asarray(
            [model_bvh.find_nearest(Vector(point))[3] for point in observed_points]
        )
        table4_row = {
            "method": method,
            "model_triangles": int(len(model_triangles)),
            "model_to_gt": distance_summary(model_to_gt),
            "observed_gt_to_model": distance_summary(observed_to_model),
            "alignment": registration["scope"],
            "model_sha256": sha256(models[method]),
        }
        report["table4"]["rows"].append(table4_row)
        np.savez_compressed(
            args.out / f"{method}_table4_distances.npz",
            model_to_gt_m=model_to_gt,
            observed_gt_to_model_m=observed_to_model,
        )

        novel_prediction = cast_depth(model_bvh, views, pixel_uv)
        table6_row = {
            "method": method,
            "model_triangles": int(len(model_triangles)),
            **depth_metrics(novel_truth, novel_prediction),
            "per_view": [
                {
                    "view_id": view["view_id"],
                    **depth_metrics(
                        novel_truth[index], novel_prediction[index]
                    ),
                }
                for index, view in enumerate(views)
            ],
        }
        report["table6"]["rows"].append(table6_row)
        np.savez_compressed(
            args.out / f"{method}_table6_depth.npz",
            pixel_uv=pixel_uv,
            predicted_z_m=novel_prediction,
        )
        print(
            method,
            "TABLE4",
            model_to_gt.mean(),
            observed_to_model.mean(),
            "TABLE6",
            table6_row["absrel"],
            table6_row["rmse_m"],
            flush=True,
        )
        del model_bvh, model_vertices, model_triangles

    for method in frozen:
        directory = model_root / method
        if "files" in frozen[method]:
            for name, digest in frozen[method]["files"].items():
                assert sha256(directory / name) == digest
        else:
            for name, record in frozen[method]["artifacts"].items():
                assert sha256(directory / name) == record["sha256"]
    report["elapsed_seconds"] = time.monotonic() - started
    (args.out / "tables_4_6.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
