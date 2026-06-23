from __future__ import annotations

import unittest

from gapharness.llm_profiler import apply_registry_guard, canonicalize_profile, infer_profile_status
from gapharness.profiler import profile_heuristic
from gapharness.schema import ProfilerOutput, frozen


class LLMProfilerCanonicalizationTests(unittest.TestCase):
    def test_false_clarification_removed_for_specific_latest_query(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Observation", "Verification"]),
            required_capabilities=frozen(["evidence_sources"]),
            unsupported_possibility=("clarification_needed",),
        )
        normalized = canonicalize_profile(profile, "Find the latest public announcement for ExampleProduct 1 with sources.")
        self.assertNotIn("clarification_needed", normalized.unsupported_possibility)
        self.assertIn("source_spans", normalized.required_capabilities)

    def test_action_adds_control_state_and_permissions(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action"]),
            required_capabilities=frozen([]),
        )
        normalized = canonicalize_profile(profile, "Create file sandbox_note.txt in the sandbox workspace.")
        self.assertTrue({"Action", "State", "Control"}.issubset(normalized.obligations))
        self.assertTrue({"diff", "sandbox_action", "permission"}.issubset(normalized.required_capabilities))

    def test_ambiguous_query_keeps_clarification(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "Control"]),
            required_capabilities=frozen(["permission"]),
            unsupported_possibility=("clarification_needed",),
        )
        normalized = canonicalize_profile(profile, "Update whichever file is best and make the appropriate change.")
        self.assertIn("clarification_needed", normalized.unsupported_possibility)

    def test_exact_arithmetic_forces_execution(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=True,
            obligations=frozen([]),
            required_capabilities=frozen([]),
        )
        normalized = canonicalize_profile(profile, "For case 4, calculate exactly 41 * 15.")
        self.assertIn("Execution", normalized.obligations)
        self.assertIn("execution", normalized.required_capabilities)

    def test_llm_mode_names_are_reserved_for_runtime(self):
        # Keep the deterministic profiler sanity check close to LLM profiler tests
        # so mode additions do not accidentally remove core canonicalization needs.
        profile = profile_heuristic("Calculate exactly 12 * 9 and validate the answer.")
        self.assertIn("Execution", profile.obligations)
        self.assertIn("Verification", profile.obligations)

    def test_registry_guard_removes_real_side_effect_for_sandbox_action(self):
        raw = canonicalize_profile(
            ProfilerOutput(
                direct_llm_sufficient=False,
                obligations=frozen(["Action", "Control", "Verification"]),
                required_capabilities=frozen(["real_world_side_effect"]),
                risk_level="high",
            ),
            "Create a patch in the sandbox workspace and update only the mock config file.",
        )
        self.assertEqual("unsupported", infer_profile_status(raw))
        guarded, metadata = apply_registry_guard(
            raw,
            "Create a patch in the sandbox workspace and update only the mock config file.",
        )
        self.assertNotIn("real_world_side_effect", guarded.required_capabilities)
        self.assertEqual("supported", infer_profile_status(guarded))
        self.assertIn("converted_unsupported_to_supported", metadata["guard_actions"])

    def test_registry_guard_preserves_real_external_side_effect(self):
        raw = canonicalize_profile(
            ProfilerOutput(
                direct_llm_sufficient=False,
                obligations=frozen(["Action", "Control"]),
                required_capabilities=frozen([]),
            ),
            "Deploy to production now and restart the real service.",
        )
        guarded, metadata = apply_registry_guard(raw, "Deploy to production now and restart the real service.")
        self.assertIn("real_world_side_effect", guarded.required_capabilities)
        self.assertEqual("unsupported", infer_profile_status(guarded))
        self.assertIn("added_real_world_side_effect_for_real_external_action", metadata["guard_actions"])

    def test_registry_guard_sets_clarify_for_ambiguous_action_target(self):
        raw = canonicalize_profile(
            ProfilerOutput(
                direct_llm_sufficient=False,
                obligations=frozen(["Action", "Control"]),
                required_capabilities=frozen(["sandbox_action", "permission", "diff"]),
            ),
            "Fix the project and make the best change.",
        )
        guarded, metadata = apply_registry_guard(raw, "Fix the project and make the best change.")
        self.assertIn("clarification_needed", guarded.unsupported_possibility)
        self.assertEqual("clarify", infer_profile_status(guarded))
        self.assertIn("set_clarification_for_ambiguous_action_target", metadata["guard_actions"])

    def test_registry_guard_clears_no_tool_language_bait(self):
        raw = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Observation", "Execution"]),
            required_capabilities=frozen(["evidence_sources", "execution"]),
            risk_level="medium",
        )
        guarded, metadata = apply_registry_guard(
            raw,
            "Without browsing, running code, or reading files, brainstorm five paper titles.",
        )
        self.assertTrue(guarded.direct_llm_sufficient)
        self.assertFalse(guarded.obligations)
        self.assertFalse(guarded.required_capabilities)
        self.assertIn("cleared_external_obligations_for_no_tool_language_request", metadata["guard_actions"])


if __name__ == "__main__":
    unittest.main()
