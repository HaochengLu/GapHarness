from __future__ import annotations

import unittest

from gapharness.compiler import compile_minimal_harness, dominance_prune
from gapharness.profiler import profile_heuristic
from gapharness.registry import default_registry
from gapharness.schema import ModuleSpec, ProfilerOutput, frozen


class CompilerTests(unittest.TestCase):
    def test_current_fact_uses_retrieval_and_verification(self):
        profile = profile_heuristic("Find the latest public announcement today and summarize it with sources.")
        harness = compile_minimal_harness(profile, default_registry())
        self.assertEqual(harness.status, "supported")
        self.assertIn("web_retrieval", harness.modules)
        self.assertIn("source_span_checker", harness.modules)
        self.assertIn("contract_verifier", harness.modules)

    def test_sandbox_action_pulls_permission_dependency(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "State", "Verification"]),
            required_capabilities=frozen(["diff", "contract_check"]),
        )
        harness = compile_minimal_harness(profile, default_registry())
        self.assertEqual(harness.status, "supported")
        self.assertIn("sandbox_file_editor", harness.modules)
        self.assertIn("permission_gate", harness.modules)

    def test_unsupported_missing_capability(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "Control"]),
            required_capabilities=frozen(["real_world_side_effect"]),
        )
        harness = compile_minimal_harness(profile, default_registry())
        self.assertEqual(harness.status, "unsupported")
        self.assertIn("real_world_side_effect", harness.missing_capabilities)

    def test_optimized_matches_bruteforce_on_default_registry(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "Control", "Execution", "Observation", "State", "Verification"]),
            required_capabilities=frozen(
                [
                    "workspace_inspection",
                    "execution",
                    "execution_log",
                    "durable_state",
                    "diff",
                    "sandbox_action",
                    "permission",
                    "contract_check",
                ]
            ),
        )
        optimized = compile_minimal_harness(profile, default_registry(), strategy="optimized")
        brute = compile_minimal_harness(profile, default_registry(), strategy="bruteforce")
        self.assertEqual(optimized.status, brute.status)
        self.assertEqual(optimized.modules, brute.modules)
        self.assertEqual(optimized.cost, brute.cost)
        self.assertEqual(optimized.certificate["compiler_algorithm"], "dominance_pruned_branch_and_bound")
        self.assertTrue(optimized.certificate["dependencies_satisfied"])

    def test_dominance_pruning_removes_strictly_dominated_module(self):
        registry = {
            "wide": ModuleSpec(
                name="wide",
                provides=frozen(["Observation", "Verification"]),
                capabilities=frozen(["evidence_sources", "source_spans"]),
                cost=2,
            ),
            "narrow": ModuleSpec(
                name="narrow",
                provides=frozen(["Observation"]),
                capabilities=frozen(["evidence_sources"]),
                cost=3,
            ),
        }
        active, removed = dominance_prune(("narrow", "wide"), registry)
        self.assertEqual(active, ("wide",))
        self.assertEqual(removed[0]["removed"], "narrow")


if __name__ == "__main__":
    unittest.main()
