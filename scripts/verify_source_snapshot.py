#!/usr/bin/env python3
"""Verify preserved source bytes and syntax without importing experiment code."""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

def main():
    snapshot = json.loads((ROOT / "source_snapshot.json").read_text())
    seen = set()
    total = 0
    for entry in snapshot["files"]:
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts or str(relative) in seen:
            raise ValueError(f"Unsafe/duplicate snapshot path: {relative}")
        seen.add(str(relative))
        path = ROOT / relative
        if path.is_symlink():
            raise ValueError(f"Snapshot file must not be a symlink: {relative}")
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Snapshot mismatch: {relative}")
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
    print(json.dumps({"status": "pass", "copied_files": len(seen), "copied_bytes": total,
                      "python_files_parsed": parsed, "artifact_revision": lock["revision"]}, indent=2))

if __name__ == "__main__":
    main()
