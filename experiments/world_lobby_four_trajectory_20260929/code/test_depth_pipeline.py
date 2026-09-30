#!/usr/bin/env python3
"""Unit and contract tests for the World Lobby DA3 depth pipeline."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from depth_pipeline import (
    BASE,
    METHODS,
    bilinear_sample,
    camera_rows,
    choose_central_observations,
    depth_metrics,
    load_pose_stream,
    windows,
)


class DepthPipelineTests(unittest.TestCase):
    def test_common_manifests_are_disjoint_and_complete(self):
        modelling = json.loads(
            (BASE / "data/depth_samples/modeling_180.json").read_text()
        )
        evaluation = json.loads(
            (BASE / "data/depth_samples/eval_500.json").read_text()
        )
        self.assertEqual(modelling["frame_count"], 180)
        self.assertEqual(evaluation["frame_count"], 500)
        model_indices = {frame["source_index"] for frame in modelling["frames"]}
        eval_indices = {frame["source_index"] for frame in evaluation["frames"]}
        self.assertFalse(model_indices & eval_indices)
        self.assertGreaterEqual(min(model_indices | eval_indices), 245)
        self.assertLessEqual(max(model_indices | eval_indices), 4498)
        self.assertTrue(
            all(Path(frame["image"]).is_file() for frame in modelling["frames"])
        )

    def test_all_methods_cover_both_schedules(self):
        wanted = []
        for name in ("modeling_180", "eval_500"):
            manifest = json.loads(
                (BASE / f"data/depth_samples/{name}.json").read_text()
            )
            wanted.extend(frame["timestamp_ns"] for frame in manifest["frames"])
        for method_id in METHODS:
            timestamps, _, _ = load_pose_stream(method_id)
            self.assertTrue(set(wanted).issubset(set(timestamps.tolist())))

    def test_camera_source_indices_start_at_zero(self):
        rows = camera_rows()
        self.assertEqual(rows[0]["source_index"], 0)
        self.assertEqual(rows[-1]["source_index"], 4498)

    def test_window_schedule_anchors_end(self):
        schedule = windows(180)
        self.assertEqual(schedule[0], [0, 1, 2, 3])
        self.assertEqual(schedule[-1], [176, 177, 178, 179])
        self.assertEqual(len(schedule), 89)
        self.assertEqual(len(windows(500)), 249)

    def test_centrality_dedup_uses_earlier_window(self):
        records = [
            {"sample_index": 2, "centrality": 0, "window_index": 0},
            {"sample_index": 2, "centrality": 1, "window_index": 1},
            {"sample_index": 2, "centrality": 1, "window_index": 2},
        ]
        chosen = choose_central_observations(records)
        self.assertEqual(chosen[2]["window_index"], 1)

    def test_bilinear_sampling_requires_full_valid_support(self):
        image = np.arange(9, dtype=float).reshape(3, 3)
        valid = np.ones((3, 3), dtype=bool)
        value, support = bilinear_sample(
            image, np.asarray([0.5]), np.asarray([0.5]), valid
        )
        self.assertTrue(support[0])
        self.assertAlmostEqual(value[0], 2.0)
        valid[1, 1] = False
        value, support = bilinear_sample(
            image, np.asarray([0.5]), np.asarray([0.5]), valid
        )
        self.assertFalse(support[0])
        self.assertTrue(np.isnan(value[0]))

    def test_depth_metrics_and_missing_penalty(self):
        truth = np.asarray([1.0, 2.0, 4.0, 8.0])
        prediction = np.asarray([1.0, 2.2, np.nan, 10.0])
        metrics = depth_metrics(prediction, truth, missing_penalty_m=30.0)
        self.assertEqual(metrics["pixels_domain"], 4)
        self.assertEqual(metrics["pixels_valid"], 3)
        self.assertAlmostEqual(metrics["valid_coverage"], 0.75)
        self.assertGreater(metrics["missing_penalty_mae_m"], metrics["mae_m"])
        self.assertLessEqual(metrics["delta1"], metrics["delta2"])
        self.assertLessEqual(metrics["delta2"], metrics["delta3"])

    def test_optical_z_ray_definition(self):
        fx = fy = 100.0
        cx = cy = 50.0
        uv = np.asarray([[60.0, 70.0]])
        ray = np.column_stack(
            [(uv[:, 0] - cx) / fx, (uv[:, 1] - cy) / fy, np.ones(1)]
        )
        distance = 5.0 * np.linalg.norm(ray, axis=1)
        recovered_z = distance / np.linalg.norm(ray, axis=1)
        self.assertAlmostEqual(float(recovered_z[0]), 5.0)


if __name__ == "__main__":
    unittest.main()
