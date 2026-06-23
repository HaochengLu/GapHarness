"""Run LLM-inferred SWE-HarnessExec-20 pipeline replay.

This script uses saved profiles/routes when present. If caches are missing, it
performs small batched API calls for 20 executable fixtures only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence

from gapharness.compiler import compile_minimal_harness
from gapharness.evaluation import row_metrics, write_jsonl
from gapharness.executor import execute_task
from gapharness.llm_client import OpenAICompatibleClient
from gapharness.registry import default_registry
from scripts.run_harness_exec20 import build_cases, case_to_task, render_report, run_case_trace, write_benchmark_artifacts
from scripts.run_phase2b_llm_sweep import PHASE2C_PROFILER, batch_profile_tasks, guard_cached_profiles
from scripts.run_phase4_reviewer_hardening import batch_route_tasks, harness_from_route


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", default="benchmarks/harness_exec/v1.0")
    parser.add_argument("--out-dir", default="outputs/final/harness_exec20_llm_pipeline")
    parser.add_argument("--audit-date", default="2026-06-23")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = Path(args.benchmark_dir)
    cases = build_cases()
    tasks = [case_to_task(case, args.audit_date) for case in cases]
    write_benchmark_artifacts(benchmark_dir, tasks, args.audit_date)

    client = OpenAICompatibleClient()
    base_profile_path = out_dir / "profiles_harness_exec20_llm_single.jsonl"
    llm_profiles = batch_profile_tasks(
        tasks,
        "llm_single",
        client,
        base_profile_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )
    guarded_path = out_dir / "profiles_harness_exec20_llm_registry_guarded.jsonl"
    guarded_entries = guard_cached_profiles(tasks, base_profile_path, guarded_path)
    guarded_profiles = {task_id: entry["profile"] for task_id, entry in guarded_entries.items()}
    guarded_metadata = {task_id: entry.get("guard_metadata", {}) for task_id, entry in guarded_entries.items()}

    route_path = out_dir / "routes_harness_exec20_llm_tool_router.jsonl"
    routes = batch_route_tasks(
        tasks,
        client,
        route_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )

    rows = []
    for case, task in zip(cases, tasks):
        rows.append(
            run_profile_case(
                case,
                task,
                "gapharness_llm",
                "llm_single",
                compile_minimal_harness(llm_profiles[task.task_id], default_registry()),
                out_dir,
                {"profile": llm_profiles[task.task_id].to_json()},
            )
        )
        rows.append(
            run_profile_case(
                case,
                task,
                "registry_guarded_gapharness",
                PHASE2C_PROFILER,
                compile_minimal_harness(guarded_profiles[task.task_id], default_registry()),
                out_dir,
                {
                    "profile": guarded_profiles[task.task_id].to_json(),
                    "guard_metadata": guarded_metadata.get(task.task_id, {}),
                },
            )
        )
        route = routes[task.task_id]
        rows.append(
            run_profile_case(
                case,
                task,
                "llm_tool_router",
                "llm_tool_router",
                harness_from_route(route),
                out_dir,
                {"route": dict(route)},
            )
        )

    write_jsonl(str(out_dir / "traces.jsonl"), rows)
    (out_dir / "summary.md").write_text(render_report(rows), encoding="utf-8")
    (out_dir / "manifest.json").write_text(render_manifest(rows), encoding="utf-8")
    print("wrote SWE-HarnessExec-20 LLM pipeline traces to %s" % out_dir)
    return 0


def run_profile_case(case, task, system: str, profiler: str, harness, out_dir: Path, extra: Mapping[str, object]):
    registry = default_registry()
    coverage_result = execute_task(task, system, profiler, harness, registry)
    exec_row = run_case_trace(case, task, system, profiler, harness.to_json(), out_dir)
    row = {
        "case_id": case.case_id,
        "task_id": task.task_id,
        "system": system,
        "profiler": profiler,
        "task": task.to_json(),
        "harness": harness.to_json(),
        "coverage_metrics": row_metrics(task, coverage_result),
        "coverage_verifier_passed": coverage_result.verifier_passed,
        "coverage_verifier_failures": list(coverage_result.verifier_failures),
        "exec_metrics": exec_row["exec_metrics"],
        "trace": exec_row["trace"],
        "sandbox_path": exec_row["sandbox_path"],
    }
    row.update(dict(extra))
    return row


def render_manifest(rows: Sequence[Mapping[str, object]]) -> str:
    summary = {}
    for row in rows:
        system = str(row["system"])
        bucket = [item for item in rows if item["system"] == system]
        summary[system] = {
            "n": len(bucket),
            "coverage_hs": mean(item["coverage_metrics"]["success"] for item in bucket),
            "trace_success": mean(item["exec_metrics"]["trace_success"] for item in bucket),
            "avg_cost": mean(item["coverage_metrics"]["predicted_cost"] for item in bucket),
            "missing_module_rate": mean(bool(item["exec_metrics"]["missing_required_modules"]) for item in bucket),
        }
    return json.dumps({"n_rows": len(rows), "systems": summary}, indent=2, sort_keys=True) + "\n"


def mean(values):
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / len(values_list)


if __name__ == "__main__":
    raise SystemExit(main())
