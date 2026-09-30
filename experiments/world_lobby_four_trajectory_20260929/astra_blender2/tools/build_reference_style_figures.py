#!/usr/bin/env python3
"""Build Figure-5/7-style panels for astra_blender/models/M1–M4."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path("/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929")
RUN = ROOT / "astra_blender2"
SPACE = RUN / "report/space"
OUT = SPACE / "assets"
BLENDER = Path("/home/hchen/Documents/blender/blender-5.2.0-linux-x64/blender")
REFERENCE_EVAL = RUN / "evaluation/reference_style_figures"
VIEWS = (0, 36, 72, 108, 144)
METHODS = ("M1", "M2", "M3", "M4")
LABELS = {
    "M1": ("M1 · RGB-only", "+ Astra"),
    "M2": ("M2 · ViPE + DA3", "+ Astra"),
    "M3": ("M3 · ORB-SLAM3 + DA3", "+ Astra"),
    "M4": ("M4 · GT pose + DA3", "+ Astra"),
    "GT": ("Input GT", "Simulator RGB"),
}
RENDER_ROOTS = {
    "M1": REFERENCE_EVAL / "renders/M1",
    "M2": REFERENCE_EVAL / "renders/M2",
    "M3": REFERENCE_EVAL / "renders/M3",
    "M4": RUN / "evaluation/blog_tables_1_6_current_m4/renders/M4",
}
DEPTH_PATHS = {
    "M1": SPACE / "results/table2_m1/depth.npz",
    "M2": SPACE / "results/M2/modeling_180/depth.npz",
    "M3": SPACE / "results/M3/modeling_180/depth.npz",
    "M4": RUN / "evaluation/blog_tables_1_6_current_m4/modeling_180/depth.npz",
}
GT_DEPTH = SPACE / "results/fresh_gt/modeling_180/gt_depth_modeling_180.npz"
APPEARANCE = SPACE / "results/blog_tables_456/table5_appearance.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gt_images() -> dict[int, Path]:
    report = json.loads(APPEARANCE.read_text())
    return {
        int(row["keyframe_index"]): Path(row["gt_path"])
        for row in report["per_view"]
        if row["system"] == "M1"
    }


def ensure_renders() -> None:
    registrations = json.loads((SPACE / "results/registrations.json").read_text())
    cameras = SPACE / "results/fresh_gt/modeling_180/cameras.json"
    for method in ("M1", "M2", "M3"):
        output = RENDER_ROOTS[method]
        if all((output / f"{frame:03d}.png").exists() for frame in VIEWS):
            continue
        output.mkdir(parents=True, exist_ok=True)
        registration = REFERENCE_EVAL / f"registration_{method}.json"
        registration.parent.mkdir(parents=True, exist_ok=True)
        registration.write_text(json.dumps(registrations[method], indent=2) + "\n")
        log = output / "render.log"
        command = [
            str(BLENDER), "-b", "--factory-startup", "--threads", "2",
            "--python-exit-code", "1",
            "--python", str(RUN / "tools/render_frozen_views.py"), "--",
            "--model", str(ROOT / f"astra_blender/models/{method}/scene.blend"),
            "--cameras", str(cameras),
            "--registration", str(registration),
            "--out", str(output),
            "--indices", ",".join(map(str, VIEWS)),
            "--samples", "16",
        ]
        with log.open("w") as handle:
            subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=True)


def build_rgb_grid() -> tuple[Path, list[dict]]:
    tile_w, tile_h = 480, 360
    gutter, left, top, margin = 6, 88, 112, 24
    columns = (*METHODS, "GT")
    width = left + len(columns) * tile_w + (len(columns) - 1) * gutter + margin
    height = top + len(VIEWS) * tile_h + (len(VIEWS) - 1) * gutter + margin
    canvas = Image.new("RGB", (width, height), "#f5f5f2")
    draw = ImageDraw.Draw(canvas)
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    bold = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 27)
    detail = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 25)
    row_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 24)
    small = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 18)
    draw.text((left / 2, 70), "Frame", font=small, anchor="mm", fill="#515953")
    for column, method in enumerate(columns):
        x = left + column * (tile_w + gutter) + tile_w / 2
        first, second = LABELS[method]
        draw.text((x, 40), first, font=bold, anchor="mm", fill="#18251f")
        draw.text((x, 77), second, font=detail, anchor="mm", fill="#515953")

    gt = gt_images()
    inputs = []
    for row, frame in enumerate(VIEWS):
        y = top + row * (tile_h + gutter)
        draw.text((left / 2, y + tile_h / 2), str(frame), font=row_font, anchor="mm", fill="#18251f")
        for column, method in enumerate(columns):
            path = gt[frame] if method == "GT" else RENDER_ROOTS[method] / f"{frame:03d}.png"
            with Image.open(path) as source:
                tile = source.convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
            canvas.paste(tile, (left + column * (tile_w + gutter), y))
            inputs.append({"method": method, "frame": frame, "path": str(path), "sha256": sha256(path)})
    output = OUT / "fixed_five_view_comparison_m1_m4.jpg"
    canvas.save(output, quality=95, subsampling=0)
    return output, inputs


def build_depth_heatmap() -> tuple[Path, list[dict]]:
    gt = np.load(GT_DEPTH)
    truth = gt["truth_z_m"]
    domain = gt["valid_domain"].astype(bool)
    predictions = {
        method: np.load(path)["prediction_z_m"] for method, path in DEPTH_PATHS.items()
    }
    figure, axes = plt.subplots(5, 4, figsize=(13, 11), layout="constrained")
    cmap = plt.get_cmap("magma").copy()
    cmap.set_bad("#90d5cf")
    records = []
    image = None
    for column, method in enumerate(METHODS):
        prediction = predictions[method]
        for row, frame in enumerate(VIEWS):
            valid = (
                domain[frame]
                & np.isfinite(prediction[frame])
                & (prediction[frame] >= 0.1)
                & (prediction[frame] <= 30)
            )
            error = np.full(19200, np.nan, dtype=np.float32)
            error[valid] = (
                np.abs(prediction[frame, valid] - truth[frame, valid])
                / truth[frame, valid]
            )
            image = axes[row, column].imshow(
                error.reshape(120, 160),
                vmin=0,
                vmax=1,
                cmap=cmap,
                interpolation="nearest",
            )
            axes[row, column].set_xticks([])
            axes[row, column].set_yticks([])
            if row == 0:
                axes[row, column].set_title(method, fontsize=14)
            if column == 0:
                axes[row, column].set_ylabel(f"Frame {frame}", fontsize=12)
            records.append({
                "method": method,
                "frame": frame,
                "valid_pixels": int(valid.sum()),
                "mean_absrel": float(np.nanmean(error)),
            })
    figure.colorbar(
        image,
        ax=axes.ravel().tolist(),
        shrink=0.65,
        label="|predicted Z − GT Z| / GT Z; clipped at 1.0",
    )
    figure.suptitle(
        "Model depth error at fixed GT cameras · teal = missing/invalid prediction",
        fontsize=15,
    )
    output = OUT / "model_depth_error_five_views_m1_m4.png"
    figure.savefig(output, dpi=160)
    plt.close(figure)
    return output, records


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_renders()
    rgb_path, rgb_inputs = build_rgb_grid()
    depth_path, depth_records = build_depth_heatmap()
    manifest = {
        "status": "COMPLETE",
        "scope": "astra_blender/models/M1..M4",
        "models": {
            method: {
                "path": str(ROOT / f"astra_blender/models/{method}/scene.blend"),
                "sha256": sha256(ROOT / f"astra_blender/models/{method}/scene.blend"),
            }
            for method in METHODS
        },
        "views": list(VIEWS),
        "rgb_figure": {
            "path": str(rgb_path.relative_to(SPACE)),
            "sha256": sha256(rgb_path),
            "layout": "rows=views; columns=M1,M2,M3,M4,input GT",
            "inputs": rgb_inputs,
        },
        "depth_figure": {
            "path": str(depth_path.relative_to(SPACE)),
            "sha256": sha256(depth_path),
            "layout": "rows=views; columns=M1,M2,M3,M4",
            "color_scale": "relative optical-Z error [0,1]; magma; teal=missing/invalid",
            "source_depth": {
                method: {"path": str(path), "sha256": sha256(path)}
                for method, path in DEPTH_PATHS.items()
            },
            "gt_depth": {"path": str(GT_DEPTH), "sha256": sha256(GT_DEPTH)},
            "panels": depth_records,
        },
    }
    manifest_path = SPACE / "results/blog_tables_1_5/reference_style_figures.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "rgb": str(rgb_path),
        "depth": str(depth_path),
        "manifest": str(manifest_path),
    }, indent=2))


if __name__ == "__main__":
    main()
