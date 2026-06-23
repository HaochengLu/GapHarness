from __future__ import annotations

import unittest
from collections import Counter

from gapharness.compiler import compile_minimal_harness
from gapharness.profiler import profile_from_gold
from gapharness.registry import default_registry
from scripts.build_harness_challenge import build_tasks
from scripts.run_harness_exec20 import build_cases, case_to_task


class HarnessChallengeTests(unittest.TestCase):
    def test_harness_challenge_counts(self):
        tasks = build_tasks("2026-06-23")
        self.assertEqual(len(tasks), 200)
        self.assertEqual(len({task.task_id for task in tasks}), 200)
        self.assertEqual(
            Counter(task.category for task in tasks),
            {
                "minimal_pair": 50,
                "hard_tool_bait": 30,
                "sandbox_vs_real_side_effect": 40,
                "registry_absence": 30,
                "verification_evidence_trap": 30,
                "real_source_paraphrase": 20,
            },
        )

    def test_supported_harness_challenge_gold_compiles(self):
        registry = default_registry()
        tasks = build_tasks("2026-06-23")
        for task in tasks:
            harness = compile_minimal_harness(profile_from_gold(task), registry)
            if task.expected_status == "supported":
                self.assertEqual(harness.status, "supported", task.task_id)
            else:
                self.assertEqual(harness.status, "unsupported", task.task_id)

    def test_harness_exec_case_count_and_gold(self):
        registry = default_registry()
        cases = build_cases()
        self.assertEqual(len(cases), 20)
        for case in cases:
            task = case_to_task(case, "2026-06-23")
            harness = compile_minimal_harness(profile_from_gold(task), registry)
            self.assertEqual(harness.status, "supported")
            self.assertEqual(harness.cost, 12)


if __name__ == "__main__":
    unittest.main()
