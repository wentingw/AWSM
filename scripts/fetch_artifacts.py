#!/usr/bin/env python3
"""Fetch immutable published evidence using only Python's standard library."""
import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("models", "all"), default="models")
    parser.add_argument("--method", choices=("M1", "M2", "M3", "M4"), help="Optionally download only this method with --group models")
    parser.add_argument("--auth", action="store_true", help="Use HF_TOKEN from the environment or the saved Hugging Face login")
    parser.add_argument("--list", action="store_true", help="Verify the remote manifest and list selected assets without downloading them")
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    args = parser.parse_args()
    if args.method and args.group != "models":
        parser.error("--method is only supported with --group models")
    token = None
    if args.auth:
        token = os.environ.get("HF_TOKEN")
        if not token:
            try:
                from huggingface_hub import get_token
            except ImportError:
                raise SystemExit("Install huggingface-hub and run hf auth login, or supply HF_TOKEN in the environment.") from None
            token = get_token()
        if not token:
            raise SystemExit("No saved Hugging Face login or HF_TOKEN was found.")
    class SafeRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
            if redirected and urllib.parse.urlparse(req.full_url).netloc != urllib.parse.urlparse(newurl).netloc:
                redirected.remove_header("Authorization")
            return redirected
    opener = urllib.request.build_opener(SafeRedirect())
    def open_url(url, timeout):
        headers = {"User-Agent": "SceneWeft-artifact-fetcher/1.0"}
        if token:
            headers["Authorization"] = "Bearer " + token
        return opener.open(urllib.request.Request(url, headers=headers), timeout=timeout)
    lock = json.loads((ROOT / "artifact-lock.json").read_text())
    base = f"https://huggingface.co/datasets/{lock['dataset']}/resolve/{lock['revision']}/"
    try:
        with open_url(base + "payload_manifest.json", timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(f"HF manifest request returned HTTP {error.code}. "
                         "Check dataset access (use --auth for private assets) and network access; "
                         "this tool will not substitute another revision.") from None
    if hashlib.sha256(data).hexdigest() != lock["manifest_sha256"]:
        raise ValueError("Published manifest SHA256 differs from artifact-lock.json")
    entries = json.loads(data)["entries"]
    index = {}
    for entry in entries:
        relative = PurePosixPath(entry["path"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or entry["path"] in index:
            raise ValueError("Unsafe or duplicate asset path")
        index[entry["path"]] = entry
    model_paths = []
    for model in lock["models"]:
        path = "models/" + model["destination"]
        entry = index[path]
        if (entry["bytes"], entry["sha256"]) != (model["bytes"], model["sha256"]):
            raise ValueError(f"Model lock mismatch: {path}")
        model_paths.append(path)
    selected = [index[path] for path in model_paths] if args.group == "models" else entries
    if args.method:
        selected = [entry for entry in selected if entry["path"].startswith("models/" + args.method + "/")]
    if args.list:
        print(json.dumps({"revision": lock["revision"], "manifest_verified": True,
                          "files": len(selected), "bytes": sum(e["bytes"] for e in selected),
                          "paths": [e["path"] for e in selected]}, indent=2))
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for entry in selected:
        dest = output / entry["path"]
        if dest.is_symlink() or not dest.resolve().is_relative_to(output):
            raise ValueError(f"Symlink or escaping output path: {entry['path']}")
        if dest.exists():
            if dest.stat().st_size != entry["bytes"] or sha(dest) != entry["sha256"]:
                raise ValueError(f"Existing file differs; move it aside explicitly: {dest}")
            print("verified", entry["path"], flush=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".download-", dir=dest.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                with open_url(base + urllib.parse.quote(entry["path"], safe="/"), timeout=120) as response:
                    while chunk := response.read(1024 * 1024):
                        stream.write(chunk)
            temp = Path(temporary)
            if temp.stat().st_size != entry["bytes"] or sha(temp) != entry["sha256"]:
                raise ValueError(f"Download checksum mismatch: {entry['path']}")
            os.replace(temp, dest)
            print("downloaded", entry["path"], flush=True)
        finally:
            Path(temporary).unlink(missing_ok=True)
    print(json.dumps({"status": "verified", "files": len(selected), "output": str(output)}))

if __name__ == "__main__":
    main()
