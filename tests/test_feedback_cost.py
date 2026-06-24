"""Tests for the honest feedback-cost analysis and the de-rigged phase6 script.

These tests guard milestone M4 / blocker B3:

1. The rigged, certificate-keyed proxies must stay deleted from
   ``scripts/run_phase6_reviewer_evidence.py`` (no metric may be a function of a
   hardcoded certificate constant).
2. ``scripts/run_feedback_cost_analysis.py`` must run on the ALREADY-CACHED
   feedback-level replay rows and produce an honest table where medium,
   non-leaky feedback is the headline and no coverage win is manufactured.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

import scripts.run_feedback_cost_analysis as fca

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE6_SCRIPT = REPO_ROOT / "scripts" / "run_phase6_reviewer_evidence.py"
REPLAY_ROWS = REPO_ROOT / "outputs" / "phase6_reviewer_evidence" / "feedback_levels" / "feedback_level_replay_rows.jsonl"
SUMMARY_ROWS = REPO_ROOT / "outputs" / "phase6_reviewer_evidence" / "feedback_levels" / "feedback_level_summary.jsonl"


# The exact rigged identifiers that previously keyed metrics on certificate
# presence via hardcoded constants. They must not exist as live code anymore.
RIGGED_FUNCTIONS = ("debug_work_proxy", "cause_localized", "diagnostic_accuracy_proxy")
RIGGED_FIELDS = (
    "scripted_audit_accuracy_proxy",
    "debug_work_units_proxy",
    "missing_cause_localized",
)
# A hardcoded certificate constant pattern: the original 2.0-vs-0.6 route penalty.
RIGGED_CONSTANT_PATTERN = re.compile(r"if\s+not\s+has_certificate.*else", re.DOTALL)


def _live_source(path: Path) -> str:
    """Return the source with comments and docstrings stripped.

    A removed function being *mentioned* in a comment is fine; what is forbidden
    is the rigged code existing as a live definition or live expression.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    # Collect docstring node ids so we can drop them.
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None and node.body and isinstance(node.body[0], ast.Expr):
                docstrings.add(id(node.body[0]))
    # ast.unparse drops comments entirely; we additionally skip docstrings by
    # blanking them. Simpler: just unparse, which already removes comments.
    return ast.unparse(tree)


class DeriggedPhase6Test(unittest.TestCase):
    def test_phase6_script_imports_without_rigged_functions(self) -> None:
        import scripts.run_phase6_reviewer_evidence as phase6

        for name in RIGGED_FUNCTIONS:
            self.assertFalse(
                hasattr(phase6, name),
                "rigged function %s must be deleted from phase6 script" % name,
            )

    def test_no_rigged_function_definitions_in_live_code(self) -> None:
        tree = ast.parse(PHASE6_SCRIPT.read_text(encoding="utf-8"))
        defined = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in RIGGED_FUNCTIONS:
            self.assertNotIn(name, defined, "rigged function %s must not be defined" % name)

    def test_no_rigged_constant_in_live_code(self) -> None:
        live = _live_source(PHASE6_SCRIPT)
        # The certificate-keyed route penalty constant must be gone from live code.
        self.assertIsNone(
            RIGGED_CONSTANT_PATTERN.search(live),
            "a metric still branches on has_certificate via a hardcoded constant",
        )
        # The rigged output field names must not be emitted by live code.
        for field in RIGGED_FIELDS:
            self.assertNotIn(
                field,
                live,
                "rigged output field %s must not appear in live phase6 code" % field,
            )

    def test_certificate_utility_row_has_no_certificate_keyed_metric(self) -> None:
        import scripts.run_phase6_reviewer_evidence as phase6

        # Build two identical fake rows differing ONLY in certificate presence;
        # every objectively-derivable metric must be identical, proving no field
        # is a function of certificate presence.
        base = {
            "metrics": {"success": True},
            "verifier_passed": True,
            "minimality_report": {"redundant_modules": ["x"], "redundancy": 0.25, "all_modules_necessary": False},
            "harness": {"modules": ["a", "b"], "certificate": {}},
            "verifier_failures": [],
        }
        with_cert = dict(base, harness={"modules": ["a", "b"], "certificate": {"algorithm": "z"}})
        row_no = phase6.certificate_utility_row("d", "s", [base], cert_expected=False)
        row_yes = phase6.certificate_utility_row("d", "s", [with_cert], cert_expected=False)
        for key in ("harness_success", "redundant_modules", "redundancy_rate", "all_modules_necessary_rate"):
            self.assertEqual(
                row_no[key],
                row_yes[key],
                "metric %s changed with certificate presence -> still rigged" % key,
            )
        # Certificate availability is allowed to differ: it is an observed fact.
        self.assertNotEqual(row_no["certificate_available"], row_yes["certificate_available"])


class FeedbackCostAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skip_reason = None
        if not REPLAY_ROWS.exists():
            cls.skip_reason = "cached feedback-level replay rows missing"
            return
        replay = fca.load_jsonl(REPLAY_ROWS)
        summary = fca.load_jsonl(SUMMARY_ROWS) if SUMMARY_ROWS.exists() else []
        cls.rows = fca.build_cost_rows(replay, fca.index_summary(summary))
        cls.by_key = {
            (str(r["dataset"]), str(r["feedback_level"]), str(r["system_raw"])): r
            for r in cls.rows
        }

    def setUp(self) -> None:
        if self.skip_reason:
            self.skipTest(self.skip_reason)

    def test_runs_on_cached_data(self) -> None:
        self.assertTrue(self.rows, "analysis produced no rows from cached data")
        # Expect 2 datasets x 3 levels x 3 systems = 18 groups.
        self.assertEqual(len(self.rows), 18)

    def test_required_columns_present(self) -> None:
        required = {
            "system",
            "harness_success",
            "excess_cost",
            "over_harness_rate",
            "llm_calls",
            "verifier_repair_rounds",
            "oracle_status_accesses",
            "leakage_label",
            "certificate",
        }
        for row in self.rows:
            self.assertTrue(required.issubset(row.keys()))

    def test_certificate_is_observed_not_assumed(self) -> None:
        # GapHarness rows carry a certificate at medium/strong; baselines never do.
        for row in self.rows:
            if str(row["system_raw"]).startswith("GapHarness") and row["feedback_level"] != "weak_pass_fail":
                self.assertEqual(row["certificate"], "yes")
            if str(row["system_raw"]) in {"ReAct replay", "Router-Repair replay"}:
                self.assertEqual(row["certificate"], "no")

    def test_medium_is_headline_and_non_leaky(self) -> None:
        headline = [r for r in self.rows if r["is_headline"]]
        self.assertTrue(headline)
        for row in headline:
            self.assertEqual(row["feedback_level"], "medium_obligation")
            self.assertIn("non-leaky", row["leakage_label"])
            # Headline (medium) must NOT consume oracle-status accesses.
            self.assertEqual(row["oracle_status_accesses"], 0.0)

    def test_medium_coverage_parity_not_manufactured(self) -> None:
        # At medium feedback the baselines must NOT be worse than GapHarness by
        # more than a small margin -> we are not manufacturing a coverage win.
        for dataset in ("GapBench test800", "HarnessChallenge-200"):
            gh = self.by_key[(dataset, "medium_obligation", "GapHarness-Repair replay")]
            react = self.by_key[(dataset, "medium_obligation", "ReAct replay")]
            self.assertGreaterEqual(
                float(react["harness_success"]) + 1e-9,
                float(gh["harness_success"]) - 0.05,
                "medium-feedback coverage gap is too large to call parity",
            )

    def test_oracle_leakage_only_at_strong(self) -> None:
        for row in self.rows:
            if row["feedback_level"] == "strong_capability_status":
                # Strong leaks gold status: repaired rows cost an oracle access.
                self.assertGreater(float(row["oracle_status_accesses"]), 0.0)
            else:
                self.assertEqual(float(row["oracle_status_accesses"]), 0.0)

    def test_weak_baselines_pay_excess_cost(self) -> None:
        # Weak feedback: baselines reach ~1.0 only by bulk-adding -> high excess.
        for dataset in ("GapBench test800", "HarnessChallenge-200"):
            react = self.by_key[(dataset, "weak_pass_fail", "ReAct replay")]
            self.assertGreaterEqual(float(react["harness_success"]), 0.99)
            self.assertGreater(float(react["excess_cost"]), 1.0)


if __name__ == "__main__":
    unittest.main()
