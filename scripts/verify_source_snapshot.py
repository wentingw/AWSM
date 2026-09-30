#!/usr/bin/env python3
"""Verify preserved source bytes and syntax without importing experiment code."""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

def main():
    snapshot = json.loads((ROOT / "source_snapshot.json").read_text())
    manifests = [(ROOT, snapshot)]
    for name in snapshot.get("additional_snapshots", []):
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe supplemental snapshot path: {relative}")
        path = ROOT / relative
        if path.is_symlink():
            raise ValueError(f"Supplemental manifest must not be a symlink: {relative}")
        manifests.append((path.parent, json.loads(path.read_text())))
    seen = set()
    total = 0
    for base, manifest in manifests:
        for entry in manifest["files"]:
            relative = PurePosixPath(entry["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe snapshot path: {relative}")
            path = base / relative
            key = path.relative_to(ROOT).as_posix()
            if key in seen:
                raise ValueError(f"Duplicate snapshot path: {key}")
            seen.add(key)
            if path.is_symlink():
                raise ValueError(f"Snapshot file must not be a symlink: {key}")
            data = path.read_bytes()
            if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"Snapshot mismatch: {key}")
            total += len(data)
    parsed = 0
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(part.startswith(".") or part in {"assets", "runtime", "vendor", "__pycache__"} for part in rel.parts):
            continue
        ast.parse(path.read_text(), filename=str(rel))
        parsed += 1
    lock = json.loads((ROOT / "artifact-lock.json").read_text())
    if len(lock["revision"]) != 40 or len(lock["manifest_sha256"]) != 64:
        raise ValueError("Artifact lock must use a full immutable revision and SHA256")
    expected = {f"M{i}/scene.{ext}" for i in range(1, 5) for ext in ("blend", "glb")}
    if {x["destination"] for x in lock["models"]} != expected or len(lock["models"]) != 8:
        raise ValueError("Expected eight original model artifacts")
    print(json.dumps({"status": "pass", "snapshots": len(manifests), "copied_files": len(seen), "copied_bytes": total,
                      "python_files_parsed": parsed, "artifact_revision": lock["revision"]}, indent=2))

if __name__ == "__main__":
    main()
