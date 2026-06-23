"""Render checkable compiler certificate samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.compiler import compile_minimal_harness
from gapharness.evaluation import load_benchmark
from gapharness.profiler import profile_from_gold
from gapharness.registry import default_registry
from gapharness.schema import TaskExample


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="outputs/final/compiler_certificates")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = build_samples()
    write_jsonl(out_dir / "certificate_samples.jsonl", rows)
    (out_dir / "certificate_samples_report.md").write_text(render_report(rows), encoding="utf-8")
    print("wrote certificate samples to %s" % out_dir)
    return 0


def build_samples() -> list[dict[str, object]]:
    gapbench = load_benchmark("benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl")
    challenge = load_benchmark("benchmarks/harness_challenge/v1.0/harness_challenge200_author_reviewed.jsonl")
    rows: list[dict[str, object]] = []
    rows.extend(compile_samples("gapbench_supported", [t for t in gapbench if t.expected_status == "supported" and t.oracle_minimal_harness][:5]))
    rows.extend(compile_samples("gapbench_direct", [t for t in gapbench if t.expected_status == "supported" and not t.oracle_minimal_harness][:5]))
    rows.extend(compile_samples("challenge_unsupported", [t for t in challenge if t.expected_status == "unsupported"][:5]))
    rows.extend(compile_perturbation_samples([t for t in challenge if "python_executor" in t.oracle_minimal_harness][:5], "python_executor"))
    return rows[:20]


def compile_samples(label: str, tasks: Sequence[TaskExample]) -> list[dict[str, object]]:
    registry = default_registry()
    rows = []
    for task in tasks:
        profile = profile_from_gold(task)
        harness = compile_minimal_harness(profile, registry)
        rows.append(sample_row(label, task, harness.to_json()))
    return rows


def compile_perturbation_samples(
    tasks: Sequence[TaskExample],
    removed_module: str,
) -> list[dict[str, object]]:
    registry = {name: spec for name, spec in default_registry().items() if name != removed_module}
    rows = []
    for task in tasks:
        profile = profile_from_gold(task)
        harness = compile_minimal_harness(profile, registry)
        row = sample_row("perturb_remove_%s" % removed_module, task, harness.to_json())
        row["removed_module"] = removed_module
        rows.append(row)
    return rows


def sample_row(label: str, task: TaskExample, harness: Mapping[str, object]) -> dict[str, object]:
    return {
        "sample_type": label,
        "task_id": task.task_id,
        "expected_status": task.expected_status,
        "category": task.category,
        "query": task.query,
        "gold_obligations": sorted(task.gold_obligations),
        "required_capabilities": sorted(task.required_capabilities),
        "harness": harness,
        "certificate": harness.get("certificate", {}),
    }


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def render_report(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# Compiler Certificate Samples",
        "",
        "These samples show checkable compiler certificates across supported, direct, unsupported, and perturbed-registry cases.",
        "",
        "| Type | Task | Status | Cost | Modules | Missing Capabilities | Algorithm | Nodes |",
        "|---|---|---|---:|---|---|---|---:|",
    ]
    for row in rows:
        harness = row["harness"]
        cert = row["certificate"]
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s | %s |"
            % (
                row["sample_type"],
                row["task_id"],
                harness.get("status"),
                harness.get("cost"),
                ",".join(harness.get("modules", [])) or "-",
                ",".join(harness.get("missing_capabilities", [])) or "-",
                cert.get("compiler_algorithm", ""),
                cert.get("search_stats", {}).get("nodes_visited", 0),
            )
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
