"""Reproducibility-hardening regression tests.

These tests lock in the fixes made by the reproducibility-engineer pass:

* the Phase-2 gold experiment script only references benchmark inputs that
  actually exist on disk (and no longer points at the missing
  ``gapbench_natural_200_for_review.jsonl``);
* ``freeze_phase2_datasets`` round-trips non-ASCII characters (e.g. U+2019)
  losslessly, so a freeze re-run preserves committed UTF-8 bytes/checksums;
* ``pyproject.toml`` declares a build-system and the correct package
  name / console-script entry point;
* the declared Python version is internally consistent and true (>=3.9).
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


class GoldScriptPathsTest(unittest.TestCase):
    GOLD_SCRIPT = "scripts/run_phase2_gold_experiments.sh"

    def test_all_referenced_benchmark_inputs_exist(self):
        text = _read(self.GOLD_SCRIPT)
        referenced = sorted(set(re.findall(r"benchmarks/[^\s]+\.jsonl", text)))
        self.assertTrue(referenced, "expected the gold script to reference benchmark inputs")
        for rel in referenced:
            self.assertTrue(
                (REPO_ROOT / rel).exists(),
                f"gold script references missing benchmark input: {rel}",
            )

    def test_stale_for_review_path_is_gone(self):
        text = _read(self.GOLD_SCRIPT)
        self.assertNotIn(
            "gapbench_natural_200_for_review.jsonl",
            text,
            "gold script still references the non-existent for_review file",
        )
        self.assertIn(
            "gapbench_natural_200_human_audited.jsonl",
            text,
            "gold script should reference the committed human-audited natural file",
        )


class FreezeUtf8Test(unittest.TestCase):
    def test_write_jsonl_preserves_non_ascii_bytes(self):
        from scripts.freeze_phase2_datasets import load_jsonl, write_jsonl

        # U+2019 RIGHT SINGLE QUOTATION MARK is the character that previously
        # got escaped to ’ and broke GAIA checksums.
        row = {"task_id": "t1", "query": "what’s the answer", "z": "last"}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "rows.jsonl"
            write_jsonl(out, [row])
            raw = out.read_bytes()
            # Raw UTF-8 bytes of U+2019 present; no \uXXXX escape sequence.
            self.assertIn("’".encode("utf-8"), raw)
            self.assertNotIn(b"\\u2019", raw)
            # And it still round-trips back to the identical object.
            self.assertEqual(load_jsonl(out), [row])

    def test_write_json_preserves_non_ascii_bytes(self):
        from scripts.freeze_phase2_datasets import write_json

        payload = {"note": "owner’s audit", "version": "v1.0"}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            write_json(out, payload)
            raw = out.read_bytes()
            self.assertIn("’".encode("utf-8"), raw)
            self.assertNotIn(b"\\u2019", raw)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), payload)


class PyprojectTest(unittest.TestCase):
    def setUp(self):
        self.text = _read("pyproject.toml")

    def test_build_system_present(self):
        self.assertIn("[build-system]", self.text)
        self.assertIn("setuptools", self.text)
        self.assertIn("build-backend = \"setuptools.build_meta\"", self.text)

    def test_project_name_and_entry_point(self):
        self.assertIn('name = "gapharness"', self.text)
        self.assertIn('gapharness = "gapharness.cli:main"', self.text)

    def test_entry_point_target_is_importable_and_callable(self):
        from gapharness.cli import main

        self.assertTrue(callable(main))

    def test_requires_python_is_truthful(self):
        # The codebase runs on the pinned 3.9 interpreter, so the floor must be
        # 3.9 and must be satisfied by whatever interpreter runs this test.
        self.assertIn('requires-python = ">=3.9"', self.text)
        self.assertGreaterEqual(sys.version_info[:2], (3, 9))


class PythonVersionPinTest(unittest.TestCase):
    def test_python_version_file_pins_39(self):
        pin = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
        self.assertTrue(pin.startswith("3.9"), f"unexpected .python-version pin: {pin!r}")

    def test_reproducibility_doc_is_consistent(self):
        doc = _read("paper/appendix/reproducibility.md")
        self.assertIn("Python 3.9", doc)
        # The doc may mention the historical for_review name when explaining the
        # fix, but it must not present it as a live benchmark *path* (i.e. a
        # benchmarks/.../gapbench_natural_200_for_review.jsonl reference).
        self.assertNotRegex(
            doc,
            r"benchmarks/[^\s`]*gapbench_natural_200_for_review\.jsonl",
            "doc still references the stale natural for_review benchmark path",
        )
        # And it must document the committed human-audited natural input path.
        self.assertIn(
            "benchmarks/gapbench_natural/v1.0/gapbench_natural_200_human_audited.jsonl",
            doc,
        )


if __name__ == "__main__":
    unittest.main()
