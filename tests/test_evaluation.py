from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gapharness.evaluation import run_benchmark, summarize_results
from gapharness.seed_data import build_seed_tasks


class EvaluationTests(unittest.TestCase):
    def test_all_systems_run_on_seed_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bench.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for task in build_seed_tasks()[:12]:
                    handle.write(json.dumps(task.to_json(), sort_keys=True) + "\n")
            rows = run_benchmark(str(path), system="all", profiler="gold")
            summary = summarize_results(rows)
            self.assertIn("gapharness", summary)
            self.assertIn("always_full", summary)
            self.assertIn("avg_cost_delta", summary["gapharness"])
            self.assertIn("avg_excess_cost", summary["gapharness"])
            self.assertGreaterEqual(summary["gapharness"]["success_rate"], 0.99)
            self.assertGreater(summary["always_full"]["avg_cost"], summary["gapharness"]["avg_cost"])
            self.assertGreaterEqual(summary["direct"]["avg_excess_cost"], 0.0)

    def test_gapharness_gold_profiler_solves_full_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bench.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for task in build_seed_tasks():
                    handle.write(json.dumps(task.to_json(), sort_keys=True) + "\n")
            rows = run_benchmark(str(path), system="all", profiler="gold")
            summary = summarize_results(rows)
            self.assertEqual(summary["gapharness"]["success_rate"], 1.0)
            self.assertEqual(summary["gapharness"]["avg_minimality_regret"], 0.0)
            self.assertLess(summary["direct"]["avg_cost_delta"], 0.0)
            self.assertEqual(summary["direct"]["avg_excess_cost"], 0.0)


if __name__ == "__main__":
    unittest.main()
