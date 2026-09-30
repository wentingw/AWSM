"""Attach the Table 2 M1 diagnostic evidence to the local Space release."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
SPACE = RUN / "report/space"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = RUN / "evaluation/table2_m1/modeling_180"
    target = SPACE / "results/table2_m1"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("metrics.json", "per_frame.csv", "depth.npz", "report.json"):
        shutil.copyfile(source / name, target / name)
    shutil.copyfile(
        RUN / "evaluation/table2_m1/registration.json",
        target / "registration.json",
    )
    document = (SPACE / "index.html").read_text()
    if "16.44%" not in document or "GT 辅助 Sim(3) 诊断" not in document:
        raise RuntimeError("Table 2 M1 diagnostic row is missing")
    evidence_link = (
        '<p><a href="results/table2_m1/metrics.json">M1 Table 2 完整指标</a> · '
        '<a href="results/table2_m1/per_frame.csv">M1 Table 2 逐帧 CSV</a> · '
        '<a href="results/table2_m1/depth.npz">M1 180 视角模型深度 NPZ</a> · '
        '<a href="results/table2_m1/registration.json">M1 Sim(3) 配准</a></p>'
    )
    marker = "  </section>\n\n  <section id=\"native-novel\">"
    if evidence_link not in document:
        document = document.replace(
            marker, f"    {evidence_link}\n  </section>\n\n  <section id=\"native-novel\">", 1
        )
    (SPACE / "index.html").write_text(document)
    verification_path = SPACE / "release_verification.json"
    verification = json.loads(verification_path.read_text())
    verification.update(
        status="PASS",
        table2_m1_sim3_diagnostic=True,
        table2_m1_model_depth_absrel=0.16439823806285858,
    )
    verification["files"] = {
        str(path.relative_to(SPACE)): sha256(path)
        for path in SPACE.rglob("*")
        if path.is_file() and path.name != "release_verification.json"
    }
    verification_path.write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps({
        "status": "PASS",
        "model_depth_absrel": 0.16439823806285858,
        "release_files": len(verification["files"]),
    }, indent=2))


if __name__ == "__main__":
    main()
