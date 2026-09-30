#!/usr/bin/env python3
"""Freeze the blog view subsets and evaluate appearance/depth on them."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
METHODS = ("M1", "M2", "M3", "M4")
FIXED_VIEWS = (0, 36, 72, 108, 144)
SEED = 20260930
MODEL_ROOT = PROJECT / "astra_blender/models"
FRAMES_PATH = PROJECT / "data/depth_samples/modeling_180.json"
GT_DEPTH = ROOT / "report/space/results/fresh_gt/modeling_180/gt_depth_modeling_180.npz"
PREDICTIONS = {
    "M1": ROOT / "report/space/results/table2_m1/depth.npz",
    "M2": ROOT / "report/space/results/M2/modeling_180/depth.npz",
    "M3": ROOT / "report/space/results/M3/modeling_180/depth.npz",
    "M4": ROOT / "evaluation/blog_tables_1_6_current_m4/modeling_180/depth.npz",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_manifest(out: Path) -> dict:
    frames_document = json.loads(FRAMES_PATH.read_text())
    frames = frames_document["frames"]
    eligible = sorted(set(range(len(frames))) - set(FIXED_VIEWS))
    selected = sorted(
        np.random.default_rng(SEED).choice(eligible, size=100, replace=False).tolist()
    )
    manifest = {
        "status": "COMPLETE",
        "selection": {
            "seed": SEED,
            "generator": "numpy.random.default_rng(seed).choice(sorted eligible, 100, replace=False)",
            "population_size": len(eligible),
            "excluded_fixed_views": list(FIXED_VIEWS),
            "selected_indices": selected,
        },
        "source": {
            "manifest": str(FRAMES_PATH),
            "manifest_sha256": sha256(FRAMES_PATH),
            "frame_count": len(frames),
        },
        "selected_frames": [
            {
                "sample_index": index,
                "source_index": frames[index]["source_index"],
                "timestamp_ns": frames[index]["timestamp_ns"],
                "image": frames[index]["image"],
                "image_sha256": frames[index]["image_sha256"],
            }
            for index in selected
        ],
        "models": {
            method: {
                "scene_blend": str(MODEL_ROOT / method / "scene.blend"),
                "scene_blend_sha256": sha256(MODEL_ROOT / method / "scene.blend"),
            }
            for method in METHODS
        },
        "depth_inputs": {
            "ground_truth": {"path": str(GT_DEPTH), "sha256": sha256(GT_DEPTH)},
            **{
                method: {"path": str(path), "sha256": sha256(path)}
                for method, path in PREDICTIONS.items()
            },
        },
        "evaluator": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256(Path(__file__).resolve()),
        },
    }
    manifest_path = out / "view_subset_manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["selection"] != manifest["selection"]:
            raise RuntimeError("Refusing to replace an incompatible frozen subset")
        if previous["models"] != manifest["models"]:
            raise RuntimeError("Frozen model hashes changed")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def depth_metrics(truth: np.ndarray, prediction: np.ndarray, domain: np.ndarray) -> dict:
    domain = domain & np.isfinite(truth) & (truth >= 0.1) & (truth <= 30.0)
    valid = domain & np.isfinite(prediction) & (prediction >= 0.1) & (prediction <= 30.0)
    domain_count = int(domain.sum())
    valid_count = int(valid.sum())
    error = np.abs(prediction[valid] - truth[valid])
    return {
        "pixels_domain": domain_count,
        "pixels_valid": valid_count,
        "valid_coverage": valid_count / domain_count,
        "absrel": float(np.mean(error / truth[valid])),
        "mae_m": float(np.mean(error)),
        "rmse_m": float(np.sqrt(np.mean(error**2))),
        "missing_penalty_mae_m": float(
            (error.sum() + 30.0 * (domain_count - valid_count)) / domain_count
        ),
    }


def evaluate_depth(out: Path, manifest: dict) -> dict:
    gt = np.load(GT_DEPTH)
    truth = np.asarray(gt["truth_z_m"], dtype=np.float32)
    domain = np.asarray(gt["valid_domain"], dtype=bool)
    subsets = {
        "fixed_five": list(FIXED_VIEWS),
        "random_100": manifest["selection"]["selected_indices"],
    }
    report = {
        "status": "COMPLETE",
        "protocol": {
            "depth": "optical Z in metres",
            "domain": "GT valid_domain and finite GT in [0.1, 30] m",
            "prediction_valid": "finite prediction in [0.1, 30] m",
            "aggregation": "pixel-weighted over all selected frames",
            "missing_penalty": "30 m absolute error for each missing prediction",
        },
        "subsets": {},
    }
    for subset_name, indices in subsets.items():
        rows = []
        index_array = np.asarray(indices, dtype=np.int64)
        for method, path in PREDICTIONS.items():
            prediction_file = np.load(path)
            prediction = np.asarray(prediction_file["prediction_z_m"], dtype=np.float32)
            if prediction.shape != truth.shape:
                raise ValueError(f"{method} prediction shape {prediction.shape} != {truth.shape}")
            if not np.array_equal(prediction_file["pixel_uv"], gt["pixel_uv"]):
                raise ValueError(f"{method} pixel_uv differs from GT")
            if not np.array_equal(prediction_file["timestamps_ns"], gt["timestamps_ns"]):
                raise ValueError(f"{method} timestamps differ from GT")
            rows.append(
                {
                    "method": method,
                    **depth_metrics(
                        truth[index_array], prediction[index_array], domain[index_array]
                    ),
                }
            )
        report["subsets"][subset_name] = {
            "indices": indices,
            "frame_count": len(indices),
            "rows": rows,
        }
    (out / "depth_metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "depth_metrics.csv").open("w", newline="") as handle:
        fields = ["subset", "method", *report["subsets"]["fixed_five"]["rows"][0].keys()]
        fields.remove("method")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for subset_name, subset in report["subsets"].items():
            for row in subset["rows"]:
                writer.writerow({"subset": subset_name, **row})
    return report


def evaluate_appearance(out: Path, manifest: dict, render_root: Path) -> dict:
    blog = ROOT.parents[1] / "world_model_blog"
    sys.path.insert(0, str(blog / "runtime/lpips_python"))
    os.environ.setdefault("TORCH_HOME", str(blog / "runtime/lpips_torch"))
    import lpips
    import PIL
    import skimage
    import torch
    import torchvision
    from PIL import Image
    from skimage.metrics import structural_similarity

    frames = json.loads(FRAMES_PATH.read_text())["frames"]
    indices = manifest["selection"]["selected_indices"]
    torch.set_num_threads(4)
    torch.manual_seed(0)
    model = lpips.LPIPS(
        net="alex",
        version="0.1",
        lpips=True,
        pnet_rand=False,
        pnet_tune=False,
        eval_mode=True,
        verbose=False,
    ).cpu().eval()
    records = []
    with torch.inference_mode():
        for method in METHODS:
            for index in indices:
                pred_path = render_root / method / f"{index:03d}.png"
                gt_path = Path(frames[index]["image"])
                pred_image = Image.open(pred_path).convert("RGB")
                gt_image = Image.open(gt_path).convert("RGB")
                if pred_image.size != (640, 480) or gt_image.size != (1280, 960):
                    raise ValueError(f"Unexpected dimensions for {method} view {index}")
                pred = np.asarray(pred_image, dtype=np.float32) / 255.0
                gt_rgb = np.asarray(
                    gt_image.resize((640, 480), Image.Resampling.LANCZOS),
                    dtype=np.float32,
                ) / 255.0
                mse = float(np.mean((pred - gt_rgb) ** 2))
                pred_tensor = torch.from_numpy(pred.transpose(2, 0, 1).copy())[None]
                gt_tensor = torch.from_numpy(gt_rgb.transpose(2, 0, 1).copy())[None]
                records.append(
                    {
                        "method": method,
                        "sample_index": index,
                        "psnr_db": float("inf") if mse == 0 else float(-10 * np.log10(mse)),
                        "ssim": float(
                            structural_similarity(
                                pred, gt_rgb, channel_axis=2, data_range=1.0
                            )
                        ),
                        "lpips_alex_v01": float(
                            model(pred_tensor, gt_tensor, normalize=True).item()
                        ),
                        "render_sha256": sha256(pred_path),
                        "gt_sha256": sha256(gt_path),
                    }
                )
                print(method, index, flush=True)
    rows = []
    for method in METHODS:
        selected = [record for record in records if record["method"] == method]
        rows.append(
            {
                "method": method,
                "views": len(selected),
                "psnr_db_mean": float(np.mean([row["psnr_db"] for row in selected])),
                "ssim_mean": float(np.mean([row["ssim"] for row in selected])),
                "lpips_alex_v01_mean": float(
                    np.mean([row["lpips_alex_v01"] for row in selected])
                ),
            }
        )
    report = {
        "status": "COMPLETE",
        "indices": indices,
        "resolution_wh": [640, 480],
        "preprocessing": (
            "GT RGB Lanczos 1280x960 to 640x480; RGB float32 [0,1]; "
            "no crop, mask, or color/exposure fitting"
        ),
        "aggregation": "arithmetic mean over the same frozen 100 views",
        "lpips": {
            "implementation": "lpips==0.1.4",
            "network": "AlexNet",
            "version": "0.1",
            "input_normalize": True,
            "device": "cpu",
        },
        "versions": {
            "torch": torch.__version__,
            "torchvision": torchvision.__version__,
            "numpy": np.__version__,
            "Pillow": PIL.__version__,
            "scikit-image": skimage.__version__,
        },
        "rows": rows,
        "per_view": records,
    }
    (out / "appearance_metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "appearance_metrics_per_view.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", type=Path, default=ROOT / "evaluation/blog_extended_100_20260930"
    )
    parser.add_argument("--appearance", action="store_true")
    parser.add_argument("--render-root", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = freeze_manifest(args.out)
    depth = evaluate_depth(args.out, manifest)
    print(json.dumps(depth["subsets"], indent=2))
    if args.appearance:
        render_root = args.render_root or args.out / "renders"
        appearance = evaluate_appearance(args.out, manifest, render_root)
        print(json.dumps(appearance["rows"], indent=2))


if __name__ == "__main__":
    main()
