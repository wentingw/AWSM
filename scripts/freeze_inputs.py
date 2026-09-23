#!/usr/bin/env python3
"""Freeze a read-only input inventory; keep truth outside reconstruction packets."""
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent
CAPTURE = LEGACY / 'vio-reconstruction/sessions/stable_orbit_20260921T044401'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    data = ROOT / 'data/world_lobby'
    for name in ['rgb_all', 'rgb_180', 'calibration']:
        (data / name).mkdir(parents=True, exist_ok=True)
    paths = sorted((CAPTURE / 'inputs/cam0/data').glob('*.png'), key=lambda p: int(p.stem))
    assert len(paths) == 8999, len(paths)
    timestamps = [int(p.stem) for p in paths]
    assert all(b > a for a, b in zip(timestamps, timestamps[1:]))
    frames = []
    for i, p in enumerate(paths):
        dest = data / 'rgb_all' / f'{i:06d}_{p.stem}.png'
        if dest.is_symlink():
            assert dest.resolve() == p.resolve()
        elif dest.exists():
            raise RuntimeError(f'Unexpected non-link input: {dest}')
        else:
            dest.symlink_to(p)
        row = dict(index=i, timestamp_ns=timestamps[i], elapsed_s=(timestamps[i]-timestamps[0])/1e9,
                   source=str(p), rgb=str(dest), sha256=sha(p), size_bytes=p.stat().st_size)
        if i % 50 == 0:
            k = i // 50
            selected = data / 'rgb_180' / f'{k:06d}_{p.stem}.png'
            if not selected.exists():
                selected.symlink_to(p)
            assert selected.resolve() == p.resolve()
            row.update(keyframe_index=k, sampled_rgb=str(selected))
        frames.append(row)
        if i % 1000 == 0:
            print(f'Hashed {i+1}/{len(paths)} RGB files', flush=True)
    calibration = CAPTURE / 'inputs/calibration.json'
    (data / 'calibration/camera_imu.json').write_bytes(calibration.read_bytes())
    inputs = dict(created_utc=datetime.now(timezone.utc).isoformat(), capture=str(CAPTURE),
                  input_contract='RGB + calibration + raw IMU; truth intentionally excluded',
                  frame_count=len(frames), frames=frames,
                  calibration=dict(path=str(calibration), sha256=sha(calibration)),
                  imu=[dict(path=str(p), sha256=sha(p)) for p in sorted((CAPTURE/'inputs/imu0').glob('*.csv'))])
    (ROOT/'manifests/input_inventory.json').write_text(json.dumps(inputs, indent=2)+'\n')
    selected = [f for f in frames if 'keyframe_index' in f]
    assert len(selected) == 180
    # RGB-only packet deliberately omits calibration, IMU, poses and all truth.
    (data/'rgb_180_manifest.json').write_text(json.dumps(dict(frames=selected, input_contract='RGB only'),indent=2)+'\n')
    (data/'rgb_all_manifest.json').write_text(json.dumps(dict(frames=frames, input_contract='RGB only'),indent=2)+'\n')
    figure_ids=[0,36,72,108,144]
    figure=dict(selection_rule='five fixed input indices at 20-percent temporal intervals, before any new result',
                selected_keyframe_indices=figure_ids, frames=[selected[i] for i in figure_ids],
                columns=['M1','M2','M3','GT'], rows=5, held_out=False)
    (ROOT/'configs/figure_views.json').write_text(json.dumps(figure,indent=2)+'\n')
    print(json.dumps(dict(status='FROZEN',rgb=len(frames),sampled=len(selected),figures=figure_ids)))


if __name__ == '__main__':
    main()
