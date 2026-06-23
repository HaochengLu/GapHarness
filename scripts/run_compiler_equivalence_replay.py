"""Replay frozen experiment rows through the optimized compiler.

The replay does not call APIs and does not overwrite frozen result files. It
checks whether the dominance-pruned branch-and-bound compiler is extensionally
equivalent to the previous exact compiler on saved tasks, profiles, and routes.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.baselines import SYSTEMS, compile_for_system
from gapharness.compiler import compile_minimal_harness
from gapharness.registry import default_registry
from gapharness.schema import CompiledHarness, ProfilerOutput, TaskExample, frozen
from scripts.run_phase4_reviewer_hardening import harness_from_route


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

    write_jsonl(out_dir / "replay_rows.jsonl", rows)
    (out_dir / "replay_report.md").write_text(render_report(rows), encoding="utf-8")
    print("wrote compiler equivalence replay to %s" % out_dir)
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
    new = compile_new_harness(row, task)
    new_json = new.to_json()
    return {
        "experiment": label,
        "source_path": str(path),
        "task_id": row.get("task_id", task.task_id),
        "system": row.get("system", ""),
        "old_status": old.get("status"),
        "new_status": new.status,
        "old_modules": old.get("modules", []),
        "new_modules": list(new.modules),
        "old_cost": old.get("cost"),
        "new_cost": new.cost,
        "status_changed": old.get("status") != new.status,
        "modules_changed": list(old.get("modules", [])) != list(new.modules),
        "cost_changed": old.get("cost") != new.cost,
        "certificate_algorithm": new_json.get("certificate", {}).get("compiler_algorithm", ""),
        "certificate_nodes_visited": new_json.get("certificate", {}).get("search_stats", {}).get("nodes_visited", 0),
        "certificate_dominated_count": new_json.get("certificate", {}).get("dominated_module_count", 0),
    }


def compile_new_harness(row: Mapping[str, object], task: TaskExample) -> CompiledHarness:
    registry = default_registry()
    if "profile" in row:
        return compile_minimal_harness(profile_from_json(row["profile"]), registry)
    if "route" in row:
        return harness_from_route(row["route"])

    system = str(row.get("system", ""))
    mapped = map_system_label(system)
    if mapped in SYSTEMS:
        harness, _profiler = compile_for_system(task, mapped, "gold", registry)
        return harness
    if system in SYSTEMS:
        harness, _profiler = compile_for_system(task, system, "gold", registry)
        return harness
    raise ValueError("Cannot replay row without profile/route for system %s task %s" % (system, task.task_id))


def map_system_label(system: str) -> str:
    mapping = {
        "gold_oracle_gap_harness": "gapharness",
        "gapharness_gold": "gapharness",
        "selected_llm_gap_harness": "gapharness",
        "phase2c_registry_guarded_gap_harness": "gapharness",
        "registry_guarded_gapharness": "gapharness",
    }
    return mapping.get(system, system)


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
        "status_changed": True,
        "modules_changed": True,
        "cost_changed": True,
    }


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def render_report(rows: Sequence[Mapping[str, object]]) -> str:
    buckets: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["experiment"])].append(row)

    lines = [
        "# Compiler Equivalence Replay",
        "",
        "Replay checks whether the optimized exact compiler preserves frozen harness outputs. Certificates are new metadata and are ignored for equality.",
        "",
        "| Frozen Experiment | N | Status changed | Harness changed | Cost changed | Avg Nodes | Avg Dominated |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label in sorted(buckets):
        bucket = buckets[label]
        n = len(bucket)
        lines.append(
            "| %s | %d | %d | %d | %d | %.1f | %.1f |"
            % (
                label,
                n,
                sum(1 for row in bucket if row.get("status_changed")),
                sum(1 for row in bucket if row.get("modules_changed")),
                sum(1 for row in bucket if row.get("cost_changed")),
                mean(row.get("certificate_nodes_visited", 0) for row in bucket),
                mean(row.get("certificate_dominated_count", 0) for row in bucket),
            )
        )

    failures = [row for row in rows if row.get("status_changed") or row.get("modules_changed") or row.get("cost_changed")]
    lines.extend(["", "## Changed Rows", ""])
    if not failures:
        lines.append("No status, module, or cost changes were observed.")
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


def mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / len(values_list)


if __name__ == "__main__":
    raise SystemExit(main())
