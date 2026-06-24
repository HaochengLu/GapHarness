from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
TABLES = REPO_ROOT / "paper" / "tables"
TABLE20 = TABLES / "table20_cost_calibration_sensitivity.md"
TABLE5_STALE = TABLES / "table5_transfer_boundary.md"
TABLE5_REVISED = TABLES / "table5_boundary_diagnostics_revised.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ReadmeOverclaimTests(unittest.TestCase):
    """README must not carry gold-truth / bare human-audited overclaims."""

    def setUp(self) -> None:
        self.text = _read(README)

    def test_no_gold_truth_claim(self) -> None:
        self.assertNotIn("gold truth", self.text)

    def test_no_bare_human_audited(self) -> None:
        # Bare prose "human-audited"/"human audited" overclaim must be gone.
        # (Literal *_human_audited.jsonl artifact filenames are not present in README.)
        self.assertNotRegex(self.text, r"human[ -]audited")

    def test_uses_single_annotator_wording(self) -> None:
        self.assertIn("single-annotator (project-owner) labels", self.text)
        self.assertIn(
            "inter-annotator agreement is reported on an independent subset", self.text
        )


class ReadmeFramingTests(unittest.TestCase):
    """README title/abstract/claim must reflect the v2 framing."""

    def setUp(self) -> None:
        self.text = _read(README)

    def test_v2_framing_present(self) -> None:
        self.assertIn("Certificate-Carrying Runtime Harness Compilation", self.text)

    def test_pre_pivot_title_dropped(self) -> None:
        # The pre-pivot tagline must not headline the README anymore.
        self.assertNotIn(
            "minimal research implementation of **Obligation-First Minimal Harness Synthesis**",
            self.text,
        )

    def test_research_claim_is_bounded(self) -> None:
        self.assertIn("bounded systems claim", self.text)


class TerminologyTests(unittest.TestCase):
    """Terminology drift must be standardized in README."""

    def setUp(self) -> None:
        self.text = _read(README)

    def test_no_terminalsmoke20(self) -> None:
        self.assertNotIn("TerminalSmoke-20", self.text)

    def test_terminal_bench_obligation50_used(self) -> None:
        self.assertIn("Terminal-Bench-obligation50", self.text)

    def test_no_minimality_regret(self) -> None:
        self.assertNotIn("minimality regret", self.text)


class Table20OverHarnessTests(unittest.TestCase):
    """Declared-scheme GapHarness profiler over-harness must be 0.14 / 0.15."""

    def setUp(self) -> None:
        self.lines = _read(TABLE20).splitlines()

    def _over_value(self, scheme: str, system: str) -> str:
        prefix = f"| {scheme} | {system} |"
        for line in self.lines:
            if line.startswith(prefix):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                return cells[-1]  # Over is the last column
        self.fail(f"row not found: {scheme} / {system}")

    def test_declared_gapharness_llm_over_is_014(self) -> None:
        self.assertEqual(self._over_value("declared", "GapHarness LLM"), "0.14")

    def test_declared_registry_guarded_over_is_015(self) -> None:
        self.assertEqual(self._over_value("declared", "Registry-guarded GH"), "0.15")

    def test_declared_rows_not_016_or_017(self) -> None:
        # Guard against regression to the stale 0.16 / 0.17 raw rounding.
        self.assertNotEqual(self._over_value("declared", "GapHarness LLM"), "0.16")
        self.assertNotEqual(self._over_value("declared", "Registry-guarded GH"), "0.17")

    def test_other_scheme_rows_left_unchanged(self) -> None:
        # Per scope: only declared-scheme profiler rows were corrected.
        self.assertEqual(self._over_value("uniform", "GapHarness LLM"), "0.16")
        self.assertEqual(self._over_value("uniform", "Registry-guarded GH"), "0.17")

    def test_repair_baseline_row_left_unchanged(self) -> None:
        self.assertEqual(self._over_value("declared", "GapHarness-Repair"), "0.15")


class Table5SupersessionTests(unittest.TestCase):
    """Stale table5 must be annotated as superseded; data preserved."""

    def test_both_files_exist(self) -> None:
        self.assertTrue(TABLE5_STALE.exists())
        self.assertTrue(TABLE5_REVISED.exists())

    def test_stale_has_superseded_note(self) -> None:
        text = _read(TABLE5_STALE)
        self.assertIn("SUPERSEDED by table5_boundary_diagnostics_revised.md", text)

    def test_stale_data_preserved(self) -> None:
        # Annotation must not delete the underlying rows.
        text = _read(TABLE5_STALE)
        self.assertIn("GAIA registry-guarded", text)
        self.assertRegex(text, r"\|\s*200\s*\|")


if __name__ == "__main__":
    unittest.main()
