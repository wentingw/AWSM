#!/usr/bin/env python3
"""Assemble the seven-table Agentic World blog dataset."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = ROOT / "report/space/results/blog_tables_1_5/tables_1_5.json"
DEFAULT_EXTENDED = ROOT / "evaluation/blog_extended_100_20260930"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.parent.resolve()).as_posix()
    except ValueError:
        return path.name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--extended", type=Path, default=DEFAULT_EXTENDED)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.extended / "tables_1_7.json"
    base = json.loads(args.base.read_text())
    appearance_path = args.extended / "appearance_metrics.json"
    depth_path = args.extended / "depth_metrics.json"
    subset_path = args.extended / "view_subset_manifest.json"
    appearance = json.loads(appearance_path.read_text())
    depth = json.loads(depth_path.read_text())
    subset = json.loads(subset_path.read_text())

    table3 = []
    for source_row in base["tables"]["table3"]:
        row = dict(source_row)
        row["bidirectional_mean_m"] = (
            row["model_to_gt_mean_m"] + row["observed_gt_to_model_mean_m"]
        ) / 2.0
        table3.append(row)

    table5 = [
        {
            "method": row["method"],
            "psnr_db": row["psnr_db_mean"],
            "ssim": row["ssim_mean"],
            "lpips_alex_v01": row["lpips_alex_v01_mean"],
        }
        for row in appearance["rows"]
    ]

    def depth_rows(name: str) -> list[dict]:
        return [
            {
                "method": row["method"],
                "absrel": row["absrel"],
                "rmse_m": row["rmse_m"],
                "coverage": row["valid_coverage"],
                "penalized_mae_m": row["missing_penalty_mae_m"],
            }
            for row in depth["subsets"][name]["rows"]
        ]

    result = {
        "schema_version": 2,
        "status": "COMPLETE",
        "scope": base["scope"],
        "reference": base["reference"],
        "m1_notice": base["m1_notice"],
        "protocols": {
            "table2": base["protocols"]["table2"],
            "table3": {
                **base["protocols"]["table3"],
                "bidirectional_mean": (
                    "arithmetic mean of model→GT and observed GT→model mean distances"
                ),
            },
            "table4": base["protocols"]["table4"],
            "table5": {
                "scope": (
                    "100 seeded views drawn without replacement from the 175 modeling "
                    "frames remaining after excluding fixed views; these are not unseen "
                    "modeling inputs"
                ),
                "seed": subset["selection"]["seed"],
                "excluded_fixed_views": subset["selection"]["excluded_fixed_views"],
                "selected_indices": subset["selection"]["selected_indices"],
                "resolution": appearance["resolution_wh"],
                "preprocessing": appearance["preprocessing"],
                "metrics": "full-image PSNR, SSIM, LPIPS AlexNet v0.1",
                "aggregation": appearance["aggregation"],
            },
            "table6": {
                "views": list(depth["subsets"]["fixed_five"]["indices"]),
                "depth": depth["protocol"],
            },
            "table7": {
                "scope": (
                    "the exact same 100 modeling-frame indices as Table 5; held out "
                    "only from the fixed-five check"
                ),
                "seed": subset["selection"]["seed"],
                "selected_indices": subset["selection"]["selected_indices"],
                "depth": depth["protocol"],
            },
        },
        "tables": {
            "table1": base["tables"]["table1"],
            "table2": base["tables"]["table2"],
            "table3": table3,
            "table4": base["tables"]["table4"],
            "table5": table5,
            "table6": depth_rows("fixed_five"),
            "table7": depth_rows("random_100"),
        },
        "source_files": {
            "base_tables_1_5": {
                "path": source_label(args.base),
                "sha256": sha256(args.base),
            },
            "view_subset_manifest": {
                "path": source_label(subset_path),
                "sha256": sha256(subset_path),
            },
            "appearance_metrics": {
                "path": source_label(appearance_path),
                "sha256": sha256(appearance_path),
            },
            "depth_metrics": {
                "path": source_label(depth_path),
                "sha256": sha256(depth_path),
            },
        },
    }
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "COMPLETE", "output": str(out), "tables": 7}))


if __name__ == "__main__":
    main()
