#!/usr/bin/env python3
"""Run the existing September 29 depth tests that require no capture or model assets."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments/world_lobby_four_trajectory_20260929/code'))
from test_depth_pipeline import DepthPipelineTests

NAMES = [
    'test_window_schedule_anchors_end',
    'test_centrality_dedup_uses_earlier_window',
    'test_bilinear_sampling_requires_full_valid_support',
    'test_depth_metrics_and_missing_penalty',
    'test_optical_z_ray_definition',
]

if __name__ == '__main__':
    suite = unittest.TestSuite(DepthPipelineTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
