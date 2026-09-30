#!/usr/bin/env python3
"""Copy the experiment's source and small companions into a new Git snapshot."""
import argparse
import ast
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {'versions', 'checks', 'logs', '__pycache__', '.tmp', '.mpl', '.cache'}
SKIP_FILES = {'input_access_log.json', 'revision_access_log.json',
              'recorded_author_commands.json', 'coordinator_handoff.json',
              'coordinator_tool_note.json', 'freeze_manifest.json',
              'final_freeze.json', 'final_candidate_hashes.json',
              'artifact_hashes.json', 'input_freeze.json'}
SECRETS = {
    'hf_token': r'hf_[A-Za-z0-9]{20,}',
    'github_token': r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})',
    'api_key': r'sk-[A-Za-z0-9_-]{20,}',
    'private_key': r'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    dest = args.repo.resolve() / 'experiments' / source.name
    if dest.exists():
        raise FileExistsError(f'Refusing to overwrite an existing snapshot: {dest}')
    chosen = set()

    def add(path):
        if path.is_file():
            if path.is_symlink():
                raise ValueError(f'Source symlink requires explicit review: {path}')
            chosen.add(path.relative_to(source))

    for path in source.iterdir():
        if path.suffix in {'.md', '.tsx'} or path.name == 'contract.json':
            add(path)
    for folder in ['code', 'astra_blender2/tools', 'astra_blender2/configs']:
        for path in (source / folder).rglob('*'):
            if not any(p in SKIP_DIRS for p in path.relative_to(source / folder).parts):
                if path.suffix in {'.py', '.md', '.json', '.yaml', '.yml'}:
                    add(path)
    for run in ['astra_blender', 'astra_blender2']:
        add(source / run / 'README.md')
        for method in ['M1', 'M2', 'M3', 'M4']:
            model = source / run / 'models' / method
            for path in model.rglob('*'):
                rel = path.relative_to(model)
                if any(p in SKIP_DIRS for p in rel.parts) or path.name in SKIP_FILES:
                    continue
                if path.suffix == '.py':
                    add(path)
                elif path.suffix in {'.json', '.md'} and path.stat().st_size <= 512 * 1024:
                    # Review summaries support interpretation; full mesh audit dumps are outputs.
                    if 'independent_review' not in rel.parts or path.name in {
                        'initial_review.json', 'initial_review.md',
                        'final_review.json', 'final_review.md',
                    }:
                        add(path)
    add(source / 'astra_blender/models/M3/analysis/model_from_input.npy')
    for path in (source / 'data/depth_samples').glob('*.json'):
        add(path)
    for method in ['M2', 'M3', 'M4']:
        add(source / 'packets' / method / 'packet.json')
    for method in ['M1', 'M2', 'M3', 'M4']:
        for name in ['packet.json', 'fixed_check_views/manifest.json', 'fixed_check_views/README.md']:
            add(source / 'astra_blender2/inputs' / method / name)
    for name in ['manifest.json', 'README.md']:
        add(source / 'fixed_check_views' / name)
    add(source / 'astra_blender2/provenance/check_generic_pair.py')
    for folder in ['publication/huggingface/space', 'astra_blender2/report/space']:
        for path in (source / folder).iterdir():
            if path.suffix in {'.html', '.css', '.js', '.md'}:
                add(path)
    entries = []
    for rel in sorted(chosen):
        data = (source / rel).read_bytes()
        if rel.suffix != '.npy':
            text = data.decode('utf-8')
            for kind, pattern in SECRETS.items():
                if re.search(pattern, text):
                    raise ValueError(f'Credential pattern ({kind}) found in {rel}; value withheld')
            if rel.suffix == '.py':
                ast.parse(text, filename=str(rel))
        entries.append({'path': rel.as_posix(), 'source': rel.as_posix(),
                        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    dest.mkdir(parents=True)
    for entry in entries:
        rel = Path(entry['path']); target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target)
        assert hashlib.sha256(target.read_bytes()).hexdigest() == entry['sha256']
    manifest = {
        'snapshot_date': datetime.now(timezone.utc).isoformat(),
        'source_workspace': str(source),
        'scope': 'Trajectory/depth pipeline, both Blender authoring runs, evaluation/publication tools, small configuration and construction companions',
        'copy_policy': 'byte-identical source files; repository helpers and documentation tracked separately',
        'excluded': ['authentication state and secrets', 'private agent session logs',
                     'RGB/depth caches and GT geometry', 'Blender/GLB model binaries',
                     'rendered images and videos', 'weights and runtime environments',
                     'duplicate version/reproduction/backup trees',
                     'large generated mesh audit dumps', 'vendored viewer bundle'],
        'files': entries,
    }
    (dest / 'source_snapshot.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'destination': str(dest), 'files': len(entries),
                      'bytes': sum(x['bytes'] for x in entries),
                      'python_files': sum(x['path'].endswith('.py') for x in entries)}, indent=2))


if __name__ == '__main__':
    main()
