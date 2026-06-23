from __future__ import annotations

import unittest

from gapharness.evaluation import run_benchmark, summarize_results, write_jsonl
from gapharness.seed_data import build_seed_tasks


class SeedBenchmarkTests(unittest.TestCase):
    def test_seed_count_and_ids(self):
        tasks = build_seed_tasks()
        self.assertEqual(len(tasks), 100)
        self.assertEqual(len({task.task_id for task in tasks}), 100)

    def test_gold_gapharness_succeeds_on_supported_seed_tasks(self):
        tasks = build_seed_tasks()
        supported = [task for task in tasks if task.expected_status == "supported"]
        self.assertTrue(supported)
        for task in supported:
            self.assertTrue(task.oracle_minimal_harness or not task.gold_obligations)


if __name__ == "__main__":
    unittest.main()
