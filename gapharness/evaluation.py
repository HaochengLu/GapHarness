"""Benchmark loading, running, and summary metrics."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

from .baselines import SYSTEMS, compile_for_system
from .executor import execute_task
from .registry import default_registry
from .schema import RunResult, TaskExample
from .verifiers import oracle_cost


def load_benchmark(path: str) -> List[TaskExample]:
    tasks = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            tasks.append(TaskExample.from_json(json.loads(line)))
    return tasks


def write_jsonl(path: str, rows: Iterable[Mapping[str, object]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run_benchmark(
    benchmark_path: str,
    system: str,
    profiler: str,
) -> List[Dict[str, object]]:
    registry = default_registry()
    tasks = load_benchmark(benchmark_path)
    systems = list(SYSTEMS) if system == "all" else [system]
    rows: List[Dict[str, object]] = []
    for row in iter_benchmark_rows(tasks, systems, profiler):
        rows.append(row)
    return rows


def iter_benchmark_rows(
    tasks: Sequence[TaskExample],
    systems: Sequence[str],
    profiler: str,
) -> Iterator[Dict[str, object]]:
    registry = default_registry()
    for task in tasks:
        for system_name in systems:
            try:
                harness, actual_profiler = compile_for_system(task, system_name, profiler, registry)
                result = execute_task(task, system_name, actual_profiler, harness, registry)
                row = result.to_json()
                row["task"] = task.to_json()
                row["metrics"] = row_metrics(task, result)
                yield row
            except Exception as exc:
                yield error_row(task, system_name, profiler, exc)


def run_benchmark_streaming(
    benchmark_path: str,
    system: str,
    profiler: str,
    out_path: str,
    limit: Optional[int] = None,
    start: int = 0,
    resume: bool = True,
    progress_every: int = 5,
) -> int:
    tasks = load_benchmark(benchmark_path)
    if start:
        tasks = tasks[start:]
    if limit is not None:
        tasks = tasks[:limit]
    systems = list(SYSTEMS) if system == "all" else [system]
    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    done = _existing_keys(output) if resume else set()
    written = 0
    attempted = 0
    mode = "a" if resume else "w"
    with output.open(mode, encoding="utf-8") as handle:
        for task in tasks:
            for system_name in systems:
                key = _row_key(task.task_id, system_name, profiler)
                if key in done:
                    continue
                attempted += 1
                row = next(iter_benchmark_rows([task], [system_name], profiler))
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                written += 1
                if progress_every and written % progress_every == 0:
                    print(
                        "progress written=%d attempted=%d last=%s/%s"
                        % (written, attempted, task.task_id, system_name),
                        file=sys.stderr,
                    )
    return written


def error_row(task: TaskExample, system_name: str, profiler: str, exc: BaseException) -> Dict[str, object]:
    task_oracle_cost = oracle_cost(task, default_registry())
    cost_delta = -task_oracle_cost
    return {
        "task_id": task.task_id,
        "system": system_name,
        "profiler": profiler,
        "task": task.to_json(),
        "error": "%s: %s" % (exc.__class__.__name__, str(exc)[:1000]),
        "verifier_passed": False,
        "verifier_failures": ("runtime_error",),
        "minimality_report": {},
        "metrics": {
            "success": False,
            "predicted_cost": 0,
            "oracle_cost": task_oracle_cost,
            "cost_delta": cost_delta,
            "excess_cost": max(0.0, cost_delta),
            "minimality_regret": cost_delta,
            "over_harness": False,
            "under_harness": task.expected_status == "supported",
            "wrong_harness": False,
            "extra_modules": [],
            "missing_oracle_modules": list(task.oracle_minimal_harness),
            "redundancy": 0.0,
        },
    }


def row_metrics(task: TaskExample, result: RunResult) -> Dict[str, object]:
    registry = default_registry()
    task_oracle_cost = oracle_cost(task, registry)
    predicted_cost = result.harness.cost
    selected = set(result.harness.modules)
    oracle = set(task.oracle_minimal_harness)
    selected_nonempty = bool(selected)
    supported_task = task.expected_status == "supported"
    under_harness = supported_task and not result.verifier_passed
    wrong_harness = selected_nonempty and supported_task and bool(result.verifier_failures)
    over_harness = supported_task and predicted_cost > task_oracle_cost
    cost_delta = predicted_cost - task_oracle_cost
    minimality = result.minimality_report
    return {
        "success": bool(result.verifier_passed),
        "predicted_cost": predicted_cost,
        "oracle_cost": task_oracle_cost,
        "cost_delta": cost_delta,
        "excess_cost": max(0.0, cost_delta),
        # Backward-compatible alias for frozen Phase 2 scripts. New paper
        # artifacts describe this quantity as cost delta, not true regret.
        "minimality_regret": cost_delta,
        "over_harness": bool(over_harness),
        "under_harness": bool(under_harness),
        "wrong_harness": bool(wrong_harness),
        "extra_modules": sorted(selected - oracle),
        "missing_oracle_modules": sorted(oracle - selected),
        "redundancy": float(minimality.get("redundancy", 0.0)),
    }


def summarize_results(rows: Sequence[Mapping[str, object]]) -> Dict[str, Dict[str, float]]:
    buckets: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["system"])].append(row)

    summary: Dict[str, Dict[str, float]] = {}
    for system, system_rows in buckets.items():
        count = float(len(system_rows))
        metrics = [row["metrics"] for row in system_rows]
        summary[system] = {
            "n": count,
            "success_rate": _mean(metric["success"] for metric in metrics),
            "avg_cost": _mean(metric["predicted_cost"] for metric in metrics),
            "avg_oracle_cost": _mean(metric["oracle_cost"] for metric in metrics),
            "avg_cost_delta": _mean(metric.get("cost_delta", metric["minimality_regret"]) for metric in metrics),
            "avg_excess_cost": _mean(metric.get("excess_cost", max(0.0, float(metric["minimality_regret"]))) for metric in metrics),
            "avg_minimality_regret": _mean(metric["minimality_regret"] for metric in metrics),
            "over_harness_rate": _mean(metric["over_harness"] for metric in metrics),
            "under_harness_rate": _mean(metric["under_harness"] for metric in metrics),
            "wrong_harness_rate": _mean(metric["wrong_harness"] for metric in metrics),
            "avg_redundancy": _mean(metric["redundancy"] for metric in metrics),
        }
    return summary


def load_results(path: str) -> List[Dict[str, object]]:
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def render_markdown_report(rows: Sequence[Mapping[str, object]]) -> str:
    summary = summarize_results(rows)
    lines = [
        "# GapHarness MVP Experiment Summary",
        "",
        "This report is generated from deterministic sandbox runs. It is suitable for MVP regression checks, not final paper numbers.",
        "",
        "## Aggregate Metrics",
        "",
        "| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | Redundancy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in sorted(summary):
        item = summary[system]
        lines.append(
            "| {system} | {n:.0f} | {success_rate:.2f} | {avg_cost:.2f} | {avg_oracle_cost:.2f} | {avg_cost_delta:.2f} | {avg_excess_cost:.2f} | {over_harness_rate:.2f} | {under_harness_rate:.2f} | {wrong_harness_rate:.2f} | {avg_redundancy:.2f} |".format(
                system=system,
                **item,
            )
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `harness success` is deterministic verifier pass against expected status plus gold obligation/capability coverage.",
            "- `cost_delta` is predicted harness cost minus oracle minimal harness cost. It can be negative for insufficient harnesses.",
            "- `excess_cost` is the per-row positive excess `max(0, cost_delta)`. Aggregate reports average that row-level value, so it can be positive even when mean cost delta is negative.",
            "- `over_harness` means predicted harness cost exceeds oracle minimal harness cost.",
            "- `under_harness` means a supported task failed obligation/capability coverage.",
            "- `redundancy` comes from drop-one counterfactual checks over selected modules.",
        ]
    )
    return "\n".join(lines) + "\n"


def profiler_confusion(rows: Sequence[Mapping[str, object]]) -> Dict[str, Dict[str, float]]:
    """Approximate profiler quality from compiled harness coverage.

    This is most useful for gapharness rows where harness obligations come from
    a profiler rather than a fixed baseline.
    """
    by_system: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        by_system[str(row["system"])].append(row)

    result: Dict[str, Dict[str, float]] = {}
    for system, system_rows in by_system.items():
        tp = fp = fn = 0
        cap_tp = cap_fp = cap_fn = 0
        for row in system_rows:
            if "harness" not in row:
                continue
            gold_obs = set(row["task"]["gold_obligations"])
            pred_obs = set(row["harness"]["obligations"])
            tp += len(gold_obs & pred_obs)
            fp += len(pred_obs - gold_obs)
            fn += len(gold_obs - pred_obs)

            gold_caps = set(row["task"]["required_capabilities"])
            pred_caps = set(row["harness"]["capabilities"])
            cap_tp += len(gold_caps & pred_caps)
            cap_fp += len(pred_caps - gold_caps)
            cap_fn += len(gold_caps - pred_caps)
        result[system] = {
            "obligation_precision": _precision(tp, fp),
            "obligation_recall": _recall(tp, fn),
            "obligation_f1": _f1(tp, fp, fn),
            "capability_precision": _precision(cap_tp, cap_fp),
            "capability_recall": _recall(cap_tp, cap_fn),
            "capability_f1": _f1(cap_tp, cap_fp, cap_fn),
        }
    return result


def _existing_keys(path: Path) -> Set[Tuple[str, str, str]]:
    if not path.exists():
        return set()
    keys = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            keys.add(_row_key(str(row.get("task_id")), str(row.get("system")), str(row.get("profiler"))))
    return keys


def _row_key(task_id: str, system_name: str, profiler: str) -> Tuple[str, str, str]:
    return (task_id, system_name, profiler)


def _mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / float(len(values_list))


def _precision(tp: int, fp: int) -> float:
    denominator = tp + fp
    return float(tp) / float(denominator) if denominator else 1.0


def _recall(tp: int, fn: int) -> float:
    denominator = tp + fn
    return float(tp) / float(denominator) if denominator else 1.0


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _precision(tp, fp)
    recall = _recall(tp, fn)
    denominator = precision + recall
    return 2.0 * precision * recall / denominator if denominator else 0.0
