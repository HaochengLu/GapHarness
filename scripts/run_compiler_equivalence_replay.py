"""Replay frozen experiment rows through the optimized compiler.

The replay does not call APIs and does not overwrite frozen result files. It
checks whether the dominance-pruned branch-and-bound compiler is extensionally
equivalent to the previous exact compiler on saved tasks, profiles, and routes.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence, Tuple

from gapharness.baselines import SYSTEMS, compile_for_system
from gapharness.compiler import compile_minimal_harness
from gapharness.dominance_registry import (
    dominance_registry,
    dominated_pairs,
    replay_profiles,
)
from gapharness.registry import (
    default_registry,
    provided_capabilities,
    provided_obligations,
    total_cost,
)
from gapharness.schema import (
    CompiledHarness,
    ModuleSpec,
    ProfilerOutput,
    TaskExample,
    frozen,
)
from scripts.run_phase4_reviewer_hardening import harness_from_route


# Systems whose harness is genuinely produced by ``compile_minimal_harness``.
# Everything else is a baseline policy or a router that never touches the
# compiler, so replaying it does not test compiler equivalence.
COMPILER_BACKED_SYSTEMS = frozenset({"gapharness"})

# Map of frozen ``system`` labels onto the canonical baseline system used when a
# row stores neither a ``profile`` nor a ``route``. Labels that resolve to
# ``gapharness`` are compiler-backed; the rest are baseline reconstructions.
SYSTEM_LABEL_MAP = {
    "gold_oracle_gap_harness": "gapharness",
    "gapharness_gold": "gapharness",
    "selected_llm_gap_harness": "gapharness",
    "phase2c_registry_guarded_gap_harness": "gapharness",
    "registry_guarded_gapharness": "gapharness",
}

# Replay-kind labels reported in the honest breakdown.
KIND_GENUINE = "compiler_reinvoked"
KIND_RECONSTRUCTED = "reconstructed_baseline"
KIND_ROUTER = "router_skipped"


DEFAULT_REPLAYS = (
    ("gapbench1000_gold", "outputs/final/results_gapbench1000_all_gold.jsonl"),
    ("test800_llm", "outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl"),
    ("test800_registry_guarded", "outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl"),
    ("harness_challenge_gold", "outputs/final/results_harness_challenge200_author_reviewed_gold.jsonl"),
    ("harness_challenge_llm", "outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl"),
    ("harness_challenge_guarded", "outputs/final/harness_challenge200_registry_guarded/results_dev200_llm_registry_guarded.jsonl"),
    ("harness_challenge_router", "outputs/phase4/llm_tool_router_harness_challenge200/results_llm_tool_router.jsonl"),
    ("harness_exec20", "outputs/final/harness_exec20/traces.jsonl"),
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs/final/compiler_equivalence")
    parser.add_argument("--result", action="append", help="Optional label:path replay input. May be repeated.")
    args = parser.parse_args(argv)

    specs = tuple(parse_spec(item) for item in args.result) if args.result else DEFAULT_REPLAYS
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for label, path in specs:
        source = Path(path)
        if not source.exists():
            rows.append(missing_row(label, source))
            continue
        rows.extend(replay_file(label, source))

    dominance = run_dominance_track()

    write_jsonl(out_dir / "replay_rows.jsonl", rows)
    write_jsonl(out_dir / "dominance_track_rows.jsonl", dominance["rows"])
    (out_dir / "replay_report.md").write_text(render_report(rows, dominance), encoding="utf-8")

    print_breakdown(rows, dominance)
    print("wrote compiler equivalence replay to %s" % out_dir)

    if dominance["mismatches"]:
        raise SystemExit("dominance track mismatch vs brute force: %d row(s)" % dominance["mismatches"])
    if dominance["max_dominated"] <= 0:
        raise SystemExit("dominance track did not prune any module (expected dominated > 0)")
    if dominance["max_nodes"] <= 0:
        raise SystemExit("dominance track did not visit any search node (expected nodes > 0)")
    return 0


def parse_spec(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise SystemExit("--result must be label:path")
    label, path = value.split(":", 1)
    return label, path


def replay_file(label: str, path: Path) -> list[dict[str, object]]:
    out = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out.append(replay_row(label, path, row))
    return out


def replay_row(label: str, path: Path, row: Mapping[str, object]) -> dict[str, object]:
    task = TaskExample.from_json(row["task"])
    old = row["harness"]
    new, kind, detail = compile_new_harness(row, task)
    new_json = new.to_json()
    # Only rows where the compiler was genuinely re-run count toward the
    # "compiler equivalence" claim. Reconstructed baselines and router rows are
    # labelled and excluded so the reported equivalence N is honest.
    genuine = kind == KIND_GENUINE
    return {
        "experiment": label,
        "source_path": str(path),
        "task_id": row.get("task_id", task.task_id),
        "system": row.get("system", ""),
        "replay_kind": kind,
        "replay_kind_detail": detail,
        "compiler_reinvoked": genuine,
        "old_status": old.get("status"),
        "new_status": new.status,
        "old_modules": old.get("modules", []),
        "new_modules": list(new.modules),
        "old_cost": old.get("cost"),
        "new_cost": new.cost,
        # Equivalence/change flags are only meaningful for genuinely recompiled
        # rows; non-genuine rows never exercise the compiler so they are excluded
        # from the equivalence count and reported as not-applicable for change.
        "status_changed": genuine and old.get("status") != new.status,
        "modules_changed": genuine and list(old.get("modules", [])) != list(new.modules),
        "cost_changed": genuine and old.get("cost") != new.cost,
        "certificate_algorithm": new_json.get("certificate", {}).get("compiler_algorithm", ""),
        "certificate_nodes_visited": new_json.get("certificate", {}).get("search_stats", {}).get("nodes_visited", 0),
        "certificate_dominated_count": new_json.get("certificate", {}).get("dominated_module_count", 0),
    }


def compile_new_harness(
    row: Mapping[str, object], task: TaskExample
) -> Tuple[CompiledHarness, str, str]:
    """Recompile a frozen row and classify whether the compiler was re-invoked.

    Returns ``(harness, kind, detail)`` where ``kind`` is one of
    :data:`KIND_GENUINE`, :data:`KIND_RECONSTRUCTED`, or :data:`KIND_ROUTER`.

    A row genuinely exercises the compiler only when it stores a profiler
    ``profile`` (recompiled directly) or its ``system`` resolves to the
    compiler-backed ``gapharness`` policy. Rows that store a router ``route`` or
    resolve to a non-compiler baseline (direct/tool_router/always_full/
    oracle_minimal) are reconstructed without ever calling
    ``compile_minimal_harness`` and are labelled accordingly.
    """

    registry = default_registry()
    if "profile" in row:
        harness = compile_minimal_harness(profile_from_json(row["profile"]), registry)
        return harness, KIND_GENUINE, "stored_profile"
    if "route" in row:
        return harness_from_route(row["route"]), KIND_ROUTER, "router_route"

    system = str(row.get("system", ""))
    mapped = map_system_label(system)
    resolved = mapped if mapped in SYSTEMS else (system if system in SYSTEMS else "")
    if not resolved:
        raise ValueError(
            "Cannot replay row without profile/route for system %s task %s" % (system, task.task_id)
        )

    harness, _profiler = compile_for_system(task, resolved, "gold", registry)
    if resolved in COMPILER_BACKED_SYSTEMS:
        # gapharness recompiles via compile_minimal_harness, but the stored row
        # carries no profile, so we re-profile from gold. This is a genuine
        # compiler invocation, distinct from the no-profile baseline policies.
        return harness, KIND_GENUINE, "reprofiled_gold:%s" % resolved
    return harness, KIND_RECONSTRUCTED, "baseline:%s" % resolved


def map_system_label(system: str) -> str:
    return SYSTEM_LABEL_MAP.get(system, system)


def profile_from_json(row: Mapping[str, object]) -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=bool(row.get("direct_llm_sufficient", False)),
        obligations=frozen(row.get("obligations", [])),
        required_capabilities=frozen(row.get("required_capabilities", [])),
        output_contract=dict(row.get("output_contract", {})),
        forbidden_paths=tuple(row.get("forbidden_paths", [])),
        risk_level=str(row.get("risk_level", "low")),
        unsupported_possibility=tuple(row.get("unsupported_possibility", [])),
        rationale=str(row.get("rationale", "")),
    )


def missing_row(label: str, path: Path) -> dict[str, object]:
    return {
        "experiment": label,
        "source_path": str(path),
        "missing_file": True,
        "replay_kind": "missing_file",
        "compiler_reinvoked": False,
        "status_changed": False,
        "modules_changed": False,
        "cost_changed": False,
    }


# --------------------------------------------------------------------------- #
# Dominance-bearing replay track
# --------------------------------------------------------------------------- #
def run_dominance_track() -> Mapping[str, object]:
    """Replay engineered profiles through the dominance-bearing registry.

    For each profile, the optimized dominance-pruned branch-and-bound compiler is
    compared against an *independent* inline brute-force reference over the SAME
    registry. The track asserts identical status/modules/cost and reports the
    dominated-module count and the number of search nodes visited so the
    "dominance-pruned branch-and-bound" claim is non-vacuous.
    """

    registry = dominance_registry()
    rows: List[dict[str, object]] = []
    mismatches = 0
    max_dominated = 0
    max_nodes = 0
    for name, profile in replay_profiles():
        optimized = compile_minimal_harness(profile, registry, strategy="optimized")
        reference = _bruteforce_reference(profile, registry)
        cert = optimized.to_json().get("certificate", {})
        nodes = int(cert.get("search_stats", {}).get("nodes_visited", 0))
        dominated = int(cert.get("dominated_module_count", 0))
        opt_modules = tuple(sorted(optimized.modules))
        status_match = optimized.status == reference["status"]
        modules_match = opt_modules == reference["modules"]
        cost_match = optimized.cost == reference["cost"]
        mismatch = not (status_match and modules_match and cost_match)
        if mismatch:
            mismatches += 1
        max_dominated = max(max_dominated, dominated)
        max_nodes = max(max_nodes, nodes)
        rows.append(
            {
                "profile": name,
                "optimized_status": optimized.status,
                "reference_status": reference["status"],
                "optimized_modules": list(opt_modules),
                "reference_modules": list(reference["modules"]),
                "optimized_cost": optimized.cost,
                "reference_cost": reference["cost"],
                "status_match": status_match,
                "modules_match": modules_match,
                "cost_match": cost_match,
                "mismatch": mismatch,
                "dominated_module_count": dominated,
                "nodes_visited": nodes,
                "candidates_evaluated": reference["candidates_evaluated"],
            }
        )
    return {
        "rows": rows,
        "mismatches": mismatches,
        "max_dominated": max_dominated,
        "max_nodes": max_nodes,
        "total_dominated": sum(r["dominated_module_count"] for r in rows),
        "total_nodes": sum(r["nodes_visited"] for r in rows),
        "dominated_pairs": [list(pair) for pair in dominated_pairs()],
    }


def _bruteforce_reference(
    profile: ProfilerOutput, registry: Mapping[str, ModuleSpec]
) -> Mapping[str, object]:
    """Independent exact reference: full power-set search, no dominance pruning.

    Implemented inline so the dominance track checks the optimized compiler
    against a search that does NOT share the dominance/branch-and-bound logic.
    """

    if "clarification_needed" in profile.unsupported_possibility:
        return {"status": "clarify", "modules": (), "cost": 0, "candidates_evaluated": 0}

    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)
    if not required_obligations and not required_capabilities:
        return {"status": "supported", "modules": (), "cost": 0, "candidates_evaluated": 0}

    names = [name for name in sorted(registry) if name != "trace_recorder"]
    valid: List[Tuple[str, ...]] = []
    candidates_evaluated = 0
    for size in range(len(names) + 1):
        for combo in combinations(names, size):
            candidates_evaluated += 1
            if _reference_candidate_valid(combo, required_obligations, required_capabilities, registry):
                valid.append(combo)

    if not valid:
        return {
            "status": "unsupported",
            "modules": (),
            "cost": 0,
            "candidates_evaluated": candidates_evaluated,
        }

    best = min(valid, key=lambda ns: (total_cost(ns, registry), len(ns), tuple(sorted(ns))))
    return {
        "status": "supported",
        "modules": tuple(sorted(best)),
        "cost": total_cost(best, registry),
        "candidates_evaluated": candidates_evaluated,
    }


def _reference_candidate_valid(
    module_names: Sequence[str],
    required_obligations: Iterable[str],
    required_capabilities: Iterable[str],
    registry: Mapping[str, ModuleSpec],
) -> bool:
    obligations = set(provided_obligations(module_names, registry))
    capabilities = set(provided_capabilities(module_names, registry))
    if not set(required_obligations).issubset(obligations):
        return False
    if not set(required_capabilities).issubset(capabilities):
        return False
    for name in module_names:
        module = registry[name]
        if not set(module.requires_obligations).issubset(obligations):
            return False
        if not set(module.requires_capabilities).issubset(capabilities):
            return False
    return True


# --------------------------------------------------------------------------- #
# Honest coverage breakdown
# --------------------------------------------------------------------------- #
def coverage_breakdown(rows: Sequence[Mapping[str, object]]) -> Mapping[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get("replay_kind", "unknown"))] += 1
    return dict(counts)


def equivalence_count(rows: Sequence[Mapping[str, object]]) -> int:
    return sum(1 for row in rows if row.get("compiler_reinvoked"))


def print_breakdown(
    rows: Sequence[Mapping[str, object]], dominance: Mapping[str, object]
) -> None:
    total = len(rows)
    genuine = equivalence_count(rows)
    breakdown = coverage_breakdown(rows)
    genuine_rows = [row for row in rows if row.get("compiler_reinvoked")]
    changes = sum(
        1
        for row in genuine_rows
        if row.get("status_changed") or row.get("modules_changed") or row.get("cost_changed")
    )

    print("=" * 72)
    print("Compiler equivalence replay -- honest coverage breakdown")
    print("=" * 72)
    print("Total replay rows scanned:            %d" % total)
    print("Compiler GENUINELY re-invoked (N):    %d  (stored profile or gapharness re-profile)"
          % breakdown.get(KIND_GENUINE, 0))
    print("Reconstructed baselines (excluded):   %d  (direct/tool_router/always_full/oracle_minimal)"
          % breakdown.get(KIND_RECONSTRUCTED, 0))
    print("Router rows (excluded):               %d  (harness_from_route, compiler never called)"
          % breakdown.get(KIND_ROUTER, 0))
    if breakdown.get("missing_file"):
        print("Missing input files (excluded):       %d" % breakdown.get("missing_file", 0))
    print("-" * 72)
    print("Honest compiler-equivalence N:        %d" % genuine)
    print("  of which status/module/cost changed: %d (0 == equivalence preserved)" % changes)
    print("=" * 72)
    print("Dominance track (separate dominance-bearing registry)")
    print("-" * 72)
    print("Profiles replayed vs brute-force ref:  %d" % len(dominance["rows"]))
    print("Mismatches vs brute force:             %d" % dominance["mismatches"])
    print("Max dominated modules removed:         %d" % dominance["max_dominated"])
    print("Total dominated removals (sum):        %d" % dominance["total_dominated"])
    print("Max search nodes visited:              %d" % dominance["max_nodes"])
    print("Total search nodes (sum):              %d" % dominance["total_nodes"])
    print("Declared dominated pairs:              %s" % dominance["dominated_pairs"])
    print("=" * 72)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def render_report(
    rows: Sequence[Mapping[str, object]], dominance: Mapping[str, object]
) -> str:
    buckets: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["experiment"])].append(row)

    genuine_total = equivalence_count(rows)
    breakdown = coverage_breakdown(rows)
    lines = [
        "# Compiler Equivalence Replay",
        "",
        "Replay checks whether the optimized exact compiler preserves frozen harness outputs. "
        "Certificates are new metadata and are ignored for equality.",
        "",
        "Only rows where the compiler is genuinely re-invoked (a stored profiler profile, or a "
        "`gapharness` system re-profiled from gold) count toward compiler equivalence. Reconstructed "
        "baseline rows and router rows never call `compile_minimal_harness` and are labelled and "
        "excluded from the equivalence N.",
        "",
        "## Honest coverage",
        "",
        "| Replay kind | Rows | Counts toward equivalence? |",
        "|---|---:|---|",
        "| %s | %d | yes |" % (KIND_GENUINE, breakdown.get(KIND_GENUINE, 0)),
        "| %s | %d | no (baseline policy) |" % (KIND_RECONSTRUCTED, breakdown.get(KIND_RECONSTRUCTED, 0)),
        "| %s | %d | no (router, compiler skipped) |" % (KIND_ROUTER, breakdown.get(KIND_ROUTER, 0)),
        "| missing_file | %d | no |" % breakdown.get("missing_file", 0),
        "",
        "**Honest compiler-equivalence N = %d** (rows where the compiler was genuinely re-run)." % genuine_total,
        "",
        "## Per-experiment (genuine compiler rows only)",
        "",
        "Columns count only the genuinely re-invoked subset of each experiment; `Genuine N` is that subset.",
        "",
        "| Frozen Experiment | Rows | Genuine N | Status changed | Harness changed | Cost changed | Avg Nodes | Avg Dominated |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in sorted(buckets):
        bucket = buckets[label]
        genuine = [row for row in bucket if row.get("compiler_reinvoked")]
        lines.append(
            "| %s | %d | %d | %d | %d | %d | %.1f | %.1f |"
            % (
                label,
                len(bucket),
                len(genuine),
                sum(1 for row in genuine if row.get("status_changed")),
                sum(1 for row in genuine if row.get("modules_changed")),
                sum(1 for row in genuine if row.get("cost_changed")),
                mean(row.get("certificate_nodes_visited", 0) for row in genuine),
                mean(row.get("certificate_dominated_count", 0) for row in genuine),
            )
        )

    lines.extend(_render_dominance_section(dominance))

    failures = [
        row
        for row in rows
        if row.get("compiler_reinvoked")
        and (row.get("status_changed") or row.get("modules_changed") or row.get("cost_changed"))
    ]
    lines.extend(["", "## Changed Rows (genuine compiler rows only)", ""])
    if not failures:
        lines.append("No status, module, or cost changes were observed among genuinely recompiled rows.")
    else:
        lines.extend(["| Experiment | Task | System | Old | New |", "|---|---|---|---|---|"])
        for row in failures[:50]:
            lines.append(
                "| %s | %s | %s | %s/%s/%s | %s/%s/%s |"
                % (
                    row.get("experiment"),
                    row.get("task_id"),
                    row.get("system"),
                    row.get("old_status"),
                    ",".join(row.get("old_modules", [])),
                    row.get("old_cost"),
                    row.get("new_status"),
                    ",".join(row.get("new_modules", [])),
                    row.get("new_cost"),
                )
            )
    lines.append("")
    return "\n".join(lines)


def _render_dominance_section(dominance: Mapping[str, object]) -> List[str]:
    lines = [
        "",
        "## Dominance Track (dominance-bearing registry)",
        "",
        "A separate registry (`gapharness.dominance_registry`) in which several modules are strictly "
        "dominated, so dominance pruning fires. Each profile is checked against an independent inline "
        "brute-force reference over the same registry.",
        "",
        "Declared dominated pairs (dominated <- dominator): %s"
        % ", ".join("%s<-%s" % (pair[0], pair[1]) for pair in dominance["dominated_pairs"]),
        "",
        "| Profile | Opt status/modules/cost | Ref status/modules/cost | Match | Dominated | Nodes |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in dominance["rows"]:
        lines.append(
            "| %s | %s/%s/%s | %s/%s/%s | %s | %d | %d |"
            % (
                row["profile"],
                row["optimized_status"],
                ",".join(row["optimized_modules"]),
                row["optimized_cost"],
                row["reference_status"],
                ",".join(row["reference_modules"]),
                row["reference_cost"],
                "ok" if not row["mismatch"] else "MISMATCH",
                row["dominated_module_count"],
                row["nodes_visited"],
            )
        )
    lines.extend(
        [
            "",
            "Mismatches vs brute force: **%d**. Max dominated removed: **%d**. Max search nodes: **%d**."
            % (dominance["mismatches"], dominance["max_dominated"], dominance["max_nodes"]),
        ]
    )
    return lines


def mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / len(values_list)


if __name__ == "__main__":
    raise SystemExit(main())
