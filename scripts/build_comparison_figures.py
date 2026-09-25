#!/usr/bin/env python3
"""Build labelled comparison grids from the existing fixed-camera renders."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
VIEWS = [0, 36, 72, 108, 144]
LABELS = {
    "M1": ("RGB-only", "+ Astra"),
    "M2": ("ViPE", "+ Astra"),
    "M3": ("OpenVINS + MapAnything", "+ Astra"),
    "M4": ("GT pose + MapAnything", "+ Astra"),
    "B1": ("ViPE", "+ TSDF"),
    "B2": ("MapAnything", "+ TSDF"),
    "B2p": ("OpenVINS + MapAnything", "+ TSDF"),
    "GT": ("Input GT", "Simulator RGB"),
}


def build_grid(columns, name, png=False):
    tile_w, tile_h = 480, 360
    gutter, left, top, margin = 6, 88, 112, 24
    width = left + len(columns) * tile_w + (len(columns) - 1) * gutter + margin
    height = top + len(VIEWS) * tile_h + (len(VIEWS) - 1) * gutter + margin
    canvas = Image.new("RGB", (width, height), "#f5f5f2")
    draw = ImageDraw.Draw(canvas)
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    label_font = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 28)
    detail_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 26)
    row_font = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 24)
    draw.text((left / 2, 70), "Frame", font=ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 18),
              anchor="mm", fill="#515953")
    for column, method in enumerate(columns):
        x = left + column * (tile_w + gutter) + tile_w / 2
        first, second = LABELS[method]
        if draw.textlength(first, font=label_font) > tile_w - 20:
            raise ValueError(f"Column label too wide: {first}")
        draw.text((x, 40), first, font=label_font, anchor="mm", fill="#18251f")
        draw.text((x, 77), second, font=detail_font, anchor="mm", fill="#515953")

    inputs = []
    for row, frame in enumerate(VIEWS):
        y = top + row * (tile_h + gutter)
        draw.text((left / 2, y + tile_h / 2), str(frame), font=row_font, anchor="mm", fill="#18251f")
        for column, method in enumerate(columns):
            if method == "GT":
                matches = list((ROOT / "data/world_lobby/rgb_180").glob(f"{frame:06d}_*.png"))
                if len(matches) != 1:
                    raise ValueError(f"Expected exactly one input RGB for frame {frame}")
                path = matches[0]
            else:
                path = ROOT / f"results/{method}/renders/{frame:03d}.png"
            with Image.open(path) as source:
                if source.width * 3 != source.height * 4:
                    raise ValueError(f"Unexpected image aspect ratio: {path}")
                tile = source.convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
            canvas.paste(tile, (left + column * (tile_w + gutter), y))
            inputs.append({"method": method, "frame": frame, "path": str(path.relative_to(ROOT)),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    out = ROOT / "figures"
    out.mkdir(exist_ok=True)
    canvas.save(out / f"{name}.jpg", quality=95, subsampling=0)
    if png:
        canvas.save(out / f"{name}.png")
    return {"figure": f"figures/{name}.jpg", "rows": VIEWS, "columns": columns,
            "column_labels": [" ".join(LABELS[m]) for m in columns], "size": [width, height],
            "tile_size": [tile_w, tile_h], "left": left, "top": top, "gutter": gutter,
            "inputs": inputs}


def build_figures():
    grids = [build_grid(["M1", "M2", "M3", "M4", "GT"], "five_view_comparison", png=True),
             build_grid(["B1", "B2", "B2p", "GT"], "direct_baseline_comparison")]
    report = {"scope": "Existing fixed-camera renders and input RGB; resize only, no crop or rerender",
              "grids": grids}
    (ROOT / "figures/comparison_grids_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"figures": [{k: g[k] for k in ("figure", "columns", "column_labels", "size")} for g in grids]}, indent=2))
    return report


if __name__ == "__main__":
    build_figures()
