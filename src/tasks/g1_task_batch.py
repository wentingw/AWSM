#!/usr/bin/env python3
"""Run the frozen-protocol G1 language-navigation episode set."""
import argparse, json, os, subprocess, sys
from pathlib import Path

INSTRUCTIONS = [
    "Find the green chair near a window", "Find the table near a plant",
    "Find a plant", "Find the reception desk", "Find a round mirror",
    "Go to the green chair near a window", "Go to the table near a plant",
    "Go to a plant", "Go to the reception desk", "Go to a round mirror",
    "Please find the green chair near a window", "Please find the table near a plant",
    "Please find a plant", "Please find the reception desk", "Please find a round mirror",
    "Look for the green chair near a window", "Look for the table near a plant",
    "Look for a plant", "Look for the reception desk", "Look for a round mirror",
    "Go to and stop in front of the green chair near a window",
    "Go to and stop in front of the table near a plant", "Go to and stop in front of a plant",
    "Go to and stop in front of the reception desk", "Go to and stop in front of a round mirror",
    "Please look for the green chair near a window", "Please look for the table near a plant",
    "Please look for a plant", "Please look for the reception desk", "Please look for a round mirror",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--start-x', type=float, required=True)
    ap.add_argument('--start-y', type=float, required=True)
    ap.add_argument('--start-yaw', type=float, default=0.0)
    ap.add_argument('--seconds', type=float, default=90.0)
    ap.add_argument('--python', type=Path, required=True)
    a = ap.parse_args(); root = Path(__file__).resolve().parents[2]
    out = a.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy(); env['MUJOCO_GL'] = 'osmesa'
    osmesa = root / 'runtime/osmesa/extracted/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH'] = str(osmesa) + ':' + env.get('LD_LIBRARY_PATH', '')
    records = []
    for i, instruction in enumerate(INSTRUCTIONS):
        ep = out / f'episode_{i:02d}'; ep.mkdir(parents=True, exist_ok=True)
        request = {'episode_id': i, 'instruction': instruction,
                   'start_xy': [a.start_x, a.start_y], 'start_yaw': a.start_yaw,
                   'spawn_source': 'model camera trace frame 12 first free supported'}
        (ep / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
        cmd = [str(a.python), str(root/'src/tasks/g1_episode.py'), '--scene', str(a.scene),
               '--request', str(ep/'request.json'), '--out', str(ep), '--seconds', str(a.seconds)]
        p = subprocess.run(cmd, cwd=root, env=env, text=True, capture_output=True)
        (ep/'runner.stdout').write_text(p.stdout); (ep/'runner.stderr').write_text(p.stderr)
        summary = json.loads((ep/'summary.json').read_text()) if (ep/'summary.json').exists() else {'status':'runner_error'}
        records.append({'episode_id': i, 'instruction': instruction, 'status': summary.get('status'),
                        'path': str(ep), 'returncode': p.returncode})
        print(json.dumps(records[-1]), flush=True)
    counts = {}
    for r in records: counts[r['status']] = counts.get(r['status'], 0) + 1
    report = {'protocol': str(root/'experiments/tasks/frozen_inputs/protocol.json'),
              'scene': str(a.scene.resolve()), 'episodes': records, 'counts': counts,
              'total': len(records), 'spawn': {'start_xy':[a.start_x,a.start_y], 'start_yaw':a.start_yaw,
              'source':'camera frame 12 first free and floor-supported'},
              'language_scope':'30 constrained English paraphrases over 5 unique semantic goals; correlated',
              'limitations':['frozen conservative AABB collision world','simulator-state-oracle localization',
                             'constrained category/attribute/near grounding','no GT-world transfer claim']}
    (out/'batch_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'counts': counts, 'summary': str(out/'batch_summary.json')}))
    return 0
if __name__ == '__main__': raise SystemExit(main())
