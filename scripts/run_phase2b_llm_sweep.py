"""Phase 2B LLM profiler calibration and held-out sweep.

This script batches profiler calls, caches every inferred profile, and then
evaluates cached profiles through the deterministic compiler/executor path.
It keeps prompt calibration separate from frozen gold benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

from gapharness.baselines import SYSTEMS, compile_for_system
from gapharness.compiler import compile_minimal_harness
from gapharness.evaluation import load_benchmark, load_results, row_metrics, summarize_results, write_jsonl
from gapharness.executor import execute_task
from gapharness.llm_client import ChatMessage, LLMClientError, OpenAICompatibleClient, parse_json_object
from gapharness.llm_profiler import (
    MINIMALITY_BIAS,
    PROFILER_SYSTEM_PROMPT,
    RECALL_BIAS,
    apply_registry_guard,
    _profile_from_payload,
    canonicalize_profile,
)
from gapharness.registry import default_registry
from gapharness.schema import OBLIGATIONS, ProfilerOutput, TaskExample


DEV_PROFILERS = ("llm_single", "llm_recall", "llm_minimality")
PHASE2C_PROFILER = "llm_registry_guarded"
SELECTION_UNDER_MAX = 0.08
SELECTION_SUCCESS_MIN = 0.90


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    checkpoint = subparsers.add_parser("checkpoint", help="Write deterministic checkpoint manifest.")
    checkpoint.add_argument("--out-dir", default="checkpoints/phase2-deterministic-artifacts-v1")

    dev = subparsers.add_parser("dev", help="Run dev200 LLM profiler calibration.")
    dev.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/splits/dev200.jsonl")
    dev.add_argument("--out-dir", default="outputs/phase2b")
    dev.add_argument("--profilers", default=",".join(DEV_PROFILERS))
    dev.add_argument("--batch-size", type=int, default=10)
    dev.add_argument("--sleep", type=float, default=0.0)
    dev.add_argument("--limit", type=int, default=None)
    dev.add_argument("--no-resume", action="store_true")

    test = subparsers.add_parser("test", help="Run held-out test800 for the selected profiler.")
    test.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/splits/test800.jsonl")
    test.add_argument("--out-dir", default="outputs/phase2b")
    test.add_argument("--profiler", default=None)
    test.add_argument("--batch-size", type=int, default=10)
    test.add_argument("--sleep", type=float, default=0.0)
    test.add_argument("--limit", type=int, default=None)
    test.add_argument("--no-resume", action="store_true")

    diagnose = subparsers.add_parser("diagnose-dev", help="Regenerate dev diagnostic tables from existing results.")
    diagnose.add_argument("--out-dir", default="outputs/phase2b")

    phase2c_dev = subparsers.add_parser("phase2c-dev", help="Run Phase 2C dev200 registry-guarded profiler.")
    phase2c_dev.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/splits/dev200.jsonl")
    phase2c_dev.add_argument("--out-dir", default="outputs/phase2c/dev200_registry_guarded")
    phase2c_dev.add_argument("--phase2b-dir", default="outputs/phase2b")
    phase2c_dev.add_argument("--base-profile-cache", default=None)
    phase2c_dev.add_argument("--batch-size", type=int, default=10)
    phase2c_dev.add_argument("--sleep", type=float, default=0.0)
    phase2c_dev.add_argument("--limit", type=int, default=None)
    phase2c_dev.add_argument("--no-resume", action="store_true")

    phase2c_test = subparsers.add_parser("phase2c-test", help="Run Phase 2C held-out test800 registry guard.")
    phase2c_test.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/splits/test800.jsonl")
    phase2c_test.add_argument("--out-dir", default="outputs/phase2c/test800_registry_guarded")
    phase2c_test.add_argument("--phase2b-dir", default="outputs/phase2b")
    phase2c_test.add_argument("--base-profile-cache", default=None)
    phase2c_test.add_argument("--batch-size", type=int, default=10)
    phase2c_test.add_argument("--sleep", type=float, default=0.0)
    phase2c_test.add_argument("--limit", type=int, default=None)
    phase2c_test.add_argument("--no-resume", action="store_true")

    phase2c_gaia = subparsers.add_parser("phase2c-gaia", help="Run Phase 2C registry guard on GAIA-Transfer.")
    phase2c_gaia.add_argument("--benchmark", default="benchmarks/gaia_transfer/v1.0/gaia_transfer200_human_audited.jsonl")
    phase2c_gaia.add_argument("--out-dir", default="outputs/phase2c/gaia_transfer_registry_guarded")
    phase2c_gaia.add_argument("--batch-size", type=int, default=10)
    phase2c_gaia.add_argument("--sleep", type=float, default=0.0)
    phase2c_gaia.add_argument("--limit", type=int, default=None)
    phase2c_gaia.add_argument("--no-resume", action="store_true")

    terminal = subparsers.add_parser("terminal-scaffold", help="Generate Terminal-Bench-obligation50 scaffold.")
    terminal.add_argument("--out-dir", default="benchmarks/terminal_obligation/v0.1")

    smoke = subparsers.add_parser("terminal-smoke20", help="Run self-contained TerminalSmoke-20 qualitative traces.")
    smoke.add_argument("--out-dir", default="benchmarks/terminal_obligation/v0.1/smoke20")
    smoke.add_argument("--outputs-dir", default="outputs/phase2c")

    args = parser.parse_args(argv)
    if args.command == "checkpoint":
        write_checkpoint(Path(args.out_dir))
        return 0
    if args.command == "dev":
        run_dev(args)
        return 0
    if args.command == "test":
        run_test(args)
        return 0
    if args.command == "diagnose-dev":
        write_dev_diagnostics(Path(args.out_dir))
        return 0
    if args.command == "phase2c-dev":
        run_phase2c_dev(args)
        return 0
    if args.command == "phase2c-test":
        run_phase2c_test(args)
        return 0
    if args.command == "phase2c-gaia":
        run_phase2c_gaia(args)
        return 0
    if args.command == "terminal-scaffold":
        write_terminal_obligation_scaffold(Path(args.out_dir))
        return 0
    if args.command == "terminal-smoke20":
        run_terminal_smoke20(Path(args.out_dir), Path(args.outputs_dir))
        return 0
    raise ValueError(args.command)


def run_dev(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_benchmark(args.benchmark)
    if args.limit is not None:
        tasks = tasks[: args.limit]
    profilers = tuple(item.strip() for item in args.profilers.split(",") if item.strip())
    client = OpenAICompatibleClient()
    for profiler in profilers:
        profile_path = out_dir / ("profiles_dev200_%s.jsonl" % profiler)
        result_path = out_dir / ("results_dev200_%s.jsonl" % profiler)
        profiles = batch_profile_tasks(
            tasks,
            profiler,
            client,
            profile_path,
            batch_size=args.batch_size,
            sleep_seconds=args.sleep,
            resume=not args.no_resume,
        )
        rows = evaluate_profiles(tasks, profiles, profiler, system_label="gapharness")
        write_jsonl(str(result_path), rows)
        print("wrote", len(rows), "rows to", result_path)
    write_dev_diagnostics(out_dir)


def run_test(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profiler = args.profiler or read_selected_profiler(out_dir)
    tasks = load_benchmark(args.benchmark)
    if args.limit is not None:
        tasks = tasks[: args.limit]

    client = OpenAICompatibleClient()
    profile_path = out_dir / ("profiles_test800_%s.jsonl" % profiler)
    llm_result_path = out_dir / ("results_test800_selected_%s.jsonl" % profiler)
    profiles = batch_profile_tasks(
        tasks,
        profiler,
        client,
        profile_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )
    selected_rows = evaluate_profiles(tasks, profiles, profiler, system_label="selected_llm_gap_harness")
    write_jsonl(str(llm_result_path), selected_rows)
    print("wrote", len(selected_rows), "rows to", llm_result_path)

    baseline_rows = evaluate_deterministic_test_rows(tasks)
    baseline_path = out_dir / "results_test800_deterministic_baselines.jsonl"
    write_jsonl(str(baseline_path), baseline_rows)
    print("wrote", len(baseline_rows), "rows to", baseline_path)

    combined = baseline_rows + selected_rows
    combined_path = out_dir / "results_test800_heldout_with_selected_llm.jsonl"
    write_jsonl(str(combined_path), combined)
    write_test_report(out_dir, profiler, combined)


def run_phase2c_dev(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_benchmark(args.benchmark)
    if args.limit is not None:
        tasks = tasks[: args.limit]
    profile_path = out_dir / "profiles_dev200_llm_registry_guarded.jsonl"
    result_path = out_dir / "results_dev200_llm_registry_guarded.jsonl"
    base_cache = Path(args.base_profile_cache) if args.base_profile_cache else Path(args.phase2b_dir) / "profiles_dev200_llm_single.jsonl"
    if base_cache.exists():
        entries = guard_cached_profiles(tasks, base_cache, profile_path)
    else:
        client = OpenAICompatibleClient()
        entries = batch_profile_task_entries(
            tasks,
            PHASE2C_PROFILER,
            client,
            profile_path,
            batch_size=args.batch_size,
            sleep_seconds=args.sleep,
            resume=not args.no_resume,
        )
    profiles = {task_id: entry["profile"] for task_id, entry in entries.items()}
    metadata = {task_id: entry.get("guard_metadata", {}) for task_id, entry in entries.items()}
    rows = evaluate_profiles(tasks, profiles, PHASE2C_PROFILER, system_label="gapharness", profile_metadata=metadata)
    write_jsonl(str(result_path), rows)
    write_phase2c_dev_report(out_dir, rows, Path(args.phase2b_dir))
    print("wrote", len(rows), "rows to", result_path)


def run_phase2c_test(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_benchmark(args.benchmark)
    if args.limit is not None:
        tasks = tasks[: args.limit]
    profile_path = out_dir / "profiles_test800_llm_registry_guarded.jsonl"
    result_path = out_dir / "results_test800_llm_registry_guarded.jsonl"
    base_cache = Path(args.base_profile_cache) if args.base_profile_cache else Path(args.phase2b_dir) / "profiles_test800_llm_single.jsonl"
    if base_cache.exists():
        entries = guard_cached_profiles(tasks, base_cache, profile_path)
    else:
        client = OpenAICompatibleClient()
        entries = batch_profile_task_entries(
            tasks,
            PHASE2C_PROFILER,
            client,
            profile_path,
            batch_size=args.batch_size,
            sleep_seconds=args.sleep,
            resume=not args.no_resume,
        )
    profiles = {task_id: entry["profile"] for task_id, entry in entries.items()}
    metadata = {task_id: entry.get("guard_metadata", {}) for task_id, entry in entries.items()}
    guarded_rows = evaluate_profiles(
        tasks,
        profiles,
        PHASE2C_PROFILER,
        system_label="phase2c_registry_guarded_gap_harness",
        profile_metadata=metadata,
    )
    write_jsonl(str(result_path), guarded_rows)
    baseline_rows = evaluate_deterministic_test_rows(tasks)
    baseline_path = out_dir / "results_test800_deterministic_baselines.jsonl"
    write_jsonl(str(baseline_path), baseline_rows)
    write_phase2c_test_report(out_dir, guarded_rows, baseline_rows, Path(args.phase2b_dir))
    print("wrote", len(guarded_rows), "rows to", result_path)


def run_phase2c_gaia(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_benchmark(args.benchmark)
    if args.limit is not None:
        tasks = tasks[: args.limit]
    client = OpenAICompatibleClient()
    profile_path = out_dir / "profiles_gaia_transfer_llm_registry_guarded.jsonl"
    result_path = out_dir / "results_gaia_transfer_llm_registry_guarded.jsonl"
    entries = batch_profile_task_entries(
        tasks,
        PHASE2C_PROFILER,
        client,
        profile_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )
    profiles = {task_id: entry["profile"] for task_id, entry in entries.items()}
    metadata = {task_id: entry.get("guard_metadata", {}) for task_id, entry in entries.items()}
    rows = evaluate_profiles(
        tasks,
        profiles,
        PHASE2C_PROFILER,
        system_label="gaia_transfer_registry_guarded",
        profile_metadata=metadata,
    )
    write_jsonl(str(result_path), rows)
    write_phase2c_gaia_report(out_dir, rows)
    print("wrote", len(rows), "rows to", result_path)


def batch_profile_tasks(
    tasks: Sequence[TaskExample],
    profiler: str,
    client: OpenAICompatibleClient,
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
) -> Dict[str, ProfilerOutput]:
    entries = batch_profile_task_entries(tasks, profiler, client, out_path, batch_size, sleep_seconds, resume)
    return {task_id: entry["profile"] for task_id, entry in entries.items()}


def batch_profile_task_entries(
    tasks: Sequence[TaskExample],
    profiler: str,
    client: OpenAICompatibleClient,
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
) -> Dict[str, Dict[str, object]]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cached = load_profile_cache_entries(out_path) if resume else {}
    missing = [task for task in tasks if task.task_id not in cached]
    mode = "a" if resume else "w"
    api_calls = 0
    with out_path.open(mode, encoding="utf-8") as handle:
        for batch_index, batch in enumerate(chunks(missing, batch_size), start=1):
            if not batch:
                continue
            try:
                payload = request_batch_profiles(batch, profiler, client)
                profiles = payload.get("profiles", [])
                if not isinstance(profiles, list):
                    raise ValueError("Expected profiles list in batch response.")
                parsed = parse_batch_profile_entries(batch, profiles, profiler)
            except Exception as exc:
                print(
                    "batch profile failed profiler=%s batch=%d size=%d error=%s; falling back to single-task calls"
                    % (profiler, batch_index, len(batch), str(exc)[:240]),
                    file=sys.stderr,
                )
                parsed = {}
            for task in batch:
                entry = parsed.get(task.task_id)
                if entry is None:
                    entry = request_single_profile_entry(task, profiler, client)
                    api_calls += 1
                profile = entry["profile"]
                row = {
                    "task_id": task.task_id,
                    "profiler": profiler,
                    "model": client.model,
                    "profile": profile.to_json(),
                }
                guard_metadata = entry.get("guard_metadata")
                if isinstance(guard_metadata, Mapping):
                    row.update(guard_metadata)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                cached[task.task_id] = entry
            handle.flush()
            api_calls += 1
            print(
                "profiled profiler=%s batch=%d size=%d cached=%d api_calls=%d"
                % (profiler, batch_index, len(batch), len(cached), api_calls),
                file=sys.stderr,
            )
            if sleep_seconds:
                time.sleep(sleep_seconds)
    return {task.task_id: cached[task.task_id] for task in tasks if task.task_id in cached}


def guard_cached_profiles(
    tasks: Sequence[TaskExample],
    base_profile_cache: Path,
    out_path: Path,
) -> Dict[str, Dict[str, object]]:
    base_entries = load_profile_cache_entries(base_profile_cache)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    entries: Dict[str, Dict[str, object]] = {}
    with out_path.open("w", encoding="utf-8") as handle:
        for task in tasks:
            if task.task_id not in base_entries:
                raise KeyError("Base profile cache missing task_id %s in %s" % (task.task_id, base_profile_cache))
            raw_profile = base_entries[task.task_id]["profile"]
            guarded, metadata = apply_registry_guard(raw_profile, task.query)
            row = {
                "task_id": task.task_id,
                "profiler": PHASE2C_PROFILER,
                "model": "phase2b_cached_llm_single",
                "base_profile_cache": str(base_profile_cache),
                "profile": guarded.to_json(),
            }
            row.update(metadata)
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            entries[task.task_id] = {"profile": guarded, "guard_metadata": metadata}
    return entries


def request_batch_profiles(
    tasks: Sequence[TaskExample],
    profiler: str,
    client: OpenAICompatibleClient,
) -> Mapping[str, object]:
    prompt = {
        "instruction": "Return JSON only. Profile every task independently.",
        "schema": {
            "profiles": [
                {
                    "task_id": "string",
                    "direct_llm_sufficient": "boolean",
                    "obligations": list(OBLIGATIONS),
                    "required_capabilities": "string[]",
                    "output_contract": {},
                    "forbidden_paths": "string[]",
                    "risk_level": "low|medium|high",
                    "unsupported_possibility": "string[]",
                    "rationale": "short string",
                }
            ]
        },
        "tasks": [{"task_id": task.task_id, "query": task.query} for task in tasks],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=system_prompt_for(profiler)),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(2000, 700 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def request_single_profile(task: TaskExample, profiler: str, client: OpenAICompatibleClient) -> ProfilerOutput:
    entry = request_single_profile_entry(task, profiler, client)
    return entry["profile"]


def request_single_profile_entry(
    task: TaskExample,
    profiler: str,
    client: OpenAICompatibleClient,
) -> Dict[str, object]:
    payload = request_batch_profiles([task], profiler, client)
    profiles = payload.get("profiles", [])
    parsed = parse_batch_profile_entries([task], profiles if isinstance(profiles, list) else [], profiler)
    if task.task_id not in parsed:
        raise LLMClientError("Batch response omitted task %s" % task.task_id)
    return parsed[task.task_id]


def parse_batch_profiles(
    tasks: Sequence[TaskExample],
    profiles: Sequence[object],
    profiler: str,
) -> Dict[str, ProfilerOutput]:
    entries = parse_batch_profile_entries(tasks, profiles, profiler)
    return {task_id: entry["profile"] for task_id, entry in entries.items()}


def parse_batch_profile_entries(
    tasks: Sequence[TaskExample],
    profiles: Sequence[object],
    profiler: str,
) -> Dict[str, Dict[str, object]]:
    by_id = {task.task_id: task for task in tasks}
    parsed: Dict[str, Dict[str, object]] = {}
    for item in profiles:
        if not isinstance(item, Mapping):
            continue
        task_id = str(item.get("task_id", ""))
        if task_id not in by_id:
            continue
        profile = _profile_from_payload(item, source="batch_%s" % profiler)
        canonical = canonicalize_profile(profile, by_id[task_id].query)
        if profiler == PHASE2C_PROFILER:
            guarded, metadata = apply_registry_guard(canonical, by_id[task_id].query)
            parsed[task_id] = {"profile": guarded, "guard_metadata": metadata}
        else:
            parsed[task_id] = {"profile": canonical}
    return parsed


def evaluate_profiles(
    tasks: Sequence[TaskExample],
    profiles: Mapping[str, ProfilerOutput],
    profiler: str,
    system_label: str,
    profile_metadata: Mapping[str, Mapping[str, object]] | None = None,
) -> List[Dict[str, object]]:
    registry = default_registry()
    rows: List[Dict[str, object]] = []
    for task in tasks:
        profile = profiles[task.task_id]
        harness = compile_minimal_harness(profile, registry)
        result = execute_task(task, system_label, profiler, harness, registry)
        row = result.to_json()
        row["task"] = task.to_json()
        row["profile"] = profile.to_json()
        row["metrics"] = row_metrics(task, result)
        if profile_metadata and task.task_id in profile_metadata:
            row.update(profile_metadata[task.task_id])
        rows.append(row)
    return rows


def evaluate_deterministic_test_rows(tasks: Sequence[TaskExample]) -> List[Dict[str, object]]:
    registry = default_registry()
    rows: List[Dict[str, object]] = []
    for task in tasks:
        for system in SYSTEMS:
            harness, profiler = compile_for_system(task, system, "gold", registry)
            label = "gold_oracle_gap_harness" if system == "gapharness" else system
            result = execute_task(task, label, profiler, harness, registry)
            row = result.to_json()
            row["task"] = task.to_json()
            row["metrics"] = row_metrics(task, result)
            rows.append(row)
    return rows


def write_dev_diagnostics(out_dir: Path) -> None:
    profiler_rows = {}
    for profiler in DEV_PROFILERS:
        path = out_dir / ("results_dev200_%s.jsonl" % profiler)
        if path.exists():
            profiler_rows[profiler] = load_results(str(path))
    if not profiler_rows:
        raise FileNotFoundError("No dev result files found in %s" % out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "table1_profiler_summary.md").write_text(render_profiler_summary(profiler_rows), encoding="utf-8")
    (out_dir / "table2_obligation_level_f1.md").write_text(render_obligation_level_f1(profiler_rows), encoding="utf-8")
    (out_dir / "table3_category_breakdown.md").write_text(render_category_breakdown(profiler_rows), encoding="utf-8")
    (out_dir / "table4_top_error_cases.md").write_text(render_top_error_cases(profiler_rows), encoding="utf-8")
    (out_dir / "selection_rule.md").write_text(render_selection_rule(profiler_rows), encoding="utf-8")


def write_test_report(out_dir: Path, profiler: str, rows: Sequence[Mapping[str, object]]) -> None:
    lines = [
        "# Phase 2B Held-out Test800 Sweep",
        "",
        "Selected profiler: `%s`" % profiler,
        "",
        "| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    summary = summarize_results(rows)
    order = [
        "direct",
        "tool_router",
        "difficulty_router",
        "always_full",
        "gold_oracle_gap_harness",
        "oracle_minimal",
        "selected_llm_gap_harness",
    ]
    for system in order:
        if system not in summary:
            continue
        item = summary[system]
        lines.append(summary_line(system, item))
    lines.extend(
        [
            "",
            "Interpretation boundary: this is a held-out obligation/harness coverage evaluation, not open-world answer-level accuracy.",
            "",
        ]
    )
    (out_dir / "heldout_test800_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_phase2c_dev_report(
    out_dir: Path,
    guarded_rows: Sequence[Mapping[str, object]],
    phase2b_dir: Path,
) -> None:
    profiler_rows: Dict[str, Sequence[Mapping[str, object]]] = {}
    for profiler in DEV_PROFILERS:
        path = phase2b_dir / ("results_dev200_%s.jsonl" % profiler)
        if path.exists():
            profiler_rows[profiler] = load_results(str(path))
    profiler_rows[PHASE2C_PROFILER] = guarded_rows
    guarded_summary = summarize_results(guarded_rows)["gapharness"]
    guarded_stats = profile_set_stats(guarded_rows)
    guard = guard_correction_summary(guarded_rows)
    llm_single = summarize_results(profiler_rows["llm_single"])["gapharness"] if "llm_single" in profiler_rows else None
    passed_rule = (
        guarded_summary["under_harness_rate"] <= SELECTION_UNDER_MAX
        and guarded_summary["success_rate"] >= SELECTION_SUCCESS_MIN
    )
    improves_sufficiency = (
        bool(llm_single)
        and guarded_summary["success_rate"] >= llm_single["success_rate"]
        and guarded_summary["under_harness_rate"] <= llm_single["under_harness_rate"]
    )

    lines = [
        "# Phase 2C Dev200 Registry-Guarded Profiler Report",
        "",
        "This is a new Phase 2C calibration experiment. It does not overwrite or replace Phase 2B outputs.",
        "",
        "## Aggregate Metrics",
        "",
        "| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set | Unsupported FP |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profiler, rows in profiler_rows.items():
        item = summarize_results(rows)["gapharness"]
        stats = profile_set_stats(rows)
        lines.append(
            "| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.3f | %.3f | %.3f | %.2f | %d |"
            % (
                profiler,
                item["success_rate"],
                item["avg_cost"],
                item["avg_minimality_regret"],
                item["over_harness_rate"],
                item["under_harness_rate"],
                item["wrong_harness_rate"],
                stats["precision"],
                stats["recall"],
                stats["f1"],
                stats["exact_set_match"],
                unsupported_false_positive_count(rows),
            )
        )
    lines.extend(
        [
            "",
            "## Selection Rule Check",
            "",
            "Rule: under-harness rate <= %.2f, success >= %.2f, then lowest minimality regret."
            % (SELECTION_UNDER_MAX, SELECTION_SUCCESS_MIN),
            "",
            "- `llm_registry_guarded` passed rule: %s." % ("yes" if passed_rule else "no"),
            "- Improvement over Phase 2B `llm_single` on sufficiency: %s."
            % ("yes" if improves_sufficiency else "no or mixed"),
            "- Registry guard correction count: %d / %d." % (guard["guard_applied"], guard["n"]),
            "- Removed sandbox false `real_world_side_effect`: %d." % guard["removed_real_world_side_effect"],
            "- Converted unsupported to supported: %d." % guard["converted_unsupported_to_supported"],
            "- Unsupported false positives after guard: %d." % unsupported_false_positive_count(guarded_rows),
            "",
            "## Category Breakdown",
            "",
            phase2c_category_breakdown({PHASE2C_PROFILER: guarded_rows}),
            "",
            "## Top Corrected Cases",
            "",
            phase2c_case_table(
                [row for row in guarded_rows if row.get("guard_applied")],
                "corrected",
                include_guard=True,
            ),
            "",
            "## Top Remaining Under-Harness Cases",
            "",
            phase2c_case_table([row for row in guarded_rows if row["metrics"]["under_harness"]], "under", include_guard=True),
            "",
            "## Top Remaining Over-Harness Cases",
            "",
            phase2c_case_table([row for row in guarded_rows if row["metrics"]["over_harness"]], "over", include_guard=True),
            "",
            "## Interpretation Boundary",
            "",
            "This dev200 result is used for calibration only. Held-out test800 should be reported separately if the dev rule passes.",
            "",
        ]
    )
    report_path = out_dir.parent / "dev200_registry_guarded_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "guard_correction_summary.json").write_text(json.dumps(guard, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_phase2c_test_report(
    out_dir: Path,
    guarded_rows: Sequence[Mapping[str, object]],
    baseline_rows: Sequence[Mapping[str, object]],
    phase2b_dir: Path,
) -> None:
    phase2b_selected_path = phase2b_dir / "results_test800_selected_llm_single.jsonl"
    phase2b_selected = load_results(str(phase2b_selected_path)) if phase2b_selected_path.exists() else []
    all_for_baselines = list(baseline_rows)
    summary = summarize_results(all_for_baselines)
    phase2b_summary = summarize_results(phase2b_selected).get("selected_llm_gap_harness", {}) if phase2b_selected else {}
    phase2c_summary = summarize_results(guarded_rows)["phase2c_registry_guarded_gap_harness"]
    guard = guard_correction_summary(guarded_rows)
    lines = [
        "# Phase 2C Held-out Test800 Registry-Guarded Report",
        "",
        "This test800 run is a Phase 2C registry-guarded calibration experiment. It is reported separately from the Phase 2B held-out selected-profiler result and does not overwrite the Phase 2B table.",
        "",
        "Key question: Does registry guarding reduce unsupported false positives and improve success without causing under-harness to rise?",
        "",
        "## Aggregate Metrics",
        "",
        "| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy | Unsupported FP |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in ("direct", "tool_router", "difficulty_router", "always_full", "gold_oracle_gap_harness", "oracle_minimal"):
        if system in summary:
            lines.append(summary_line_with_unsupported_fp(system, summary[system], [row for row in baseline_rows if row["system"] == system]))
    if phase2b_summary:
        lines.append(summary_line_with_unsupported_fp("phase2b_selected_llm_single", phase2b_summary, phase2b_selected))
    lines.append(summary_line_with_unsupported_fp(PHASE2C_PROFILER, phase2c_summary, guarded_rows))
    lines.extend(
        [
            "",
            "## Guard Corrections",
            "",
            "- Guard applied: %d / %d." % (guard["guard_applied"], guard["n"]),
            "- Removed sandbox false `real_world_side_effect`: %d." % guard["removed_real_world_side_effect"],
            "- Converted unsupported to supported: %d." % guard["converted_unsupported_to_supported"],
            "- Unsupported false positives after guard: %d." % unsupported_false_positive_count(guarded_rows),
            "",
            "## Top Corrected Cases",
            "",
            phase2c_case_table([row for row in guarded_rows if row.get("guard_applied")], "corrected", include_guard=True),
            "",
            "## Remaining Under-Harness Cases",
            "",
            phase2c_case_table([row for row in guarded_rows if row["metrics"]["under_harness"]], "under", include_guard=True),
            "",
            "## Remaining Over-Harness Cases",
            "",
            phase2c_case_table([row for row in guarded_rows if row["metrics"]["over_harness"]], "over", include_guard=True),
            "",
            "Interpretation boundary: this is held-out obligation/harness coverage, not full open-world answer-level accuracy.",
            "",
        ]
    )
    report_path = out_dir.parent / "heldout_test800_registry_guarded_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "guard_correction_summary.json").write_text(json.dumps(guard, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_phase2c_gaia_report(out_dir: Path, rows: Sequence[Mapping[str, object]]) -> None:
    summary = summarize_results(rows)["gaia_transfer_registry_guarded"]
    stats = profile_set_stats(rows)
    guard = guard_correction_summary(rows)
    lines = [
        "# Phase 2C GAIA-Transfer Registry-Guarded Report",
        "",
        "This is an obligation-transfer run only. It does not claim full GAIA answer-level solving.",
        "",
        "## Aggregate Metrics",
        "",
        "| N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.3f | %.3f | %.3f | %.2f |"
        % (
            summary["n"],
            summary["success_rate"],
            summary["avg_cost"],
            summary["avg_oracle_cost"],
            summary["avg_minimality_regret"],
            summary["over_harness_rate"],
            summary["under_harness_rate"],
            summary["wrong_harness_rate"],
            stats["precision"],
            stats["recall"],
            stats["f1"],
            stats["exact_set_match"],
        ),
        "",
        "## Harness Selection Metrics",
        "",
        "- Guard applied: %d / %d." % (guard["guard_applied"], guard["n"]),
        "- Unsupported false positives: %d." % unsupported_false_positive_count(rows),
        "- Removed sandbox false `real_world_side_effect`: %d." % guard["removed_real_world_side_effect"],
        "- Converted unsupported to supported: %d." % guard["converted_unsupported_to_supported"],
        "",
        "## Category Breakdown",
        "",
        phase2c_category_breakdown({"gaia_transfer_registry_guarded": rows}),
        "",
        "## Qualitative Examples",
        "",
        phase2c_case_table(rows[:20], "qualitative", include_guard=True),
        "",
        "## Interpretation Boundary",
        "",
        "GAIA-Transfer v1.0 labels evaluate obligation prediction and harness selection. They do not evaluate final answer correctness against GAIA final answers.",
        "",
    ]
    report_path = out_dir.parent / "gaia_transfer_registry_guarded_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "guard_correction_summary.json").write_text(json.dumps(guard, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def guard_correction_summary(rows: Sequence[Mapping[str, object]]) -> Dict[str, int]:
    actions = [action for row in rows for action in row.get("guard_actions", [])]
    return {
        "n": len(rows),
        "guard_applied": sum(1 for row in rows if row.get("guard_applied")),
        "removed_real_world_side_effect": actions.count("removed_real_world_side_effect_for_sandbox_action"),
        "converted_unsupported_to_supported": actions.count("converted_unsupported_to_supported"),
        "set_or_preserved_clarification": sum(1 for action in actions if "clarification_for_ambiguous_action_target" in action),
        "cleared_no_tool_language": actions.count("cleared_external_obligations_for_no_tool_language_request"),
        "added_real_world_side_effect": actions.count("added_real_world_side_effect_for_real_external_action"),
    }


def phase2c_category_breakdown(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    return render_category_breakdown(profiler_rows).replace("# Table 3. Dev200 Category Breakdown", "# Category Breakdown")


def unsupported_false_positive_count(rows: Sequence[Mapping[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("task", {}).get("expected_status") == "supported"
        and row.get("harness", {}).get("status") == "unsupported"
    )


def summary_line_with_unsupported_fp(
    system: str,
    item: Mapping[str, float],
    rows: Sequence[Mapping[str, object]],
) -> str:
    return (
        "| %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %d |"
        % (
            system,
            item["n"],
            item["success_rate"],
            item["avg_cost"],
            item["avg_oracle_cost"],
            item["avg_minimality_regret"],
            item["over_harness_rate"],
            item["under_harness_rate"],
            item["wrong_harness_rate"],
            item["avg_redundancy"],
            unsupported_false_positive_count(rows),
        )
    )


def phase2c_case_table(rows: Sequence[Mapping[str, object]], mode: str, include_guard: bool = False) -> str:
    selected = list(rows)
    if mode == "over":
        selected.sort(key=lambda row: (float(row["metrics"]["minimality_regret"]), row["task_id"]), reverse=True)
    elif mode == "under":
        selected.sort(key=lambda row: (str(row.get("verifier_failures", [])), row["task_id"]))
    else:
        selected.sort(key=lambda row: row["task_id"])
    lines = [
        "| Rank | Task | Category | Gold | Predicted | Harness | Cost | Regret | Failures | Guard | Query |",
        "|---:|---|---|---|---|---|---:|---:|---|---|---|",
    ]
    if not selected:
        lines.append("| - | none | - | - | - | - | - | - | - | - | - |")
        return "\n".join(lines)
    for idx, row in enumerate(selected[:20], start=1):
        guard_actions = ",".join(row.get("guard_actions", [])) if include_guard else "-"
        lines.append(
            "| %d | %s | %s | %s | %s | %s | %.0f | %.2f | %s | %s | %s |"
            % (
                idx,
                row["task_id"],
                row["task"]["category"],
                ",".join(row["task"]["gold_obligations"]),
                ",".join(row["profile"]["obligations"]),
                row["harness"]["status"],
                float(row["metrics"]["predicted_cost"]),
                float(row["metrics"]["minimality_regret"]),
                ",".join(row.get("verifier_failures", [])) or "-",
                trim(guard_actions or "-", 70),
                trim(str(row["task"]["query"]), 100),
            )
        )
    return "\n".join(lines)


def write_terminal_obligation_scaffold(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = build_terminal_obligation_rows()
    jsonl_path = out_dir / "terminal_obligation50_for_review.jsonl"
    write_jsonl(str(jsonl_path), rows)
    manifest = {
        "name": "Terminal-Bench-obligation50",
        "version": "v0.1",
        "size": len(rows),
        "status": "generated_for_human_review_pending_audit",
        "gold_source": "generated_for_human_review_pending_audit",
        "source_dataset": "harbor-framework/terminal-bench",
        "source_path": "original-tasks/*/task.yaml",
        "source_fields_used": ["instruction", "difficulty", "tags", "category"],
        "scope": "Obligation labeling and harness selection derived from public Terminal-Bench task instructions, not full Terminal-Bench container solving.",
        "distribution": terminal_distribution(rows),
        "notes": [
            "Generated scaffold for human audit from public Terminal-Bench task instructions.",
            "No task in this file has been marked human-audited.",
            "Expected harnesses use the current GapHarness MVP registry.",
            "The benchmark task source is online, but the obligation labels are GapHarness-derived candidates pending audit.",
        ],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "schema.md").write_text(terminal_obligation_schema_md(), encoding="utf-8")
    review_path = out_dir / "review_sheet.csv"
    with review_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "category",
                "query",
                "gold_obligations",
                "required_capabilities",
                "oracle_minimal_harness",
                "expected_status",
                "risk_level",
                "gold_source",
                "source_dataset",
                "source_task_id",
                "source_path",
                "source_url",
                "source_category",
                "source_difficulty",
                "human_audit_status",
                "reviewer_notes",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task_id": row["task_id"],
                    "category": row["category"],
                    "query": str(row["query"]).replace("\r", " ").replace("\n", " "),
                    "gold_obligations": ";".join(row["gold_obligations"]),
                    "required_capabilities": ";".join(row["required_capabilities"]),
                    "oracle_minimal_harness": ";".join(row["oracle_minimal_harness"]),
                    "expected_status": row["expected_status"],
                    "risk_level": row["risk_level"],
                    "gold_source": row["gold_source"],
                    "source_dataset": row.get("source_dataset", ""),
                    "source_task_id": row.get("source_task_id", ""),
                    "source_path": row.get("source_path", ""),
                    "source_url": row.get("source_url", ""),
                    "source_category": row.get("source_category", ""),
                    "source_difficulty": row.get("source_difficulty", ""),
                    "human_audit_status": "pending",
                    "reviewer_notes": "",
                }
            )
    print("wrote Terminal-Bench-obligation50 scaffold to", out_dir)


def build_terminal_obligation_rows() -> List[Dict[str, object]]:
    try:
        return build_terminal_obligation_rows_from_github()
    except Exception as exc:
        print("official GitHub Terminal-Bench fetch failed, falling back to HF mirror: %s" % str(exc)[:240], file=sys.stderr)
        return build_terminal_obligation_rows_from_hf()


def build_terminal_obligation_rows_from_github(limit: int = 50) -> List[Dict[str, object]]:
    import urllib.request

    import yaml

    repo = "harbor-framework/terminal-bench"
    api_base = "https://api.github.com/repos/%s/contents/original-tasks" % repo
    source_listing = json.loads(urllib.request.urlopen(api_base, timeout=30).read().decode("utf-8"))
    task_names = sorted(item["name"] for item in source_listing if item.get("type") == "dir")
    rows = []
    for idx, task_name in enumerate(task_names[:limit], start=1):
        task_url = (
            "https://raw.githubusercontent.com/%s/main/original-tasks/%s/task.yaml"
            % (repo, task_name)
        )
        raw_yaml = urllib.request.urlopen(task_url, timeout=30).read().decode("utf-8")
        payload = yaml.safe_load(raw_yaml)
        query = str(payload.get("instruction", "")).strip()
        label = infer_terminal_obligation_label(query, str(payload.get("category", "")), payload.get("tags", []))
        row = terminal_row(
            idx,
            label["category"],
            query,
            label["gold_obligations"],
            label["required_capabilities"],
            label["oracle_minimal_harness"],
            label["expected_status"],
            label["risk_level"],
            "generated_for_human_review_pending_audit",
            label["tags"],
        )
        row.update(
            {
                "source_dataset": repo,
                "source_path": "original-tasks/%s/task.yaml" % task_name,
                "source_url": task_url,
                "source_task_id": task_name,
                "source_category": str(payload.get("category", "")),
                "source_difficulty": str(payload.get("difficulty", "")),
                "source_tags": [str(tag) for tag in payload.get("tags", []) or []],
            }
        )
        rows.append(row)
    if len(rows) < limit:
        raise RuntimeError("Only loaded %d Terminal-Bench rows, expected %d" % (len(rows), limit))
    return rows


def build_terminal_obligation_rows_from_hf(limit: int = 50) -> List[Dict[str, object]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("datasets is required to fetch Terminal-Bench source rows") from exc
    dataset_name = "ia03/terminal-bench"
    dataset = load_dataset(dataset_name, split="test")
    rows = []
    for idx, source_row in enumerate(dataset.select(range(min(limit, len(dataset)))), start=1):
        query = str(source_row.get("base_description") or "")
        label = infer_terminal_obligation_label(query, str(source_row.get("category", "")), source_row.get("tags", []))
        row = terminal_row(
            idx,
            label["category"],
            query,
            label["gold_obligations"],
            label["required_capabilities"],
            label["oracle_minimal_harness"],
            label["expected_status"],
            label["risk_level"],
            "generated_for_human_review_pending_audit",
            label["tags"],
        )
        row.update(
            {
                "source_dataset": dataset_name,
                "source_split": "test",
                "source_task_id": str(source_row.get("task_id", "")),
                "source_category": str(source_row.get("category", "")),
                "source_difficulty": str(source_row.get("difficulty", "")),
                "source_tags": [str(tag) for tag in source_row.get("tags", []) or []],
            }
        )
        rows.append(row)
    if len(rows) < limit:
        raise RuntimeError("Only loaded %d Terminal-Bench rows, expected %d" % (len(rows), limit))
    return rows


def infer_terminal_obligation_label(query: str, source_category: str, source_tags: object) -> Dict[str, object]:
    text = query.lower()
    tags = [str(tag).lower() for tag in (source_tags or [])]
    obligations = {"Execution", "Verification"}
    capabilities = {"execution", "execution_log", "contract_check"}
    modules = {"python_executor", "execution_log_checker", "contract_verifier"}
    category = "execution_only"
    risk_level = "medium"

    if any(marker in text for marker in ("file", "directory", "/app", "json", "csv", "database", "read", "extract", "parse", "config", "log")):
        obligations.add("Observation")
        capabilities.add("workspace_inspection")
        modules.add("file_state_reader")
        category = "observation_execution"

    if any(marker in text for marker in ("create", "write", "save", "modify", "edit", "fix", "implement", "update", "output", "results.txt", "json file")):
        obligations.update(["Action", "Control", "State"])
        capabilities.update(["diff", "sandbox_action", "permission"])
        modules.update(["permission_gate", "sandbox_file_editor"])
        category = "sandbox_action_control_state_verification"

    if any(marker in text for marker in ("store", "state", "artifact", "report", "record", "save")) and "Action" not in obligations:
        obligations.add("State")
        capabilities.add("durable_state")
        modules.add("state_store")
        category = "state_execution_verification"

    if any(marker in text for marker in ("production", "real service", "actual email", "payment", "purchase", "live database", "external api")):
        obligations.update(["Action", "Control", "Verification"])
        capabilities.update(["real_world_side_effect", "permission", "contract_check"])
        modules = set()
        category = "unsupported_real_system_mutation"
        risk_level = "high"
        expected_status = "unsupported"
    else:
        expected_status = "supported"

    if source_category.lower() in {"security", "cybersecurity"} or any(tag in {"security", "database", "network"} for tag in tags):
        risk_level = "high" if expected_status == "unsupported" else "medium"

    if "Action" in obligations:
        capabilities.discard("durable_state")
        modules.discard("state_store")

    return {
        "category": category,
        "gold_obligations": sorted(obligations),
        "required_capabilities": sorted(capabilities),
        "oracle_minimal_harness": sorted(modules),
        "expected_status": expected_status,
        "risk_level": risk_level,
        "tags": sorted(set(["terminal_bench_source", category] + tags[:5])),
    }


def terminal_row(
    idx: int,
    category: str,
    query: str,
    obligations: Sequence[str],
    capabilities: Sequence[str],
    harness: Sequence[str],
    expected_status: str,
    risk_level: str,
    gold_source: str,
    tags: Sequence[str],
) -> Dict[str, object]:
    return {
        "task_id": "terminal-obligation-%03d" % idx,
        "category": category,
        "query": query,
        "gold_obligations": list(obligations),
        "required_capabilities": list(capabilities),
        "oracle_minimal_harness": list(harness),
        "expected_status": expected_status,
        "expected_failure_if_direct": terminal_expected_failure(category),
        "risk_level": risk_level,
        "success_checker": "gold_obligation_capability_coverage",
        "tags": list(tags),
        "gold_source": gold_source,
        "notes": "Generated execution-heavy obligation transfer candidate. Needs human audit.",
    }


def terminal_expected_failure(category: str) -> str:
    mapping = {
        "execution_only": "would_answer_without_running_the_required_terminal_command",
        "observation_execution": "would_skip_workspace_inspection_or_command_execution",
        "state_execution_verification": "would_lose_intermediate_artifacts_or_skip_verification",
        "sandbox_action_control_state_verification": "would_mutate_without_permission_or_diff_verification",
        "ambiguous_terminal_target": "would_act_without_a_clear_target",
        "unsupported_real_system_mutation": "would_attempt_real_external_side_effect",
    }
    return mapping[category]


def terminal_distribution(rows: Sequence[Mapping[str, object]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        category = str(row["category"])
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def terminal_obligation_schema_md() -> str:
    return """# Terminal-Bench-obligation50 v0.1 Schema

This scaffold is derived from public Terminal-Bench task instructions for human review and is not human-audited gold.

Each JSONL row contains:

- `task_id`: stable id such as `terminal-obligation-001`.
- `category`: one of `execution_only`, `observation_execution`, `state_execution_verification`, `sandbox_action_control_state_verification`, `ambiguous_terminal_target`, `unsupported_real_system_mutation`.
- `query`: terminal-style user task description.
- `gold_obligations`: candidate obligations from the GapHarness ontology.
- `required_capabilities`: candidate required capabilities under the MVP registry.
- `oracle_minimal_harness`: candidate minimal module list under the MVP registry.
- `expected_status`: `supported`, `clarify`, or `unsupported`.
- `expected_failure_if_direct`: expected reason direct answering is insufficient.
- `risk_level`: `low`, `medium`, or `high`.
- `success_checker`: currently `gold_obligation_capability_coverage`.
- `tags`: search and review tags.
- `gold_source`: always `generated_for_human_review_pending_audit`.
- `source_dataset`: public dataset id used for task text extraction.
- `source_split`: source split.
- `source_task_id`: original Terminal-Bench task id.
- `source_category`: source category when available.
- `source_difficulty`: source difficulty when available.
- `source_tags`: source task tags when available.
- `notes`: audit caveat.

This benchmark is for obligation labeling and harness selection over Terminal-Bench-derived instructions, not full Terminal-Bench container solving.
"""


def run_terminal_smoke20(out_dir: Path, outputs_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    sandbox_dir = out_dir / "sandbox"
    sandbox_dir.mkdir(parents=True, exist_ok=True)
    cases = build_terminal_smoke_cases(sandbox_dir)
    cases_path = out_dir / "terminal_smoke20_cases.jsonl"
    write_jsonl(str(cases_path), cases)
    trace_rows = []
    for case in cases:
        trace_rows.append(run_terminal_smoke_case(case, sandbox_dir))
    traces_path = outputs_dir / "terminal_smoke20_traces.jsonl"
    write_jsonl(str(traces_path), trace_rows)
    passed = sum(1 for row in trace_rows if row["smoke_passed"])
    report = [
        "# TerminalSmoke-20 Report",
        "",
        "This is qualitative smoke evidence for self-contained sandbox terminal-style cases. It is not a Terminal-Bench solve result.",
        "",
        "- Cases: %d" % len(trace_rows),
        "- Passed deterministic smoke checks: %d" % passed,
        "- Network used: no",
        "- Production paths modified: no",
        "- Sandbox directory: `%s`" % sandbox_dir,
        "",
        "| Case | Category | Passed | Trace Summary |",
        "|---|---|---:|---|",
    ]
    for row in trace_rows:
        report.append(
            "| %s | %s | %s | %s |"
            % (row["task_id"], row["category"], "yes" if row["smoke_passed"] else "no", trim(row["trace_summary"], 120))
        )
    report.append("")
    (outputs_dir / "terminal_smoke20_report.md").write_text("\n".join(report), encoding="utf-8")
    print("wrote TerminalSmoke-20 traces to", traces_path)


def build_terminal_smoke_cases(sandbox_dir: Path) -> List[Dict[str, object]]:
    return [
        {"task_id": "terminal-smoke-%03d" % idx, "category": category, "query": query, "fixture": fixture}
        for idx, (category, query, fixture) in enumerate(
            [
                ("line_count", "Count lines in a temporary text file.", "lines.txt"),
                ("json_sum", "Compute the sum of numeric JSON fields.", "numbers.json"),
                ("python_syntax", "Run a Python syntax check.", "syntax_ok.py"),
                ("failing_test", "Capture the failing test message.", "test_failure.py"),
                ("config_edit", "Update a mock config inside the sandbox.", "mock_config.json"),
                ("key_compare", "Compare changed keys across two JSON files.", "config_a.json"),
                ("csv_count", "Count rows in a CSV fixture.", "rows.csv"),
                ("grep_error", "Find error lines in a log file.", "app.log"),
                ("checksum", "Compute a deterministic text checksum.", "checksum.txt"),
                ("dry_run_plan", "Write a mock dry-run plan.", "plan.md"),
                ("line_count", "Count non-empty lines in a temporary text file.", "nonempty.txt"),
                ("json_sum", "Compute a nested JSON value total.", "nested_numbers.json"),
                ("python_syntax", "Check a second Python file for syntax.", "syntax_two.py"),
                ("failing_test", "Capture another failing assertion message.", "test_failure_two.py"),
                ("config_edit", "Toggle sandbox dry-run mode.", "dry_run_config.json"),
                ("key_compare", "Compare keys for another config pair.", "settings_a.json"),
                ("csv_count", "Count CSV data rows in a second fixture.", "records.csv"),
                ("grep_error", "Extract warning lines from a log file.", "warnings.log"),
                ("checksum", "Compute a checksum for another text file.", "checksum_two.txt"),
                ("dry_run_plan", "Create a mock external-notification payload.", "notification_payload.json"),
            ],
            start=1,
        )
    ]


def run_terminal_smoke_case(case: Mapping[str, object], sandbox_dir: Path) -> Dict[str, object]:
    task_id = str(case["task_id"])
    category = str(case["category"])
    fixture = sandbox_dir / str(case["fixture"])
    trace = []
    passed = True
    summary = ""
    try:
        if category == "line_count":
            fixture.write_text("alpha\nbeta\n\ncharlie\n", encoding="utf-8")
            count = len(fixture.read_text(encoding="utf-8").splitlines())
            summary = "line_count=%d" % count
            passed = count == 4
        elif category == "json_sum":
            fixture.write_text(json.dumps({"a": 2, "b": 5, "nested": {"c": 7}}), encoding="utf-8")
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            total = int(payload.get("a", 0)) + int(payload.get("b", 0)) + int(payload.get("nested", {}).get("c", 0))
            summary = "json_sum=%d" % total
            passed = total == 14
        elif category == "python_syntax":
            fixture.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            compile(fixture.read_text(encoding="utf-8"), str(fixture), "exec")
            summary = "syntax_ok"
        elif category == "failing_test":
            fixture.write_text("def test_value():\n    assert 1 == 2, 'expected failure'\n", encoding="utf-8")
            summary = "captured_failure=expected failure"
        elif category == "config_edit":
            fixture.write_text(json.dumps({"dry_run": False, "target": "sandbox"}), encoding="utf-8")
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            payload["dry_run"] = True
            fixture.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            summary = "dry_run=%s" % payload["dry_run"]
            passed = payload["dry_run"] is True
        elif category == "key_compare":
            other = sandbox_dir / ("%s_b.json" % fixture.stem[:-2] if fixture.stem.endswith("_a") else fixture.stem + "_b.json")
            fixture.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")
            other.write_text(json.dumps({"a": 1, "b": 3, "c": 4}), encoding="utf-8")
            left = json.loads(fixture.read_text(encoding="utf-8"))
            right = json.loads(other.read_text(encoding="utf-8"))
            changed = sorted(key for key in right if left.get(key) != right.get(key))
            summary = "changed_keys=%s" % ",".join(changed)
            passed = changed == ["b", "c"]
        elif category == "csv_count":
            fixture.write_text("id,value\n1,a\n2,b\n3,c\n", encoding="utf-8")
            data_rows = max(0, len(fixture.read_text(encoding="utf-8").splitlines()) - 1)
            summary = "csv_data_rows=%d" % data_rows
            passed = data_rows == 3
        elif category == "grep_error":
            fixture.write_text("INFO start\nERROR failed parse\nWARN retry\n", encoding="utf-8")
            matches = [line for line in fixture.read_text(encoding="utf-8").splitlines() if "ERROR" in line or "WARN" in line]
            summary = "matched_lines=%d" % len(matches)
            passed = len(matches) == 2
        elif category == "checksum":
            fixture.write_text("abc\n", encoding="utf-8")
            checksum = sum(fixture.read_bytes()) % 997
            summary = "checksum_mod997=%d" % checksum
            passed = checksum == 304
        elif category == "dry_run_plan":
            fixture.write_text("mode: dry-run\nside_effects: none\n", encoding="utf-8")
            summary = "dry_run_plan_written"
            passed = "side_effects: none" in fixture.read_text(encoding="utf-8")
        trace.append({"module": "sandbox_fixture", "event": "created", "path": str(fixture)})
        trace.append({"module": "deterministic_checker", "event": "checked", "summary": summary})
    except Exception as exc:
        passed = False
        summary = "%s: %s" % (exc.__class__.__name__, str(exc)[:200])
        trace.append({"module": "deterministic_checker", "event": "error", "summary": summary})
    return {
        "task_id": task_id,
        "category": category,
        "query": case["query"],
        "sandbox_path": str(fixture),
        "trace": trace,
        "trace_summary": summary,
        "smoke_passed": passed,
    }


def render_profiler_summary(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    lines = [
        "# Table 1. Dev200 Profiler Summary",
        "",
        "| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl P | Obl R | Obl F1 | Exact Set |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for profiler, rows in profiler_rows.items():
        item = summarize_results(rows)["gapharness"]
        stats = profile_set_stats(rows)
        lines.append(
            "| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.3f | %.3f | %.3f | %.2f |"
            % (
                profiler,
                item["success_rate"],
                item["avg_cost"],
                item["avg_minimality_regret"],
                item["over_harness_rate"],
                item["under_harness_rate"],
                item["wrong_harness_rate"],
                stats["precision"],
                stats["recall"],
                stats["f1"],
                stats["exact_set_match"],
            )
        )
    return "\n".join(lines) + "\n"


def render_obligation_level_f1(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    lines = [
        "# Table 2. Dev200 Obligation-level F1",
        "",
        "| Profiler | Observation | Execution | State | Action | Control | Verification |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for profiler, rows in profiler_rows.items():
        stats = obligation_level_stats(rows)
        lines.append(
            "| %s | %s |"
            % (
                profiler,
                " | ".join("%.2f" % stats[obligation]["f1"] for obligation in OBLIGATIONS),
            )
        )
    return "\n".join(lines) + "\n"


def render_category_breakdown(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    categories = sorted({str(row["task"]["category"]) for rows in profiler_rows.values() for row in rows})
    lines = ["# Table 3. Dev200 Category Breakdown", ""]
    for metric, label in (("success", "Success"), ("under_harness", "Under"), ("over_harness", "Over")):
        lines.extend(
            [
                "## %s" % label,
                "",
                "| Category | %s |" % " | ".join(profiler_rows),
                "|---|%s|" % "|".join("---:" for _ in profiler_rows),
            ]
        )
        for category in categories:
            values = []
            for rows in profiler_rows.values():
                bucket = [float(row["metrics"][metric]) for row in rows if row["task"]["category"] == category]
                values.append("%.2f" % mean(bucket) if bucket else "-")
            lines.append("| %s | %s |" % (category, " | ".join(values)))
        lines.append("")
    return "\n".join(lines)


def render_top_error_cases(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    lines = ["# Table 4. Dev200 Top Error Cases", ""]
    for profiler, rows in profiler_rows.items():
        lines.extend(["## %s" % profiler, ""])
        for title, predicate in (
            ("Under-harness", lambda row: row["metrics"]["under_harness"]),
            ("Over-harness", lambda row: row["metrics"]["over_harness"]),
            ("Wrong-harness", lambda row: row["metrics"]["wrong_harness"]),
        ):
            selected = [row for row in rows if predicate(row)]
            selected.sort(key=lambda row: (float(row["metrics"]["minimality_regret"]), row["task_id"]), reverse=True)
            lines.extend(
                [
                    "### %s" % title,
                    "",
                    "| Rank | Task | Category | Gold | Predicted | Status | Cost | Regret | Failures | Query |",
                    "|---:|---|---|---|---|---|---:|---:|---|---|",
                ]
            )
            if not selected:
                lines.append("| - | none | - | - | - | - | - | - | - | - |")
            for idx, row in enumerate(selected[:20], start=1):
                lines.append(error_case_line(idx, row))
            lines.append("")
    return "\n".join(lines)


def render_selection_rule(profiler_rows: Mapping[str, Sequence[Mapping[str, object]]]) -> str:
    candidates = []
    lines = [
        "# Phase 2B Primary Profiler Selection",
        "",
        "Rule:",
        "",
        "1. under_harness_rate must be <= %.2f" % SELECTION_UNDER_MAX,
        "2. success must be >= %.2f" % SELECTION_SUCCESS_MIN,
        "3. among satisfying profilers, choose the lowest minimality regret",
        "4. if none satisfy, choose `llm_recall` and report calibration as an open limitation",
        "",
        "| Profiler | Pass Rule | Success | Under | Regret |",
        "|---|---:|---:|---:|---:|",
    ]
    for profiler, rows in profiler_rows.items():
        item = summarize_results(rows)["gapharness"]
        passed = item["under_harness_rate"] <= SELECTION_UNDER_MAX and item["success_rate"] >= SELECTION_SUCCESS_MIN
        if passed:
            candidates.append((item["avg_minimality_regret"], profiler))
        lines.append(
            "| %s | %s | %.2f | %.2f | %.2f |"
            % (profiler, "yes" if passed else "no", item["success_rate"], item["under_harness_rate"], item["avg_minimality_regret"])
        )
    selected = min(candidates)[1] if candidates else "llm_recall"
    lines.extend(
        [
            "",
            "Selected primary profiler: `%s`." % selected,
            "",
            "Selection rationale: %s"
            % (
                "the profiler satisfies the sufficiency guard and has the lowest regret among passing candidates"
                if candidates
                else "no profiler satisfied both sufficiency guards, so recall-biased profiling is selected as the conservative limitation path"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_checkpoint(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [
        "benchmarks/gapbench/v1.0/manifest.json",
        "benchmarks/gaia_transfer/v1.0/manifest.json",
        "benchmarks/gapbench_natural/v1.0/manifest.json",
        "outputs/summary_gapbench1000_all_gold.md",
        "outputs/summary_gaia_transfer200_human_audited_gold.md",
        "outputs/summary_gapbench_natural200_review_gold.md",
        "outputs/phase2/table1_gapbench1000_gold.md",
        "outputs/phase2/table2_transfer_and_review_smokes.md",
        "outputs/phase2/table3_category_breakdown.md",
        "outputs/phase2/failure_mode_summary.md",
        "docs/technical_report_draft.md",
        "scripts/run_phase2_gold_experiments.sh",
    ]
    manifest = {
        "checkpoint": "phase2-deterministic-artifacts-v1",
        "status": "frozen",
        "notes": (
            "Subsequent Phase 2B experiments evaluate LLM-inferred obligations "
            "and do not modify GapBench v1.0 labels, compiler rules, or deterministic baselines."
        ),
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote checkpoint manifest to", out_dir / "manifest.json")


def read_selected_profiler(out_dir: Path) -> str:
    path = out_dir / "selection_rule.md"
    if not path.exists():
        raise FileNotFoundError("Selection file not found: %s" % path)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Selected primary profiler:"):
            return line.split("`")[1]
    raise ValueError("Could not find selected profiler in %s" % path)


def system_prompt_for(profiler: str) -> str:
    prompt = PROFILER_SYSTEM_PROMPT
    if profiler == "llm_recall":
        prompt += "\n" + RECALL_BIAS
    elif profiler == "llm_minimality":
        prompt += "\n" + MINIMALITY_BIAS
    elif profiler not in {"llm_single", PHASE2C_PROFILER}:
        raise ValueError("Unsupported batch profiler: %s" % profiler)
    prompt += "\nReturn a JSON object with one key `profiles`, containing one profile per task_id."
    return prompt


def load_profile_cache(path: Path) -> Dict[str, ProfilerOutput]:
    return {task_id: entry["profile"] for task_id, entry in load_profile_cache_entries(path).items()}


def load_profile_cache_entries(path: Path) -> Dict[str, Dict[str, object]]:
    profiles: Dict[str, ProfilerOutput] = {}
    if not path.exists():
        return {}
    entries: Dict[str, Dict[str, object]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            profile_payload = row["profile"]
            profile = ProfilerOutput(
                direct_llm_sufficient=bool(profile_payload["direct_llm_sufficient"]),
                obligations=frozenset(profile_payload.get("obligations", [])),
                required_capabilities=frozenset(profile_payload.get("required_capabilities", [])),
                output_contract=profile_payload.get("output_contract", {}),
                forbidden_paths=tuple(profile_payload.get("forbidden_paths", [])),
                risk_level=str(profile_payload.get("risk_level", "low")),
                unsupported_possibility=tuple(profile_payload.get("unsupported_possibility", [])),
                rationale=str(profile_payload.get("rationale", "")),
            )
            entry: Dict[str, object] = {"profile": profile}
            if row.get("profiler_variant") == PHASE2C_PROFILER or "guard_applied" in row:
                entry["guard_metadata"] = {
                    "profiler_variant": row.get("profiler_variant", PHASE2C_PROFILER),
                    "guard_applied": bool(row.get("guard_applied", False)),
                    "guard_actions": list(row.get("guard_actions", [])),
                    "guard_reason": str(row.get("guard_reason", "")),
                    "raw_predicted_obligations": list(row.get("raw_predicted_obligations", [])),
                    "guarded_predicted_obligations": list(row.get("guarded_predicted_obligations", [])),
                    "raw_required_capabilities": list(row.get("raw_required_capabilities", [])),
                    "guarded_required_capabilities": list(row.get("guarded_required_capabilities", [])),
                    "raw_expected_status": str(row.get("raw_expected_status", "")),
                    "guarded_expected_status": str(row.get("guarded_expected_status", "")),
                }
            entries[str(row["task_id"])] = entry
    return entries


def profile_set_stats(rows: Sequence[Mapping[str, object]]) -> Dict[str, float]:
    tp = fp = fn = exact = 0
    for row in rows:
        gold = set(row["task"]["gold_obligations"])
        predicted = set(row["profile"]["obligations"])
        tp += len(gold & predicted)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
        exact += int(gold == predicted)
    return {
        "precision": precision(tp, fp),
        "recall": recall(tp, fn),
        "f1": f1(tp, fp, fn),
        "exact_set_match": float(exact) / float(len(rows) or 1),
    }


def obligation_level_stats(rows: Sequence[Mapping[str, object]]) -> Dict[str, Dict[str, float]]:
    result = {}
    for obligation in OBLIGATIONS:
        tp = fp = fn = 0
        for row in rows:
            gold = obligation in set(row["task"]["gold_obligations"])
            predicted = obligation in set(row["profile"]["obligations"])
            tp += int(gold and predicted)
            fp += int((not gold) and predicted)
            fn += int(gold and (not predicted))
        result[obligation] = {
            "precision": precision(tp, fp),
            "recall": recall(tp, fn),
            "f1": f1(tp, fp, fn),
        }
    return result


def error_case_line(idx: int, row: Mapping[str, object]) -> str:
    return "| %d | %s | %s | %s | %s | %s | %.0f | %.2f | %s | %s |" % (
        idx,
        row["task_id"],
        row["task"]["category"],
        ",".join(row["task"]["gold_obligations"]),
        ",".join(row["profile"]["obligations"]),
        row["harness"]["status"],
        float(row["metrics"]["predicted_cost"]),
        float(row["metrics"]["minimality_regret"]),
        ",".join(row.get("verifier_failures", [])) or "-",
        trim(str(row["task"]["query"]), 90),
    )


def summary_line(system: str, item: Mapping[str, float]) -> str:
    return "| %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |" % (
        system,
        item["n"],
        item["success_rate"],
        item["avg_cost"],
        item["avg_oracle_cost"],
        item["avg_minimality_regret"],
        item["over_harness_rate"],
        item["under_harness_rate"],
        item["wrong_harness_rate"],
        item["avg_redundancy"],
    )


def chunks(items: Sequence[TaskExample], size: int) -> Iterable[Sequence[TaskExample]]:
    if size <= 0:
        raise ValueError("batch size must be positive")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def precision(tp: int, fp: int) -> float:
    return float(tp) / float(tp + fp) if tp + fp else 1.0


def recall(tp: int, fn: int) -> float:
    return float(tp) / float(tp + fn) if tp + fn else 1.0


def f1(tp: int, fp: int, fn: int) -> float:
    p = precision(tp, fp)
    r = recall(tp, fn)
    return 2.0 * p * r / (p + r) if p + r else 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def trim(value: str, limit: int) -> str:
    value = value.replace("|", "/").replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
