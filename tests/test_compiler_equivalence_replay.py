"""Tests for the dominance-bearing replay track and honest coverage labelling.

These cover two additions:

1. ``gapharness.dominance_registry`` -- a registry where dominance pruning
   genuinely fires, and where the optimized compiler must stay extensionally
   equal to an independent brute-force reference.
2. ``scripts.run_compiler_equivalence_replay`` -- the replay must classify each
   row as compiler-reinvoked / reconstructed-baseline / router-skipped and only
   count genuine compiler invocations toward the equivalence N.
"""

from __future__ import annotations

import unittest

from gapharness.compiler import compile_minimal_harness, dominance_prune
from gapharness.dominance_registry import (
    DOMINANCE_MODULES,
    dominance_registry,
    dominated_pairs,
    replay_profiles,
)
from gapharness.schema import TaskExample, frozen

from scripts import run_compiler_equivalence_replay as replay


class DominanceRegistryTests(unittest.TestCase):
    def test_dominance_actually_fires(self):
        registry = dominance_registry()
        names = sorted(registry)
        active, removed = dominance_prune(names, registry)
        removed_pairs = tuple(sorted((r["removed"], r["dominated_by"]) for r in removed))
        self.assertEqual(removed_pairs, dominated_pairs())
        self.assertGreaterEqual(len(removed), 1)
        for dominated, _dominator in dominated_pairs():
            self.assertNotIn(dominated, active)

    def test_optimized_equals_inline_bruteforce_reference(self):
        registry = dominance_registry()
        for name, profile in replay_profiles():
            optimized = compile_minimal_harness(profile, registry, strategy="optimized")
            reference = replay._bruteforce_reference(profile, registry)
            self.assertEqual(optimized.status, reference["status"], name)
            self.assertEqual(tuple(sorted(optimized.modules)), reference["modules"], name)
            self.assertEqual(optimized.cost, reference["cost"], name)

    def test_optimized_equals_compiler_bruteforce_strategy(self):
        # Cross-check against the compiler's own brute-force entrypoint too.
        registry = dominance_registry()
        for name, profile in replay_profiles():
            optimized = compile_minimal_harness(profile, registry, strategy="optimized")
            brute = compile_minimal_harness(profile, registry, strategy="bruteforce")
            self.assertEqual(optimized.status, brute.status, name)
            self.assertEqual(optimized.modules, brute.modules, name)
            self.assertEqual(optimized.cost, brute.cost, name)

    def test_search_bearing_profiles_report_nonzero_dominated_and_nodes(self):
        registry = dominance_registry()
        saw_dominated = False
        saw_nodes = False
        for _name, profile in replay_profiles():
            cert = compile_minimal_harness(profile, registry).to_json().get("certificate", {})
            if int(cert.get("dominated_module_count", 0)) > 0:
                saw_dominated = True
            if int(cert.get("search_stats", {}).get("nodes_visited", 0)) > 0:
                saw_nodes = True
        self.assertTrue(saw_dominated, "dominance pruning never fired")
        self.assertTrue(saw_nodes, "branch-and-bound never visited a node")

    def test_dominated_pairs_in_registry(self):
        names = {module.name for module in DOMINANCE_MODULES}
        for dominated, dominator in dominated_pairs():
            self.assertIn(dominated, names)
            self.assertIn(dominator, names)


class DominanceTrackTests(unittest.TestCase):
    def test_run_dominance_track_reports_nonzero_and_no_mismatch(self):
        result = replay.run_dominance_track()
        self.assertEqual(result["mismatches"], 0)
        self.assertGreater(result["max_dominated"], 0)
        self.assertGreater(result["max_nodes"], 0)
        self.assertEqual(len(result["rows"]), len(replay_profiles()))
        for row in result["rows"]:
            self.assertFalse(row["mismatch"], row["profile"])


class CoverageClassificationTests(unittest.TestCase):
    def _task(self, **overrides):
        base = dict(
            task_id="t-1",
            query="Find the latest public price today and cite sources.",
            gold_obligations=frozen(["Observation", "Verification"]),
            required_capabilities=frozen(["evidence_sources", "source_spans"]),
            oracle_minimal_harness=("web_retrieval", "source_span_checker"),
            success_checker="gold_coverage",
            expected_failure_if_direct="stale",
            risk_level="low",
            category="current_fact",
            expected_status="supported",
        )
        base.update(overrides)
        return TaskExample(**base)

    def test_stored_profile_is_genuine(self):
        task = self._task()
        row = {
            "task": task.to_json(),
            "harness": {"status": "supported", "modules": [], "cost": 0},
            "profile": {
                "obligations": ["Observation"],
                "required_capabilities": ["evidence_sources"],
            },
            "system": "selected_llm_gap_harness",
        }
        _harness, kind, detail = replay.compile_new_harness(row, task)
        self.assertEqual(kind, replay.KIND_GENUINE)
        self.assertEqual(detail, "stored_profile")

    def test_router_route_is_skipped(self):
        task = self._task()
        row = {
            "task": task.to_json(),
            "harness": {"status": "supported", "modules": [], "cost": 0},
            "route": {"expected_status": "supported", "selected_modules": []},
            "system": "llm_tool_router",
        }
        _harness, kind, _detail = replay.compile_new_harness(row, task)
        self.assertEqual(kind, replay.KIND_ROUTER)

    def test_gapharness_without_profile_is_genuine_reprofile(self):
        task = self._task()
        row = {
            "task": task.to_json(),
            "harness": {"status": "supported", "modules": [], "cost": 0},
            "system": "gapharness",
        }
        _harness, kind, detail = replay.compile_new_harness(row, task)
        self.assertEqual(kind, replay.KIND_GENUINE)
        self.assertTrue(detail.startswith("reprofiled_gold"))

    def test_baseline_systems_are_reconstructed_not_genuine(self):
        task = self._task()
        for system in ("direct", "tool_router", "always_full", "oracle_minimal"):
            row = {
                "task": task.to_json(),
                "harness": {"status": "supported", "modules": [], "cost": 0},
                "system": system,
            }
            _harness, kind, detail = replay.compile_new_harness(row, task)
            self.assertEqual(kind, replay.KIND_RECONSTRUCTED, system)
            self.assertEqual(detail, "baseline:%s" % system)

    def test_replay_row_excludes_nongenuine_from_change_flags(self):
        task = self._task()
        # Reconstructed baseline whose harness differs from old -> must NOT be
        # flagged as a compiler-equivalence change, and must not count toward N.
        row = {
            "task": task.to_json(),
            "harness": {"status": "unsupported", "modules": ["web_retrieval"], "cost": 99},
            "system": "always_full",
        }
        out = replay.replay_row("label", __import__("pathlib").Path("x"), row)
        self.assertFalse(out["compiler_reinvoked"])
        self.assertFalse(out["status_changed"])
        self.assertFalse(out["modules_changed"])
        self.assertFalse(out["cost_changed"])

    def test_equivalence_count_only_counts_genuine(self):
        rows = [
            {"compiler_reinvoked": True, "replay_kind": replay.KIND_GENUINE},
            {"compiler_reinvoked": True, "replay_kind": replay.KIND_GENUINE},
            {"compiler_reinvoked": False, "replay_kind": replay.KIND_RECONSTRUCTED},
            {"compiler_reinvoked": False, "replay_kind": replay.KIND_ROUTER},
        ]
        self.assertEqual(replay.equivalence_count(rows), 2)
        breakdown = replay.coverage_breakdown(rows)
        self.assertEqual(breakdown[replay.KIND_GENUINE], 2)
        self.assertEqual(breakdown[replay.KIND_RECONSTRUCTED], 1)
        self.assertEqual(breakdown[replay.KIND_ROUTER], 1)


if __name__ == "__main__":
    unittest.main()
