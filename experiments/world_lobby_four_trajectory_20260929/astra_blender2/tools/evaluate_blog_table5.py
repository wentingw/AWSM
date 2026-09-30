"""Evaluate the reference blog Table 5 protocol on frozen World Lobby models."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT.parents[1] / "world_model_blog"
sys.path.insert(0, str(BLOG / "runtime/lpips_python"))
os.environ.setdefault("TORCH_HOME", str(BLOG / "runtime/lpips_torch"))

import lpips
import numpy as np
import PIL
import skimage
import torch
import torchvision
from PIL import Image
from skimage.metrics import structural_similarity

METHODS = ("M1", "M2", "M3", "M4")
VIEWS = (0, 36, 72, 108, 144)
OUT = ROOT / "evaluation/blog_tables_456"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--model-root", type=Path, default=ROOT / "models")
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--registrations", type=Path)
    args = parser.parse_args()
    out = args.out
    requested = tuple(item.strip() for item in args.methods.split(",") if item.strip())
    out.mkdir(parents=True, exist_ok=True)
    frames = json.loads((ROOT.parent / "data/depth_samples/modeling_180.json").read_text())["frames"]
    torch.set_num_threads(4)
    torch.manual_seed(0)
    model = lpips.LPIPS(
        net="alex", version="0.1", lpips=True, pnet_rand=False,
        pnet_tune=False, eval_mode=True, verbose=False,
    ).cpu().eval()
    registration_path = args.registrations or (ROOT / "evaluation/depth/registrations.json")
    registrations = json.loads(registration_path.read_text())
    methods=[m for m in requested if registrations[m]["status"]=="COMPLETE"]
    records = []
    with torch.inference_mode():
        for method in methods:
            for view in VIEWS:
                pred_path = out / "renders" / method / f"{view:03d}.png"
                gt_path = Path(frames[view]["image"])
                pred_image = Image.open(pred_path).convert("RGB")
                gt_image = Image.open(gt_path).convert("RGB")
                if pred_image.size != (640, 480) or gt_image.size != (1280, 960):
                    raise ValueError(f"Unexpected image dimensions for {method} view {view}")
                pred = np.asarray(pred_image, dtype=np.float32) / 255.0
                gt = np.asarray(
                    gt_image.resize((640, 480), Image.Resampling.LANCZOS),
                    dtype=np.float32,
                ) / 255.0
                mse = float(np.mean((pred - gt) ** 2))
                psnr = float("inf") if mse == 0 else float(-10.0 * np.log10(mse))
                ssim = float(structural_similarity(pred, gt, channel_axis=2, data_range=1.0))
                pred_tensor = torch.from_numpy(pred.transpose(2, 0, 1).copy())[None]
                gt_tensor = torch.from_numpy(gt.transpose(2, 0, 1).copy())[None]
                lpips_value = float(model(pred_tensor, gt_tensor, normalize=True).item())
                record = {
                    "system": method,
                    "keyframe_index": view,
                    "psnr_db": psnr,
                    "ssim": ssim,
                    "lpips_alex_v01": lpips_value,
                    "pred_path": str(pred_path),
                    "gt_path": str(gt_path),
                    "pred_sha256": sha256(pred_path),
                    "gt_sha256": sha256(gt_path),
                }
                records.append(record)
                print(method, view, f"PSNR={psnr:.6f}", f"SSIM={ssim:.6f}", f"LPIPS={lpips_value:.6f}")
    rows = []
    for method in methods:
        selected = [record for record in records if record["system"] == method]
        rows.append({
            "system": method,
            "views": len(selected),
            "psnr_db_mean": float(np.mean([record["psnr_db"] for record in selected])),
            "ssim_mean": float(np.mean([record["ssim"] for record in selected])),
            "lpips_alex_v01_mean": float(np.mean([record["lpips_alex_v01"] for record in selected])),
        })
    report = {
        "status": "complete",
        "model_sha256":{m:sha256(args.model_root/m/"scene.blend") for m in methods},
        "methods": methods,
        "m1_alignment": registrations.get("M1"),
        "keyframe_indices": list(VIEWS),
        "resolution_wh": [640, 480],
        "preprocessing": "GT RGB Lanczos 1280x960 to 640x480; RGB float32 [0,1]; no crop, mask, or color/exposure fitting",
        "aggregation": "arithmetic mean over five views",
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
    (out / "table5_appearance.json").write_text(json.dumps(report, indent=2) + "\n")
    with (out / "table5_appearance_per_view.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    with (out / "table5_appearance_means.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
