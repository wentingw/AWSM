#!/usr/bin/env python3
"""Read-only, standard-library audit of current article evidence (no simulation)."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text())


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10), (a, b)


def main():
    appearance = read('results/evaluation/appearance_five_views_20260925/report.json')
    original = {r['system']: r for r in read('results/rgb_metrics_five_views_mean.json')['rows']}
    for row in appearance['rows']:
        views = [v for v in appearance['per_view'] if v['system'] == row['system']]
        assert [v['keyframe_index'] for v in views] == [0, 36, 72, 108, 144]
        for field, mean in [('psnr_db', 'psnr_db_mean'), ('ssim', 'ssim_mean'), ('lpips_alex_v01', 'lpips_alex_v01_mean')]:
            close(sum(v[field] for v in views) / 5, row[mean])
        for metric in ['psnr_db_mean', 'ssim_mean']:
            close(original[row['system']][metric], row[metric])
        for v in views:
            for role in ['pred', 'gt']:
                assert hashlib.sha256((ROOT / v[role + '_path']).read_bytes()).hexdigest() == v[role + '_sha256']
    assert len(appearance['rows']) == 4 and len(appearance['per_view']) == 20

    combined = read('results/evaluation/tasks/m4_downstream_20260924/report.json')
    drone = read('results/evaluation/tasks/drone_M4_20260924/report.json')
    assert combined['scene_method'] == 'M4' and combined['drone'] == drone
    counts = {'episodes': 20, 'collision_free_candidate_arrivals': 0, 'collisions': 0,
              'planning_failed': 0, 'strict_rephotography_successes': 0, 'relaxed_rephotography_successes': 0}
    assert len(drone['episodes']) == 20
    for row in drone['episodes']:
        ep = f"experiments/tasks/drone_M4/replay_20260924/episode_{row['query_id']:02d}"
        summary = read(ep + '/summary.json')
        assert summary['status'] == row['flight_status']
        assert summary['query_pose_input'] is False and summary['GT_access'] is False
        arrived = row['flight_status'] == 'success'
        assert not arrived or summary['dynamics']['collision_steps'] == 0
        counts['collision_free_candidate_arrivals'] += arrived
        counts['collisions'] += row['flight_status'] == 'collision'
        counts['planning_failed'] += row['flight_status'] == 'planning_failed'
        for mode, position, angle in [('strict', .1, 5), ('relaxed', .25, 10)]:
            success = arrived and row['translation_error_m'] <= position and row['rotation_error_deg'] <= angle
            assert success == row[mode + '_rephotography_success']
            counts[mode + '_rephotography_successes'] += success
        assert (ROOT / ep / 'drone_trajectory.csv').is_file()
        assert (ROOT / ep / 'final_rgb.png').is_file()
    assert counts == drone['counts']
    for field, mean in drone['means'].items():
        close(sum(row[field] for row in drone['episodes']) / 20, mean)

    expected = {r['episode_id']: r['expected_target_id'] for r in read('results/evaluation/tasks/g1_M4_20260924/expected_targets.json')}
    visible = read('results/evaluation/tasks/g1_M4_20260924/visibility.json')
    visibility = {r['episode_id']: r for r in visible['episodes']}
    checks = read('revisions/m4_downstream_20260924/independent_g1_check.json')
    assert len(expected) == len(visibility) == len(checks['episodes']) == 20
    total = 0
    for row in checks['episodes']:
        i = row['episode_id']
        ep = f'experiments/tasks/g1_M4/replay_20260924/episode_{i:02d}'
        summary = read(ep + '/summary.json')
        assert summary['scene_method'] == 'M4' and summary['target_id'] == expected[i]
        assert summary['status'] == 'success' and summary['obstacle_contact_steps'] == 0 and not summary['fallen']
        assert row['correct_identity'] and row['navigation_verified']
        for name, key in [('summary.json', 'summary_sha256'), ('trajectory_full.csv', 'trajectory_full_sha256')]:
            assert hashlib.sha256((ROOT / ep / name).read_bytes()).hexdigest() == row[key]
        v = visibility[i]
        assert v['target_id'] == expected[i]
        close(v['target_pixel_count'] / v['sample_count'], v['target_pixel_fraction'])
        assert v['visible'] == (v['target_pixel_fraction'] >= visible['threshold_fraction'])
        total += bool(v['visible'])
    assert total == combined['g1']['counts']['verified_target_successes'] == 20
    for field, mean in combined['g1']['means'].items():
        close(sum(row[field] for row in checks['episodes']) / 20, mean)

    for page in ['blog/index.html', 'blog/en.html']:
        text = (ROOT / page).read_text()
        assert re.findall(r'<figure class="table-figure" id="table-(\d+)"', text) == [str(i) for i in range(1, 9)]
        assert len(re.findall(r'<table\b', text)) == 8
    print(json.dumps({'status': 'pass', 'scope': 'saved evidence, not new simulation or LPIPS inference',
                      'appearance_pairs_verified': 20, 'drone_counts': counts, 'g1_verified': total,
                      'article_tables_per_language': 8}, indent=2))


if __name__ == '__main__':
    main()
