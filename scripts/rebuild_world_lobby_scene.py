#!/usr/bin/env python3
"""Rebuild one saved September 29 scene in a separate directory, without renders."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'experiments/world_lobby_four_trajectory_20260929/astra_blender2/models'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['M1', 'M2', 'M3', 'M4'], required=True)
    parser.add_argument('--blender', default=os.environ.get('BLENDER_PATH', 'blender'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    executable = shutil.which(args.blender)
    if not executable:
        parser.error('Blender not found; supply --blender /path/to/blender')
    source = MODELS / args.method
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('Use an output directory outside this repository')
    if output.exists():
        parser.error('Output directory already exists; choose a new directory')
    output.mkdir(parents=True)
    for file in source.rglob('*'):
        rel = file.relative_to(source)
        if file.is_file() and not any(x in {'independent_review', '__pycache__'} for x in rel.parts):
            if file.suffix in {'.py', '.json', '.npy'}:
                target = output / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, target)
    for name in ['checks', 'analysis']:
        (output / name).mkdir(exist_ok=True)
    cmd = [executable, '--background', '--factory-startup', '--threads', '2',
           '--python-exit-code', '1', '--python', str(output / 'build_scene.py')]
    with (output / 'rebuild.log').open('w') as log:
        subprocess.run(cmd, cwd=output, stdout=log, stderr=subprocess.STDOUT, check=True)
    for name in ['scene.blend', 'scene.glb', 'objects.json', 'colliders.json']:
        if not (output / name).is_file():
            raise RuntimeError(f'Builder did not produce {name}; inspect {output / "rebuild.log"}')
    print(f'Rebuilt {args.method}: {output}\nNo visual renders or Astra reasoning were run.')


if __name__ == '__main__':
    main()
