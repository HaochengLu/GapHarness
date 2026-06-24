"""Cross-check the exact compiler against an INDEPENDENT minimum-cost solver.

Motivation (B1)
---------------
The gold ``oracle_minimal_harness`` labels in the benchmarks were produced by
``compile_minimal_harness`` (``seed_data.py`` calls it at build time), so
"compiler == gold oracle" is tautological. This script instead runs BOTH the
compiler under test AND an independently implemented solver
(``gapharness.independent_oracle``) on the SAME reconstructed gold profile for
every supported benchmark row, and reports a real agreement number:

  * total supported rows checked,
  * # cost-equal,
  * # module-set-equal,
  * any mismatches (printed with task_id and both harnesses).

A high cost-agreement number from two algorithmically distinct exact solvers is
a genuine cross-validation of the compiler implementation, not a restatement of
Proposition 1.

Usage
-----
    python3 scripts/verify_independent_oracle.py            # default splits
    python3 scripts/verify_independent_oracle.py FILE...    # custom jsonl files

Exit code is 0 when there are no cost mismatches, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from gapharness.compiler import compile_minimal_harness
from gapharness.independent_oracle import independent_oracle
from gapharness.registry import default_registry
from gapharness.schema import ProfilerOutput, frozen

REPO_ROOT = Path(__file__).resolve().parent.parent

# Default benchmark splits to cross-check. Only files that exist are used.
DEFAULT_FILES: Tuple[str, ...] = (
    "benchmarks/gapbench/v1.0/splits/dev200.jsonl",
    "benchmarks/gapbench/v1.0/splits/test800.jsonl",
    "benchmarks/gaia_transfer/v1.0/gaia_transfer200_human_audited.jsonl",
    "benchmarks/gaia_transfer/v1.0/gaia_validation100_human_audited.jsonl",
    "benchmarks/gaia_transfer/v1.0/gaia_test100_human_audited.jsonl",
    "benchmarks/swe_obligation/v1.0/swe_obligation50_human_audited.jsonl",
)


def gold_profile_from_row(row: Mapping[str, object]) -> ProfilerOutput:
    """Reconstruct the gold ProfilerOutput a row implies.

    Mirrors ``seed_data._make_task``: a supported row's profile is just its gold
    obligations + required capabilities. Clarify rows carry the
    ``clarification_needed`` marker; unsupported rows keep their gold
    obligations/capabilities (which by construction cannot be covered).
    """
    obligations = frozen(row.get("gold_obligations", []))
    capabilities = frozen(row.get("required_capabilities", []))
    expected_status = str(row.get("expected_status", "supported"))
    unsupported_possibility: Tuple[str, ...] = ()
    if expected_status == "clarify":
        unsupported_possibility = ("clarification_needed",)
    return ProfilerOutput(
        direct_llm_sufficient=not obligations and not capabilities,
        obligations=obligations,
        required_capabilities=capabilities,
        risk_level=str(row.get("risk_level", "low")),
        unsupported_possibility=unsupported_possibility,
    )


def iter_rows(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def check_file(path: Path, registry: Mapping[str, object]) -> Dict[str, object]:
    total = 0
    supported_checked = 0
    cost_equal = 0
    module_equal = 0
    mismatches: List[Dict[str, object]] = []

    for row in iter_rows(path):
        total += 1
        # We compare only on rows the gold says are supported, because the
        # cross-check is about the optimisation result (min-cost cover). For
        # clarify/unsupported rows both methods short-circuit identically, but
        # they carry no optimum to compare.
        if str(row.get("expected_status", "supported")) != "supported":
            continue

        profile = gold_profile_from_row(row)
        compiled = compile_minimal_harness(profile, registry)
        solved = independent_oracle(profile, registry)

        # Both should agree the row is supported under the gold profile.
        if compiled.status != "supported" or solved.status != "supported":
            mismatches.append(
                {
                    "task_id": row.get("task_id"),
                    "kind": "status",
                    "compiler_status": compiled.status,
                    "independent_status": solved.status,
                    "compiler_modules": list(compiled.modules),
                    "independent_modules": list(solved.modules),
                    "compiler_cost": compiled.cost,
                    "independent_cost": solved.cost,
                }
            )
            supported_checked += 1
            continue

        supported_checked += 1
        if compiled.cost == solved.cost:
            cost_equal += 1
        else:
            mismatches.append(
                {
                    "task_id": row.get("task_id"),
                    "kind": "cost",
                    "compiler_modules": list(compiled.modules),
                    "independent_modules": list(solved.modules),
                    "compiler_cost": compiled.cost,
                    "independent_cost": solved.cost,
                }
            )
        if tuple(sorted(compiled.modules)) == tuple(solved.modules):
            module_equal += 1

    return {
        "path": str(path),
        "total_rows": total,
        "supported_checked": supported_checked,
        "cost_equal": cost_equal,
        "module_set_equal": module_equal,
        "mismatches": mismatches,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files",
        nargs="*",
        help="Benchmark jsonl files to cross-check (default: gapbench/gaia/swe splits).",
    )
    args = parser.parse_args(argv)

    if args.files:
        candidate_paths = [Path(item) for item in args.files]
    else:
        candidate_paths = [REPO_ROOT / item for item in DEFAULT_FILES]

    registry = default_registry()
    reports: List[Dict[str, object]] = []
    missing: List[str] = []
    for path in candidate_paths:
        if not path.exists():
            missing.append(str(path))
            continue
        reports.append(check_file(path, registry))

    grand_total = sum(int(r["total_rows"]) for r in reports)
    grand_supported = sum(int(r["supported_checked"]) for r in reports)
    grand_cost_equal = sum(int(r["cost_equal"]) for r in reports)
    grand_module_equal = sum(int(r["module_set_equal"]) for r in reports)
    grand_mismatches = sum(len(r["mismatches"]) for r in reports)  # type: ignore[arg-type]

    print("Independent oracle cross-check: compile_minimal_harness vs independent_oracle")
    print("=" * 78)
    for r in reports:
        print(
            "{path}\n  rows={total_rows} supported_checked={supported_checked} "
            "cost_equal={cost_equal} module_set_equal={module_set_equal} "
            "mismatches={n_mismatch}".format(
                n_mismatch=len(r["mismatches"]),  # type: ignore[arg-type]
                **r,
            )
        )
        for mm in r["mismatches"]:  # type: ignore[assignment]
            print("    MISMATCH task_id=%s kind=%s" % (mm.get("task_id"), mm.get("kind")))
            print(
                "      compiler:    cost=%s modules=%s"
                % (mm.get("compiler_cost"), mm.get("compiler_modules"))
            )
            print(
                "      independent: cost=%s modules=%s"
                % (mm.get("independent_cost"), mm.get("independent_modules"))
            )

    if missing:
        print("-" * 78)
        print("Skipped %d missing file(s):" % len(missing))
        for path in missing:
            print("  (missing) %s" % path)

    print("=" * 78)
    print("SUMMARY")
    print("  files_checked        = %d" % len(reports))
    print("  total_rows           = %d" % grand_total)
    print("  supported_checked    = %d" % grand_supported)
    cost_pct = (100.0 * grand_cost_equal / grand_supported) if grand_supported else 100.0
    mod_pct = (100.0 * grand_module_equal / grand_supported) if grand_supported else 100.0
    print("  cost_equal           = %d (%.2f%%)" % (grand_cost_equal, cost_pct))
    print("  module_set_equal     = %d (%.2f%%)" % (grand_module_equal, mod_pct))
    print("  mismatches           = %d" % grand_mismatches)
    if grand_mismatches == 0 and grand_supported > 0:
        print(
            "  RESULT: exact compiler == independent optimum on all %d supported rows."
            % grand_supported
        )
    elif grand_supported == 0:
        print("  RESULT: no supported rows checked.")
    else:
        print("  RESULT: cost mismatches detected; see MISMATCH lines above.")

    # Non-zero exit only on real cost mismatches (a genuine compiler defect).
    cost_mismatch = grand_supported - grand_cost_equal
    return 0 if cost_mismatch == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
