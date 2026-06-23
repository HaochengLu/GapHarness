"""Phase 4 reviewer-hardening experiments and paper artifacts.

This stage adds reviewer-requested checks without modifying Phase 2/3 frozen
results:

- LLM Tool Router baseline: direct module selection without obligation labels.
- Secondary adversarial label audit over a stratified GapBench-100 sample.
- Paper-facing metric tables with harness-coverage terminology and cost deltas.
- Paper-style figures for grouped over/under/wrong and registry guard effects.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from gapharness.evaluation import load_benchmark, load_results, row_metrics, summarize_results, write_jsonl
from gapharness.executor import execute_task
from gapharness.llm_client import ChatMessage, LLMClientError, OpenAICompatibleClient, parse_json_object
from gapharness.registry import default_registry, provided_capabilities, provided_obligations, total_cost
from gapharness.schema import CompiledHarness, OBLIGATIONS, TaskExample, frozen


PHASE4_DIR = Path("outputs/phase4")
PAPER_TABLE_DIR = Path("paper/tables")
PAPER_FIG_DIR = Path("paper/figures")

ROUTER_SYSTEM = """You are a module router baseline for GapHarness.

You select runtime modules directly. You must NOT use or infer the named
obligation ontology. Do not mention Observation, Execution, State, Action,
Control, or Verification in your response.

You receive a user query and a registry of available modules. Return JSON only:
{
  "routes": [
    {
      "task_id": "string",
      "expected_status": "supported" | "unsupported" | "clarify",
      "selected_modules": ["module_name"],
      "rationale": "short reason"
    }
  ]
}

Rules:
- Select only modules listed in the registry.
- Use an empty module list when a direct answer is sufficient.
- Return "clarify" if the target is ambiguous.
- Return "unsupported" if the request requires a real irreversible external
  side effect not represented by the registry.
- Prefer lower-cost module sets, but do not omit modules needed for a warranted
  answer or safe sandbox action.
- Do not use benchmark labels, hidden gold labels, or the obligation ontology.
"""

AUDIT_SYSTEM = """You are an adversarial secondary auditor for GapBench labels.

You are not judging final answer correctness. You are labeling what external
runtime support would be required for a warranted answer or sandbox action.

Allowed obligations:
- Observation
- Execution
- State
- Action
- Control
- Verification

Allowed capabilities:
evidence_sources, source_spans, execution, execution_log, workspace_inspection,
durable_state, diff, sandbox_action, permission, contract_check,
real_world_side_effect.

Return JSON only:
{
  "audits": [
    {
      "task_id": "string",
      "expected_status": "supported" | "unsupported" | "clarify",
      "obligations": ["..."],
      "required_capabilities": ["..."],
      "oracle_minimal_harness": ["module_name"],
      "rationale": "short reason"
    }
  ]
}

Use the provided registry descriptions. Do not see or assume existing gold
labels. Prefer minimal sufficient labels.
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    router = sub.add_parser("llm-tool-router")
    router.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/splits/test800.jsonl")
    router.add_argument("--out-dir", default=str(PHASE4_DIR / "llm_tool_router_test800"))
    router.add_argument("--system-label", default="llm_tool_router")
    router.add_argument("--batch-size", type=int, default=10)
    router.add_argument("--sleep", type=float, default=0.0)
    router.add_argument("--limit", type=int, default=None)
    router.add_argument("--subset", choices=["all", "negative"], default="all")
    router.add_argument("--no-resume", action="store_true")

    audit = sub.add_parser("secondary-audit")
    audit.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl")
    audit.add_argument("--out-dir", default=str(PHASE4_DIR / "secondary_audit_gapbench100"))
    audit.add_argument("--sample-size", type=int, default=100)
    audit.add_argument("--seed", type=int, default=1729)
    audit.add_argument("--batch-size", type=int, default=10)
    audit.add_argument("--sleep", type=float, default=0.0)
    audit.add_argument("--no-resume", action="store_true")

    tables = sub.add_parser("paper-tables")
    tables.add_argument("--out-dir", default=str(PHASE4_DIR))

    figures = sub.add_parser("paper-figures")
    figures.add_argument("--out-dir", default=str(PHASE4_DIR))

    all_cmd = sub.add_parser("all")
    all_cmd.add_argument("--batch-size", type=int, default=10)
    all_cmd.add_argument("--sleep", type=float, default=0.0)
    all_cmd.add_argument("--no-resume", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "llm-tool-router":
        run_llm_tool_router(args)
    elif args.command == "secondary-audit":
        run_secondary_audit(args)
    elif args.command == "paper-tables":
        write_phase4_tables(Path(args.out_dir))
    elif args.command == "paper-figures":
        write_phase4_figures(Path(args.out_dir))
    elif args.command == "all":
        router_dev_args = argparse.Namespace(
            benchmark="benchmarks/gapbench/v1.0/splits/dev200.jsonl",
            out_dir=str(PHASE4_DIR / "llm_tool_router_dev200"),
            system_label="llm_tool_router",
            batch_size=args.batch_size,
            sleep=args.sleep,
            limit=None,
            subset="all",
            no_resume=args.no_resume,
        )
        run_llm_tool_router(router_dev_args)
        router_args = argparse.Namespace(
            benchmark="benchmarks/gapbench/v1.0/splits/test800.jsonl",
            out_dir=str(PHASE4_DIR / "llm_tool_router_test800"),
            system_label="llm_tool_router",
            batch_size=args.batch_size,
            sleep=args.sleep,
            limit=None,
            subset="all",
            no_resume=args.no_resume,
        )
        run_llm_tool_router(router_args)
        negative_args = argparse.Namespace(
            benchmark="benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl",
            out_dir=str(PHASE4_DIR / "llm_tool_router_negative_controls"),
            system_label="llm_tool_router",
            batch_size=args.batch_size,
            sleep=args.sleep,
            limit=None,
            subset="negative",
            no_resume=args.no_resume,
        )
        run_llm_tool_router(negative_args)
        audit_args = argparse.Namespace(
            benchmark="benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl",
            out_dir=str(PHASE4_DIR / "secondary_audit_gapbench100"),
            sample_size=100,
            seed=1729,
            batch_size=args.batch_size,
            sleep=args.sleep,
            no_resume=args.no_resume,
        )
        run_secondary_audit(audit_args)
        write_phase4_tables(PHASE4_DIR)
        write_phase4_figures(PHASE4_DIR)
    else:
        raise ValueError(args.command)
    return 0


def run_llm_tool_router(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_benchmark(args.benchmark)
    if args.subset == "negative":
        tasks = [t for t in tasks if t.category in {"pure_language_negative", "tool_bait"}]
    if args.limit is not None:
        tasks = tasks[: args.limit]
    client = OpenAICompatibleClient()
    route_path = out_dir / "routes.jsonl"
    routes = batch_route_tasks(
        tasks,
        client,
        route_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )
    rows = evaluate_routes(tasks, routes, args.system_label)
    result_path = out_dir / "results_llm_tool_router.jsonl"
    write_jsonl(str(result_path), rows)
    report = render_llm_tool_router_report(rows, args.benchmark, args.subset)
    (out_dir / "llm_tool_router_report.md").write_text(report, encoding="utf-8")
    print("wrote", len(rows), "rows to", result_path)


def batch_route_tasks(
    tasks: Sequence[TaskExample],
    client: OpenAICompatibleClient,
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
) -> Dict[str, Mapping[str, object]]:
    cached = load_jsonl_by_task(out_path) if resume else {}
    missing = [task for task in tasks if task.task_id not in cached]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if resume else "w"
    api_calls = 0
    with out_path.open(mode, encoding="utf-8") as handle:
        for batch_idx, batch in enumerate(chunks(missing, batch_size), start=1):
            if not batch:
                continue
            payload = request_router_batch(batch, client)
            routes = payload.get("routes", [])
            parsed = parse_router_routes(batch, routes if isinstance(routes, list) else [])
            if len(parsed) < len(batch):
                for task in batch:
                    if task.task_id not in parsed:
                        single = request_router_batch([task], client).get("routes", [])
                        parsed.update(parse_router_routes([task], single if isinstance(single, list) else []))
                        api_calls += 1
            for task in batch:
                route = parsed.get(task.task_id)
                if route is None:
                    raise LLMClientError("LLM tool router omitted task %s" % task.task_id)
                row = {
                    "task_id": task.task_id,
                    "model": client.model,
                    "router": "llm_tool_router",
                    **route,
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                cached[task.task_id] = row
            handle.flush()
            api_calls += 1
            print("routed batch=%d size=%d cached=%d api_calls=%d" % (batch_idx, len(batch), len(cached), api_calls), file=sys.stderr)
            if sleep_seconds:
                time.sleep(sleep_seconds)
    return {task.task_id: cached[task.task_id] for task in tasks if task.task_id in cached}


def request_router_batch(tasks: Sequence[TaskExample], client: OpenAICompatibleClient) -> Mapping[str, object]:
    prompt = {
        "instruction": "Choose modules directly. Do not use obligation labels.",
        "registry": registry_prompt(),
        "tasks": [{"task_id": task.task_id, "query": task.query} for task in tasks],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=ROUTER_SYSTEM),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(1600, 450 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def parse_router_routes(tasks: Sequence[TaskExample], routes: Sequence[object]) -> Dict[str, Mapping[str, object]]:
    by_id = {task.task_id: task for task in tasks}
    registry = default_registry()
    parsed: Dict[str, Mapping[str, object]] = {}
    for item in routes:
        if not isinstance(item, Mapping):
            continue
        task_id = str(item.get("task_id", ""))
        if task_id not in by_id:
            continue
        status = str(item.get("expected_status", "supported"))
        if status not in {"supported", "unsupported", "clarify"}:
            status = "supported"
        modules = []
        for name in item.get("selected_modules", []) or []:
            module_name = str(name)
            if module_name in registry and module_name != "trace_recorder" and module_name not in modules:
                modules.append(module_name)
        parsed[task_id] = {
            "expected_status": status,
            "selected_modules": sorted(modules),
            "rationale": str(item.get("rationale", ""))[:1000],
        }
    return parsed


def evaluate_routes(
    tasks: Sequence[TaskExample],
    routes: Mapping[str, Mapping[str, object]],
    system_label: str,
) -> List[Dict[str, object]]:
    registry = default_registry()
    rows: List[Dict[str, object]] = []
    for task in tasks:
        route = routes[task.task_id]
        harness = harness_from_route(route)
        result = execute_task(task, system_label, "llm_tool_router", harness, registry)
        row = result.to_json()
        row["task"] = task.to_json()
        row["route"] = dict(route)
        row["metrics"] = row_metrics(task, result)
        row["metrics"].update(paper_metric_fields(row["metrics"]))
        rows.append(row)
    return rows


def harness_from_route(route: Mapping[str, object]) -> CompiledHarness:
    registry = default_registry()
    status = str(route.get("expected_status", "supported"))
    selected = tuple(sorted(str(name) for name in route.get("selected_modules", []) if str(name) in registry))
    if status == "clarify":
        return CompiledHarness(
            status="clarify",
            modules=(),
            obligations=frozen([]),
            capabilities=frozen([]),
            cost=0,
            loop_template="unsupported_or_clarify",
            reason="LLM tool router requested clarification.",
        )
    if status == "unsupported":
        return CompiledHarness(
            status="unsupported",
            modules=(),
            obligations=frozen([]),
            capabilities=frozen([]),
            cost=0,
            loop_template="unsupported_or_clarify",
            reason="LLM tool router marked unsupported.",
        )
    obligations = provided_obligations(selected, registry)
    capabilities = provided_capabilities(selected, registry)
    return CompiledHarness(
        status="supported",
        modules=selected,
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(selected, registry),
        loop_template="llm_tool_router_selected_modules" if selected else "direct_answer",
        reason="LLM tool router selected modules directly without obligation labels.",
    )


def run_secondary_audit(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = stratified_sample(load_benchmark(args.benchmark), args.sample_size, args.seed)
    manifest = {
        "benchmark": args.benchmark,
        "sample_size": len(tasks),
        "seed": args.seed,
        "audit_type": "secondary_adversarial_llm_audit_not_inter_annotator_agreement",
        "task_ids": [task.task_id for task in tasks],
    }
    (out_dir / "sample_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    client = OpenAICompatibleClient()
    audit_path = out_dir / "secondary_audit_labels.jsonl"
    audits = batch_audit_tasks(
        tasks,
        client,
        audit_path,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
    )
    report = render_secondary_audit_report(tasks, audits)
    (out_dir / "secondary_audit_report.md").write_text(report, encoding="utf-8")
    print("wrote secondary audit for", len(audits), "tasks to", audit_path)


def batch_audit_tasks(
    tasks: Sequence[TaskExample],
    client: OpenAICompatibleClient,
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
) -> Dict[str, Mapping[str, object]]:
    cached = load_jsonl_by_task(out_path) if resume else {}
    missing = [task for task in tasks if task.task_id not in cached]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if resume else "w"
    api_calls = 0
    with out_path.open(mode, encoding="utf-8") as handle:
        for batch_idx, batch in enumerate(chunks(missing, batch_size), start=1):
            payload = request_audit_batch(batch, client)
            audits = payload.get("audits", [])
            parsed = parse_audit_labels(batch, audits if isinstance(audits, list) else [])
            if len(parsed) < len(batch):
                for task in batch:
                    if task.task_id not in parsed:
                        single = request_audit_batch([task], client).get("audits", [])
                        parsed.update(parse_audit_labels([task], single if isinstance(single, list) else []))
                        api_calls += 1
            for task in batch:
                audit = parsed.get(task.task_id)
                if audit is None:
                    raise LLMClientError("Secondary audit omitted task %s" % task.task_id)
                row = {
                    "task_id": task.task_id,
                    "model": client.model,
                    "audit_type": "secondary_adversarial_llm_audit",
                    **audit,
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                cached[task.task_id] = row
            handle.flush()
            api_calls += 1
            print("audited batch=%d size=%d cached=%d api_calls=%d" % (batch_idx, len(batch), len(cached), api_calls), file=sys.stderr)
            if sleep_seconds:
                time.sleep(sleep_seconds)
    return {task.task_id: cached[task.task_id] for task in tasks if task.task_id in cached}


def request_audit_batch(tasks: Sequence[TaskExample], client: OpenAICompatibleClient) -> Mapping[str, object]:
    prompt = {
        "instruction": "Audit these tasks from scratch without seeing existing labels.",
        "registry": registry_prompt(),
        "tasks": [{"task_id": task.task_id, "query": task.query} for task in tasks],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=AUDIT_SYSTEM),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(2000, 650 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def parse_audit_labels(tasks: Sequence[TaskExample], audits: Sequence[object]) -> Dict[str, Mapping[str, object]]:
    by_id = {task.task_id: task for task in tasks}
    registry = default_registry()
    parsed: Dict[str, Mapping[str, object]] = {}
    for item in audits:
        if not isinstance(item, Mapping):
            continue
        task_id = str(item.get("task_id", ""))
        if task_id not in by_id:
            continue
        obligations = sorted({str(v) for v in item.get("obligations", []) or [] if str(v) in OBLIGATIONS})
        capabilities = sorted({str(v) for v in item.get("required_capabilities", []) or []})
        modules = sorted({str(v) for v in item.get("oracle_minimal_harness", []) or [] if str(v) in registry})
        status = str(item.get("expected_status", "supported"))
        if status not in {"supported", "unsupported", "clarify"}:
            status = "supported"
        parsed[task_id] = {
            "expected_status": status,
            "obligations": obligations,
            "required_capabilities": capabilities,
            "oracle_minimal_harness": modules,
            "rationale": str(item.get("rationale", ""))[:1000],
        }
    return parsed


def write_phase4_tables(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    PAPER_TABLE_DIR.mkdir(parents=True, exist_ok=True)

    table1 = render_table1_revised()
    table2 = render_table2_revised()
    table3 = render_table3_revised()
    table4 = render_table4_revised()
    table5 = render_boundary_diagnostics_table()
    table6 = render_llm_tool_router_table()
    audit_table = render_secondary_audit_table()
    sensitivity_table = render_cost_sensitivity_table()
    related_work = render_related_work_comparison_table()

    files = {
        "table1_gapbench1000_gold_revised.md": table1,
        "table2_phase2b_llm_heldout_revised.md": table2,
        "table3_phase2c_registry_guarded_revised.md": table3,
        "table4_phase2d_stress_tests_revised.md": table4,
        "table5_boundary_diagnostics_revised.md": table5,
        "table6_llm_tool_router_baseline.md": table6,
        "table7_secondary_audit.md": audit_table,
        "table8_cost_sensitivity.md": sensitivity_table,
        "related_work_comparison_table.md": related_work,
    }
    for name, text in files.items():
        (out_dir / name).write_text(text, encoding="utf-8")
        (PAPER_TABLE_DIR / name).write_text(text, encoding="utf-8")
    (out_dir / "phase4_table_index.md").write_text(render_phase4_table_index(files), encoding="utf-8")


def write_phase4_figures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)
    main_rows = load_results("outputs/final/results_gapbench1000_all_gold.jsonl")
    summary = summarize_results(main_rows)
    write_grouped_failure_svg(PAPER_FIG_DIR / "figure3_grouped_over_under_wrong.svg", summary)
    write_registry_guard_paper_svg(PAPER_FIG_DIR / "figure4_registry_guard_paper.svg")
    write_cost_success_svg(PAPER_FIG_DIR / "figure2_cost_success_frontier_revised.svg", summary)
    write_grouped_failure_svg(out_dir / "figure3_grouped_over_under_wrong.svg", summary)
    write_registry_guard_paper_svg(out_dir / "figure4_registry_guard_paper.svg")
    write_cost_success_svg(out_dir / "figure2_cost_success_frontier_revised.svg", summary)


def render_llm_tool_router_report(rows: Sequence[Mapping[str, object]], benchmark: str, subset: str) -> str:
    summary = summarize_results(rows)
    item = summary["llm_tool_router"]
    negative = category_summary(rows)
    lines = [
        "# LLM Tool Router Baseline",
        "",
        "Benchmark: `%s`" % benchmark,
        "",
        "Subset: `%s`" % subset,
        "",
        "This baseline gives the LLM the module registry and costs, but not the obligation ontology or gold labels.",
        "",
        "| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        paper_summary_line("llm_tool_router", item),
        "",
        "## Category Breakdown",
        "",
        "| Category | N | Harness Success | Avg Cost | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cat in sorted(negative):
        v = negative[cat]
        lines.append("| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f |" % (cat, v["n"], v["success"], v["cost"], v["over"], v["under"], v["wrong"]))
    lines.extend(["", "Harness success is obligation/capability coverage under the declared registry, not answer-level task correctness.", ""])
    return "\n".join(lines)


def render_secondary_audit_report(tasks: Sequence[TaskExample], audits: Mapping[str, Mapping[str, object]]) -> str:
    stats = secondary_audit_stats(tasks, audits)
    lines = [
        "# Secondary Adversarial Label Audit",
        "",
        "This is a secondary LLM audit over a stratified GapBench-100 sample. It is not inter-annotator agreement and should not be described as an independent human audit.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        "| N | %d |" % stats["n"],
        "| Obligation exact-set agreement | %.2f |" % stats["obligation_exact_agreement"],
        "| Obligation micro-F1 | %.3f |" % stats["obligation_micro_f1"],
        "| Capability micro-F1 | %.3f |" % stats["capability_micro_f1"],
        "| Expected-status agreement | %.2f |" % stats["status_agreement"],
        "| Oracle harness exact agreement | %.2f |" % stats["harness_exact_agreement"],
        "",
        "## Disagreement Samples",
        "",
        "| Task | Category | Gold obligations | Audit obligations | Gold caps | Audit caps |",
        "|---|---|---|---|---|---|",
    ]
    disagreements = []
    for task in tasks:
        audit = audits[task.task_id]
        if set(audit["obligations"]) != set(task.gold_obligations) or set(audit["required_capabilities"]) != set(task.required_capabilities):
            disagreements.append((task, audit))
    for task, audit in disagreements[:20]:
        lines.append(
            "| %s | %s | %s | %s | %s | %s |"
            % (
                task.task_id,
                task.category,
                ",".join(sorted(task.gold_obligations)) or "-",
                ",".join(audit["obligations"]) or "-",
                ",".join(sorted(task.required_capabilities)) or "-",
                ",".join(audit["required_capabilities"]) or "-",
            )
        )
    if not disagreements:
        lines.append("| - | none | - | - | - | - |")
    lines.append("")
    return "\n".join(lines)


def render_table1_revised() -> str:
    rows = load_results("outputs/final/results_gapbench1000_all_gold.jsonl")
    summary = summarize_results(rows)
    order = ["direct", "tool_router", "difficulty_router", "always_full", "gapharness", "oracle_minimal"]
    lines = [
        "# Table 1. GapBench-1000 Gold-Profile Compiler Result",
        "",
        "This table validates obligation-coverage compilation under gold profiles. Harness success is not answer-level semantic correctness.",
        "",
        "| System | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in order:
        if system in summary:
            lines.append(paper_summary_line(system, summary[system]))
    return "\n".join(lines) + "\n"


def render_table2_revised() -> str:
    rows = load_results("outputs/final/phase2b/results_test800_heldout_with_selected_llm.jsonl")
    summary = summarize_results(rows)
    order = ["direct", "tool_router", "difficulty_router", "always_full", "gold_oracle_gap_harness", "selected_llm_gap_harness"]
    lines = [
        "# Table 2. LLM-Inferred Profiles on GapBench Test800",
        "",
        "This table measures held-out harness-coverage success for inferred profiles. It does not claim the profiler is fully calibrated.",
        "",
        "| System | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in order:
        if system in summary:
            lines.append(paper_summary_line(system, summary[system]))
    return "\n".join(lines) + "\n"


def render_table3_revised() -> str:
    phase2b_dev = load_results("outputs/final/phase2b/results_dev200_llm_single.jsonl")
    phase2c_dev = load_results("outputs/final/phase2c/dev200_registry_guarded/results_dev200_llm_registry_guarded.jsonl")
    phase2b_test = load_results("outputs/final/phase2b/results_test800_selected_llm_single.jsonl")
    phase2c_test = load_results("outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl")
    items = [
        ("dev200", "LLM single", phase2b_dev, "gapharness"),
        ("dev200", "registry guard", phase2c_dev, "gapharness"),
        ("test800", "LLM single", phase2b_test, "selected_llm_gap_harness"),
        ("test800", "registry guard", phase2c_test, "phase2c_registry_guarded_gap_harness"),
    ]
    lines = [
        "# Table 3. Registry-Guarded Post-Hoc Calibration",
        "",
        "This is reported as post-hoc registry-boundary calibration after observing a systematic unsupported false-positive pattern.",
        "",
        "| Split | Profiler | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Over | Under | Wrong | Unsupported FP |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split, label, rows, system in items:
        summary = summarize_results(rows)[system]
        lines.append(paper_summary_line(label, summary, prefix=[split], unsupported_fp=unsupported_false_positive_count(rows)))
    return "\n".join(lines) + "\n"


def render_table4_revised() -> str:
    lines = [
        "# Table 4. Anti-Circularity Stress Tests and Negative Controls",
        "",
        "## Registry Perturbation",
        "",
        "| Perturbation | Removed Module | Base Harness Success | Perturbed Harness Success | Unsupported | Under-covered | Dominant Missing |",
        "|---|---|---:|---:|---:|---:|---|",
        "| remove_python_executor | python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |",
        "| remove_source_span_checker | source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |",
        "| remove_permission_gate | permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |",
        "| remove_sandbox_file_editor | sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |",
        "| remove_web_retrieval | web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |",
        "| remove_contract_verifier | contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |",
        "",
        "## Gold Label Permutation",
        "",
        "| Condition | N | Harness Success | Cost Delta | Over | Under | Wrong | Verifier Fail |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        "| correct gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |",
        "| permuted labels | 200 | 0.17 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |",
        "",
        "Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.",
        "",
        "## Negative Controls",
        "",
        "| Category | System | N | Harness Success | Avg Cost | Over |",
        "|---|---|---:|---:|---:|---:|",
    ]
    lines.extend(render_negative_control_table_rows())
    return "\n".join(lines) + "\n"


def render_negative_control_table_rows() -> List[str]:
    rows: List[Mapping[str, object]] = []
    old_path = Path("outputs/final/phase2d/negative_controls/results_negative_controls.jsonl")
    if old_path.exists():
        rows.extend(load_results(str(old_path)))
    router_path = PHASE4_DIR / "llm_tool_router_negative_controls/results_llm_tool_router.jsonl"
    if router_path.exists():
        rows.extend(load_results(str(router_path)))
    labels = {
        "direct": "Direct",
        "tool_router": "Tool Router",
        "always_full": "Always-full",
        "difficulty_router": "Difficulty Router",
        "gapharness_gold": "GapHarness gold",
        "gapharness_llm_single": "GapHarness LLM",
        "gapharness_registry_guarded": "Registry-guarded GapHarness",
        "llm_tool_router": "LLM Tool Router",
    }
    category_order = ["pure_language_negative", "tool_bait"]
    system_order = [
        "direct",
        "tool_router",
        "llm_tool_router",
        "difficulty_router",
        "always_full",
        "gapharness_gold",
        "gapharness_llm_single",
        "gapharness_registry_guarded",
    ]
    buckets: Dict[Tuple[str, str], List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[(str(row["task"]["category"]), str(row["system"]))].append(row)
    out: List[str] = []
    for category in category_order:
        for system in system_order:
            items = buckets.get((category, system))
            if not items:
                continue
            summary = summarize_results(items)[system]
            out.append(
                "| %s | %s | %.0f | %.2f | %.2f | %.2f |"
                % (
                    category,
                    labels.get(system, system),
                    summary["n"],
                    summary["success_rate"],
                    summary["avg_cost"],
                    summary["over_harness_rate"],
                )
            )
    return out


def render_boundary_diagnostics_table() -> str:
    rows = [
        ("GAIA-Transfer gold", "obligation-transfer smoke", 200, "1.00", "1.48", "0.00", "confirms compiler handles transfer labels; not GAIA solving"),
        ("GAIA guarded", "limitation diagnostic", 200, "0.56", "5.56", "4.08", "shows multimodal/file/evidence/state transfer gap"),
        ("GapBench-Natural", "human-audited naturalization", 200, "1.00", "2.83", "0.00", "human-audited naturalized GapBench prompts; still GapBench-derived"),
        ("SWE-Obligation-50", "real-source obligation transfer", 50, "1.00", "12.00", "0.00", "derived from SWE-bench Lite issue text; not patch solving or pass@1"),
        ("SWE-Obligation-50 LLM-safe", "LLM diagnostic view", 50, "1.00", "12.80", "0.80", "shortened real-source view for LLM profiler API; not replacement for gold source"),
        ("Terminal obligation50", "appendix scaffold", 50, "-", "-", "-", "labels pending audit; not Terminal-Bench solving"),
    ]
    lines = [
        "# Table 5. Boundary Diagnostics on Transfer Artifacts",
        "",
        "Transfer artifacts are boundary diagnostics, not primary performance evidence.",
        "",
        "| Artifact | Identity | N | Harness Success | Cost | Cost Delta | Boundary |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % row)
    return "\n".join(lines) + "\n"


def render_llm_tool_router_table() -> str:
    dev_path = PHASE4_DIR / "llm_tool_router_dev200/results_llm_tool_router.jsonl"
    path = PHASE4_DIR / "llm_tool_router_test800/results_llm_tool_router.jsonl"
    neg_path = PHASE4_DIR / "llm_tool_router_negative_controls/results_llm_tool_router.jsonl"
    swe_path = PHASE4_DIR / "llm_tool_router_swe_obligation50/results_llm_tool_router.jsonl"
    lines = [
        "# Table 6. LLM Tool Router Baseline",
        "",
        "The LLM Tool Router sees registry modules and costs, but not obligation labels or gold labels.",
        "",
        "| System/Subsample | N | Harness Success | Cost | Oracle | Cost Delta | Excess Cost | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    if dev_path.exists():
        summary = summarize_results(load_results(str(dev_path)))["llm_tool_router"]
        lines.append(paper_summary_line("llm_tool_router dev200", summary))
    if path.exists():
        summary = summarize_results(load_results(str(path)))["llm_tool_router"]
        lines.append(paper_summary_line("llm_tool_router test800", summary))
    else:
        lines.append("| llm_tool_router test800 | - | - | - | - | - | - | - | - | - |")
    if neg_path.exists():
        rows = load_results(str(neg_path))
        for category, item in category_summary(rows).items():
            pseudo = {
                "n": item["n"],
                "success_rate": item["success"],
                "avg_cost": item["cost"],
                "avg_oracle_cost": 0.0,
                "avg_minimality_regret": item["cost"],
                "over_harness_rate": item["over"],
                "under_harness_rate": item["under"],
                "wrong_harness_rate": item["wrong"],
            }
            lines.append(paper_summary_line("router " + category, pseudo))
    if swe_path.exists():
        summary = summarize_results(load_results(str(swe_path)))["llm_tool_router"]
        lines.append(paper_summary_line("llm_tool_router SWE-Obligation-50", summary))
    return "\n".join(lines) + "\n"


def render_secondary_audit_table() -> str:
    report_path = PHASE4_DIR / "secondary_audit_gapbench100/secondary_audit_labels.jsonl"
    sample_path = PHASE4_DIR / "secondary_audit_gapbench100/sample_manifest.json"
    if not report_path.exists() or not sample_path.exists():
        return "# Table 7. Secondary Audit\n\nSecondary audit not yet run.\n"
    manifest = json.loads(sample_path.read_text(encoding="utf-8"))
    task_ids = set(manifest["task_ids"])
    tasks = [task for task in load_benchmark(manifest["benchmark"]) if task.task_id in task_ids]
    audits = load_jsonl_by_task(report_path)
    stats = secondary_audit_stats(tasks, audits)
    return "\n".join(
        [
            "# Table 7. Secondary Adversarial Audit on GapBench-100",
            "",
            "This is an LLM secondary audit, not inter-annotator agreement.",
            "",
            "| N | Obl Exact | Obl Micro-F1 | Cap Micro-F1 | Status Agree | Harness Exact |",
            "|---:|---:|---:|---:|---:|---:|",
            "| %d | %.2f | %.3f | %.3f | %.2f | %.2f |"
            % (
                stats["n"],
                stats["obligation_exact_agreement"],
                stats["obligation_micro_f1"],
                stats["capability_micro_f1"],
                stats["status_agreement"],
                stats["harness_exact_agreement"],
            ),
            "",
        ]
    )


def render_cost_sensitivity_table() -> str:
    rows = load_results("outputs/final/results_gapbench1000_all_gold.jsonl")
    # Sensitivity is deterministic and relative: report baseline success/cost under
    # current costs plus two analytical variants from existing selected modules.
    variants = {
        "default": {},
        "execution_x2": {"python_executor": 2.0, "execution_log_checker": 2.0},
        "verification_x2": {"source_span_checker": 2.0, "execution_log_checker": 2.0, "contract_verifier": 2.0},
    }
    registry = default_registry()
    lines = [
        "# Table 8. Cost-Model Sensitivity",
        "",
        "Costs are recomputed analytically on existing selected modules; no new experiment is run.",
        "",
        "| Variant | System | N | Harness Success | Recomputed Cost | Oracle Cost | Cost Delta |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for variant, multipliers in variants.items():
        buckets: Dict[str, List[Tuple[float, float, bool]]] = defaultdict(list)
        for row in rows:
            system = str(row["system"])
            modules = row.get("harness", {}).get("modules", [])
            task_modules = row.get("task", {}).get("oracle_minimal_harness", [])
            cost = recomputed_cost(modules, registry, multipliers)
            oracle = recomputed_cost(task_modules, registry, multipliers)
            buckets[system].append((cost, oracle, bool(row["metrics"]["success"])))
        for system in ["direct", "tool_router", "difficulty_router", "always_full", "gapharness"]:
            if system not in buckets:
                continue
            vals = buckets[system]
            n = len(vals)
            cost = sum(v[0] for v in vals) / n
            oracle = sum(v[1] for v in vals) / n
            success = sum(1 for v in vals if v[2]) / n
            lines.append("| %s | %s | %d | %.2f | %.2f | %.2f | %.2f |" % (variant, system, n, success, cost, oracle, cost - oracle))
    return "\n".join(lines) + "\n"


def render_related_work_comparison_table() -> str:
    lines = [
        "# Related Work Comparison Table",
        "",
        "| Work | Primary object | Obligation-level? | Registry-relative minimality? | Query-conditioned? | Verifier/stress tests? | Difference from GapHarness |",
        "|---|---|---|---|---|---|---|",
        "| ReAct / Toolformer | tool-using LM behavior | no | no | yes | task eval | GapHarness compiles declared harnesses from obligations. |",
        "| Gorilla / ToolLLM | API selection/calling | no | no | yes | API benchmarks | GapHarness separates obligation inference from module selection. |",
        "| MetaTool | tool necessity | partial/tool-level | no | yes | tool-choice eval | GapHarness adds registry-relative minimal compilation and stress tests. |",
        "| AutoFlow / AFlow / WorFBench | agentic workflow generation | no | no; workflow optimization | yes | workflow benchmarks | GapHarness targets minimal runtime coverage, not workflow synthesis. |",
        "| AutoHarness / NL Agent Harnesses | harness synthesis/specification | partial | not over finite obligation registry | yes | system eval | GapHarness formalizes obligation/capability coverage over a finite registry. |",
        "| Harness-Bench | harness effects benchmark | no | no | mixed | benchmarked effects | GapHarness provides a compiler and anti-circularity tests for declared harness synthesis. |",
    ]
    return "\n".join(lines) + "\n"


def paper_metric_fields(metrics: Mapping[str, object]) -> Dict[str, object]:
    cost_delta = float(metrics["predicted_cost"]) - float(metrics["oracle_cost"])
    success = bool(metrics["success"])
    return {
        "harness_success": success,
        "cost_delta": cost_delta,
        "excess_cost": max(0.0, cost_delta),
        "sufficient_cost_delta": cost_delta if success else None,
    }


def paper_summary_line(
    system: str,
    item: Mapping[str, float],
    prefix: Optional[Sequence[str]] = None,
    unsupported_fp: Optional[int] = None,
) -> str:
    cells: List[str] = list(prefix or []) + [
        system,
        "%.0f" % item["n"],
        "%.2f" % item["success_rate"],
        "%.2f" % item["avg_cost"],
        "%.2f" % item["avg_oracle_cost"],
        "%.2f" % item.get("avg_cost_delta", item["avg_minimality_regret"]),
        "%.2f" % item.get("avg_excess_cost", max(0.0, item["avg_minimality_regret"])),
        "%.2f" % item["over_harness_rate"],
        "%.2f" % item["under_harness_rate"],
        "%.2f" % item["wrong_harness_rate"],
    ]
    if unsupported_fp is not None:
        cells.append(str(unsupported_fp))
    return "| " + " | ".join(cells) + " |"


def unsupported_false_positive_count(rows: Sequence[Mapping[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("task", {}).get("expected_status") == "supported"
        and row.get("harness", {}).get("status") == "unsupported"
    )


def category_summary(rows: Sequence[Mapping[str, object]]) -> Dict[str, Dict[str, float]]:
    buckets: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["task"]["category"])].append(row)
    out = {}
    for category, items in buckets.items():
        n = len(items)
        out[category] = {
            "n": n,
            "success": mean(row["metrics"]["success"] for row in items),
            "cost": mean(row["metrics"]["predicted_cost"] for row in items),
            "over": mean(row["metrics"]["over_harness"] for row in items),
            "under": mean(row["metrics"]["under_harness"] for row in items),
            "wrong": mean(row["metrics"]["wrong_harness"] for row in items),
        }
    return out


def secondary_audit_stats(tasks: Sequence[TaskExample], audits: Mapping[str, Mapping[str, object]]) -> Dict[str, float]:
    exact = status = harness_exact = 0
    obl_tp = obl_fp = obl_fn = 0
    cap_tp = cap_fp = cap_fn = 0
    for task in tasks:
        audit = audits[task.task_id]
        gold_obs = set(task.gold_obligations)
        pred_obs = set(audit["obligations"])
        gold_caps = set(task.required_capabilities)
        pred_caps = set(audit["required_capabilities"])
        if gold_obs == pred_obs:
            exact += 1
        if task.expected_status == audit["expected_status"]:
            status += 1
        if set(task.oracle_minimal_harness) == set(audit["oracle_minimal_harness"]):
            harness_exact += 1
        obl_tp += len(gold_obs & pred_obs)
        obl_fp += len(pred_obs - gold_obs)
        obl_fn += len(gold_obs - pred_obs)
        cap_tp += len(gold_caps & pred_caps)
        cap_fp += len(pred_caps - gold_caps)
        cap_fn += len(gold_caps - pred_caps)
    n = len(tasks)
    return {
        "n": n,
        "obligation_exact_agreement": exact / n if n else 0.0,
        "status_agreement": status / n if n else 0.0,
        "harness_exact_agreement": harness_exact / n if n else 0.0,
        "obligation_micro_f1": f1(obl_tp, obl_fp, obl_fn),
        "capability_micro_f1": f1(cap_tp, cap_fp, cap_fn),
    }


def f1(tp: int, fp: int, fn: int) -> float:
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def stratified_sample(tasks: Sequence[TaskExample], sample_size: int, seed: int) -> List[TaskExample]:
    rng = random.Random(seed)
    by_category: Dict[str, List[TaskExample]] = defaultdict(list)
    for task in tasks:
        by_category[task.category].append(task)
    selected: List[TaskExample] = []
    categories = sorted(by_category)
    base = sample_size // len(categories)
    remainder = sample_size % len(categories)
    for i, category in enumerate(categories):
        items = list(by_category[category])
        rng.shuffle(items)
        k = min(len(items), base + (1 if i < remainder else 0))
        selected.extend(items[:k])
    if len(selected) < sample_size:
        remaining = [task for task in tasks if task not in selected]
        rng.shuffle(remaining)
        selected.extend(remaining[: sample_size - len(selected)])
    selected.sort(key=lambda task: task.task_id)
    return selected[:sample_size]


def registry_prompt() -> List[Mapping[str, object]]:
    registry = default_registry()
    return [
        {
            "name": module.name,
            "capabilities": sorted(module.capabilities),
            "cost": module.cost,
            "requires_capabilities": sorted(module.requires_capabilities),
            "description": module_description(module.name),
        }
        for module in registry.values()
        if module.name != "trace_recorder"
    ]


def module_description(name: str) -> str:
    return {
        "web_retrieval": "Retrieve public web evidence for current or external information.",
        "source_span_checker": "Check source spans when web evidence is used.",
        "python_executor": "Run deterministic computation, parsing, scripts, tests, or simulations.",
        "execution_log_checker": "Check execution logs when code execution is used.",
        "file_state_reader": "Inspect local workspace files or durable workspace state.",
        "state_store": "Maintain durable intermediate task state.",
        "sandbox_file_editor": "Apply sandbox-local file edits and produce diffs.",
        "permission_gate": "Gate risky, permissioned, or sandbox action steps.",
        "contract_verifier": "Check output contracts, schemas, exactness, or required format.",
    }.get(name, name)


def load_jsonl_by_task(path: Path) -> Dict[str, Mapping[str, object]]:
    if not path.exists():
        return {}
    rows: Dict[str, Mapping[str, object]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[str(row["task_id"])] = row
    return rows


def chunks(items: Sequence[TaskExample], size: int) -> Iterable[Sequence[TaskExample]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def mean(values: Iterable[object]) -> float:
    vals = [float(v) for v in values]
    return sum(vals) / len(vals) if vals else 0.0


def recomputed_cost(modules: Sequence[str], registry: Mapping[str, object], multipliers: Mapping[str, float]) -> float:
    value = 0.0
    for name in modules:
        if name not in registry:
            continue
        value += registry[name].cost * multipliers.get(name, 1.0)
    return value


def write_grouped_failure_svg(path: Path, summary: Mapping[str, Mapping[str, float]]) -> None:
    systems = ["direct", "tool_router", "difficulty_router", "always_full", "gapharness"]
    labels = {
        "direct": "Direct",
        "tool_router": "Tool",
        "difficulty_router": "Difficulty",
        "always_full": "Always-full",
        "gapharness": "GapHarness",
    }
    series = [("Over", "over_harness_rate", "#ef4444"), ("Under", "under_harness_rate", "#f59e0b"), ("Wrong", "wrong_harness_rate", "#3b82f6")]
    w, h = 900, 470
    ml, mr, mt, mb = 70, 115, 45, 80
    plot_w, plot_h = w - ml - mr, h - mt - mb
    parts = [svg_header(w, h)]
    parts.append(line(ml, mt, ml, mt + plot_h, "#334155"))
    parts.append(line(ml, mt + plot_h, ml + plot_w, mt + plot_h, "#334155"))
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = mt + plot_h - tick * plot_h
        parts.append(line(ml - 5, y, ml, y, "#334155"))
        parts.append(text(ml - 10, y + 4, "%.2f" % tick, 11, "end"))
        parts.append(line(ml, y, ml + plot_w, y, "#e5e7eb"))
    group_w = plot_w / len(systems)
    bar_w = 18
    for i, system in enumerate(systems):
        cx = ml + i * group_w + group_w / 2
        for j, (_, key, color) in enumerate(series):
            v = float(summary[system][key])
            bh = v * plot_h
            x = cx + (j - 1) * (bar_w + 4) - bar_w / 2
            y = mt + plot_h - bh
            parts.append(rect(x, y, bar_w, bh, color, color, rx=1))
        parts.append(text(cx, h - 36, labels[system], 11))
    parts.append(text(w / 2, h - 8, "System", 12))
    parts.append(text(20, h / 2, "Rate (not mutually exclusive)", 12, rotate=-90))
    parts.append(legend(w - 220, 30, [(name, color) for name, _, color in series]))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_registry_guard_paper_svg(path: Path) -> None:
    values = [
        ("Unsupported FP", 56, 12, "#7c3aed"),
        ("Under", 0.09, 0.03, "#f59e0b"),
        ("Harness success", 0.89, 0.94, "#16a34a"),
    ]
    w, h = 780, 430
    ml, mr, mt, mb = 80, 45, 45, 70
    plot_w, plot_h = w - ml - mr, h - mt - mb
    parts = [svg_header(w, h)]
    parts.append(text(w / 2, 26, "Registry-guarded calibration on GapBench test800", 16))
    parts.append(line(ml, mt, ml, mt + plot_h, "#334155"))
    parts.append(line(ml, mt + plot_h, ml + plot_w, mt + plot_h, "#334155"))
    max_v = 56.0
    group_w = plot_w / len(values)
    bar_w = 38
    for i, (label, before, after, color) in enumerate(values):
        cx = ml + i * group_w + group_w / 2
        for j, (name, val, shade) in enumerate([("2B", before, color), ("2C", after, "#0f766e" if label == "Unsupported FP" else color)]):
            scaled = val if label == "Unsupported FP" else val * 56
            bh = scaled / max_v * plot_h
            x = cx + (j - 0.5) * (bar_w + 10) - bar_w / 2
            y = mt + plot_h - bh
            parts.append(rect(x, y, bar_w, bh, shade, shade, rx=2))
            parts.append(text(x + bar_w / 2, y - 6, "%.2f" % val if val < 1 else "%.0f" % val, 11))
            parts.append(text(x + bar_w / 2, mt + plot_h + 18, name, 10))
        parts.append(text(cx, h - 20, label, 11))
    parts.append(text(25, h / 2, "Count for FP; rates scaled to same axis", 11, rotate=-90))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_cost_success_svg(path: Path, summary: Mapping[str, Mapping[str, float]]) -> None:
    systems = ["direct", "tool_router", "difficulty_router", "always_full", "gapharness", "oracle_minimal"]
    labels = {
        "direct": "Direct",
        "tool_router": "Tool Router",
        "difficulty_router": "Difficulty",
        "always_full": "Always-full",
        "gapharness": "GapHarness",
        "oracle_minimal": "Oracle",
    }
    colors = {
        "direct": "#64748b",
        "tool_router": "#3b82f6",
        "difficulty_router": "#8b5cf6",
        "always_full": "#ef4444",
        "gapharness": "#16a34a",
        "oracle_minimal": "#0f766e",
    }
    w, h = 760, 470
    ml, mr, mt, mb = 70, 170, 45, 65
    plot_w, plot_h = w - ml - mr, h - mt - mb
    max_cost = 16.0
    parts = [svg_header(w, h)]
    parts.append(line(ml, mt, ml, mt + plot_h, "#334155"))
    parts.append(line(ml, mt + plot_h, ml + plot_w, mt + plot_h, "#334155"))
    for tick in [0, 4, 8, 12, 16]:
        x = ml + tick / max_cost * plot_w
        parts.append(line(x, mt + plot_h, x, mt + plot_h + 5, "#334155"))
        parts.append(text(x, mt + plot_h + 22, str(tick), 11))
    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = mt + plot_h - tick * plot_h
        parts.append(line(ml - 5, y, ml, y, "#334155"))
        parts.append(text(ml - 10, y + 4, "%.2f" % tick, 11, "end"))
        parts.append(line(ml, y, ml + plot_w, y, "#e5e7eb"))
    offsets = {
        "gapharness": (10, -14),
        "oracle_minimal": (10, 16),
        "always_full": (-72, -12),
    }
    for system in systems:
        item = summary[system]
        x = ml + float(item["avg_cost"]) / max_cost * plot_w
        y = mt + plot_h - float(item["success_rate"]) * plot_h
        parts.append(circle(x, y, 5, colors[system]))
        dx, dy = offsets.get(system, (8, -8))
        parts.append(text(x + dx, y + dy, labels[system], 11, "start" if dx >= 0 else "end"))
    parts.append(text(ml + plot_w / 2, h - 12, "Average cost", 12))
    parts.append(text(20, mt + plot_h / 2, "Harness success", 12, rotate=-90))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def svg_header(width: int, height: int) -> str:
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\\n<rect width="100%%" height="100%%" fill="white"/>\\n' % (width, height, width, height)


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str, rx: int = 4) -> str:
    return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%d" fill="%s" stroke="%s"/>\\n' % (x, y, w, max(h, 0.0), rx, fill, stroke)


def line(x1: float, y1: float, x2: float, y2: float, color: str = "#334155") -> str:
    return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="1.2"/>\\n' % (x1, y1, x2, y2, color)


def circle(x: float, y: float, r: float, fill: str) -> str:
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/>\\n' % (x, y, r, fill)


def text(x: float, y: float, value: str, size: int, anchor: str = "middle", rotate: Optional[int] = None) -> str:
    transform = ' transform="rotate(%d %.2f %.2f)"' % (rotate, x, y) if rotate is not None else ""
    return '<text x="%.2f" y="%.2f" font-family="Arial, sans-serif" font-size="%d" text-anchor="%s"%s>%s</text>\\n' % (x, y, size, anchor, transform, escape_xml(value))


def legend(x: float, y: float, items: Sequence[Tuple[str, str]]) -> str:
    parts = []
    for idx, (label, color) in enumerate(items):
        yy = y + idx * 20
        parts.append(rect(x, yy, 11, 11, color, color, rx=1))
        parts.append(text(x + 18, yy + 10, label, 11, "start"))
    return "".join(parts)


def escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_phase4_table_index(files: Mapping[str, str]) -> str:
    lines = ["# Reviewer-Hardening Table Index", ""]
    for name in files:
        lines.append("- `%s`" % name)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
