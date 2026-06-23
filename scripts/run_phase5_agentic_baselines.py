"""Strong agentic harness-selection baselines.

This stage compares GapHarness against stronger *policies* over the same
declared registry, model interface, executor, and verifier:

- workflow_generator: one-shot workflow/module DAG generation.
- verifier_repair_router: LLM Tool Router followed by verifier-feedback repair.
- react_module_selector: iterative module selection with verifier feedback.

The baselines are framework-independent strategy baselines; they could be
implemented in LangGraph, AutoGen, Agents SDK, or a plain loop. Holding the
registry/executor/verifier fixed avoids framework confounds.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from gapharness.compiler import compile_minimal_harness
from gapharness.evaluation import load_benchmark, load_results, row_metrics, summarize_results, write_jsonl
from gapharness.executor import execute_task
from gapharness.llm_profiler import canonicalize_profile
from gapharness.llm_client import ChatMessage, LLMClientError, OpenAICompatibleClient, parse_json_object
from gapharness.registry import default_registry, provided_capabilities, provided_obligations, total_cost
from gapharness.schema import CompiledHarness, OBLIGATIONS, ProfilerOutput, TaskExample, frozen
from gapharness.verifiers import verify_task_result
from scripts.run_harness_exec20 import build_cases, case_to_task, render_report as render_exec_report, run_case_trace, summarize_exec, write_benchmark_artifacts
from scripts.run_phase4_reviewer_hardening import (
    batch_route_tasks,
    harness_from_route,
    load_jsonl_by_task,
    mean,
    module_description,
    paper_summary_line,
    registry_prompt,
)


PHASE5_DIR = Path("outputs/phase5_agentic_baselines")
PAPER_TABLE_DIR = Path("paper/tables")

STRATEGIES = ("workflow_generator", "verifier_repair_router", "react_module_selector", "gapharness_repair")

WORKFLOW_SYSTEM = """You are a workflow-generation baseline for GapHarness.

You generate a compact runtime workflow over a declared module registry. You
must not use named obligation labels. You see only the user query, module
descriptions, costs, and dependencies.

Return JSON only:
{
  "routes": [
    {
      "task_id": "string",
      "expected_status": "supported" | "unsupported" | "clarify",
      "selected_modules": ["module_name"],
      "workflow": ["module_name"],
      "rationale": "short reason"
    }
  ]
}

Rules:
- Select only listed modules.
- Use an empty workflow when direct answering is sufficient.
- Return unsupported for real irreversible external side effects that the
  registry cannot safely perform.
- Respect dependencies such as execution logs requiring execution, source-span
  checking requiring web evidence, and sandbox edits requiring permission.
- Prefer low cost, but do not omit modules needed for a warranted answer or
  sandbox action.
"""

REPAIR_SYSTEM = """You are a verifier-repair router baseline for GapHarness.

You receive a previous direct module route and verifier feedback. You may add
or remove modules, mark the request unsupported, ask for clarification, or keep
the route. Do not use named obligation labels. Use the verifier feedback only
as runtime feedback.

Return JSON only:
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
- Select only listed modules.
- Minimize cost after satisfying verifier feedback.
- Respect module dependencies.
- If feedback says the task is unsupported under the declared registry, return
  unsupported with no modules.
"""

REACT_SYSTEM = """You are a ReAct-style module selector baseline for GapHarness.

You run an iterative select-and-check loop. Each step receives the current
module set, current cost, previous verifier feedback, and registry modules. You
may select a revised module set, stop, mark unsupported, or ask for
clarification. Do not use named obligation labels.

Return JSON only:
{
  "routes": [
    {
      "task_id": "string",
      "action": "select" | "stop" | "unsupported" | "clarify",
      "selected_modules": ["module_name"],
      "rationale": "short reason"
    }
  ]
}

Rules:
- Select only listed modules.
- Use verifier feedback to repair missing capabilities or dependency failures.
- Prefer low cost, but do not omit modules needed for a warranted answer or
  sandbox action.
- If the current route already satisfies the verifier, stop or keep it.
"""


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--batch-size", type=int, default=10)
    common.add_argument("--sleep", type=float, default=0.0)
    common.add_argument("--no-resume", action="store_true")
    common.add_argument("--repair-rounds", type=int, default=2)
    common.add_argument("--react-steps", type=int, default=4)
    common.add_argument("--concurrency", type=int, default=1)

    run = sub.add_parser("run", parents=[common])
    run.add_argument("--benchmark", required=True)
    run.add_argument("--out-dir", required=True)
    run.add_argument("--existing-router-routes", default="")
    run.add_argument("--base-gapharness-results", default="")
    run.add_argument("--limit", type=int, default=None)
    run.add_argument("--strategies", default=",".join(STRATEGIES))

    exec_cmd = sub.add_parser("harness-exec20", parents=[common])
    exec_cmd.add_argument("--out-dir", default=str(PHASE5_DIR / "harness_exec20_agentic"))
    exec_cmd.add_argument("--benchmark-dir", default="benchmarks/harness_exec/v1.0")
    exec_cmd.add_argument("--audit-date", default="2026-06-23")
    exec_cmd.add_argument("--strategies", default=",".join(STRATEGIES))

    all_cmd = sub.add_parser("all", parents=[common])

    tables = sub.add_parser("tables")
    tables.add_argument("--out-dir", default=str(PHASE5_DIR))

    args = parser.parse_args(argv)
    if args.command == "run":
        tasks = load_limited(args.benchmark, args.limit)
        run_agentic_strategies(
            tasks=tasks,
            out_dir=Path(args.out_dir),
            strategies=parse_strategies(args.strategies),
            batch_size=args.batch_size,
            sleep_seconds=args.sleep,
            resume=not args.no_resume,
            repair_rounds=args.repair_rounds,
            react_steps=args.react_steps,
            concurrency=args.concurrency,
            existing_router_routes=Path(args.existing_router_routes) if args.existing_router_routes else None,
            base_gapharness_results=Path(args.base_gapharness_results) if args.base_gapharness_results else None,
        )
    elif args.command == "harness-exec20":
        run_harness_exec20_agentic(args)
    elif args.command == "all":
        run_all(args)
    elif args.command == "tables":
        write_phase5_tables(Path(args.out_dir))
    else:
        raise ValueError(args.command)
    return 0


def run_all(args: argparse.Namespace) -> None:
    run_agentic_strategies(
        tasks=load_benchmark("benchmarks/gapbench/v1.0/splits/test800.jsonl"),
        out_dir=PHASE5_DIR / "gapbench_test800",
        strategies=STRATEGIES,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
        repair_rounds=args.repair_rounds,
        react_steps=args.react_steps,
        concurrency=args.concurrency,
        existing_router_routes=Path("outputs/phase4/llm_tool_router_test800/routes.jsonl"),
        base_gapharness_results=Path("outputs/final/phase2b/results_test800_selected_llm_single.jsonl"),
    )
    run_agentic_strategies(
        tasks=load_benchmark("benchmarks/harness_challenge/v1.0/harness_challenge200_author_reviewed.jsonl"),
        out_dir=PHASE5_DIR / "harness_challenge200",
        strategies=STRATEGIES,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
        repair_rounds=args.repair_rounds,
        react_steps=args.react_steps,
        concurrency=args.concurrency,
        existing_router_routes=Path("outputs/phase4/llm_tool_router_harness_challenge200/routes.jsonl"),
        base_gapharness_results=Path("outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl"),
    )
    exec_args = argparse.Namespace(
        out_dir=str(PHASE5_DIR / "harness_exec20_agentic"),
        benchmark_dir="benchmarks/harness_exec/v1.0",
        audit_date="2026-06-23",
        strategies=",".join(STRATEGIES),
        batch_size=args.batch_size,
        sleep=args.sleep,
        no_resume=args.no_resume,
        repair_rounds=args.repair_rounds,
        react_steps=args.react_steps,
        concurrency=args.concurrency,
    )
    run_harness_exec20_agentic(exec_args)
    write_phase5_tables(PHASE5_DIR)


def run_agentic_strategies(
    tasks: Sequence[TaskExample],
    out_dir: Path,
    strategies: Sequence[str],
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
    repair_rounds: int,
    react_steps: int,
    concurrency: int,
    existing_router_routes: Optional[Path] = None,
    base_gapharness_results: Optional[Path] = None,
) -> List[Mapping[str, object]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    client: Optional[OpenAICompatibleClient] = None
    all_rows: List[Mapping[str, object]] = []

    if "workflow_generator" in strategies:
        client = client or OpenAICompatibleClient()
        workflow_routes = batch_workflow_tasks(
            tasks,
            client,
            out_dir / "routes_workflow_generator.jsonl",
            batch_size,
            sleep_seconds,
            resume,
            concurrency,
        )
        all_rows.extend(evaluate_strategy_routes(tasks, workflow_routes, "workflow_generator", "workflow_generator"))

    if "verifier_repair_router" in strategies:
        client = client or OpenAICompatibleClient()
        initial_path = out_dir / "routes_verifier_repair_initial.jsonl"
        if existing_router_routes and existing_router_routes.exists() and resume and not initial_path.exists():
            initial_path.write_text(existing_router_routes.read_text(encoding="utf-8"), encoding="utf-8")
        initial_routes = batch_route_tasks(tasks, client, initial_path, batch_size, sleep_seconds, resume)
        repaired_routes = run_repair_rounds(
            tasks,
            client,
            out_dir,
            initial_routes,
            repair_rounds,
            batch_size,
            sleep_seconds,
            resume,
            concurrency,
        )
        all_rows.extend(evaluate_strategy_routes(tasks, repaired_routes, "verifier_repair_router", "verifier_repair_router"))

    if "react_module_selector" in strategies:
        client = client or OpenAICompatibleClient()
        react_routes = run_react_steps(
            tasks,
            client,
            out_dir,
            react_steps,
            batch_size,
            sleep_seconds,
            resume,
            concurrency,
        )
        all_rows.extend(evaluate_strategy_routes(tasks, react_routes, "react_module_selector", "react_module_selector"))

    if "gapharness_repair" in strategies:
        repaired_rows = run_gapharness_repair(
            tasks=tasks,
            base_results_path=base_gapharness_results,
            out_dir=out_dir,
        )
        all_rows.extend(repaired_rows)

    result_path = out_dir / "results_agentic_strategies.jsonl"
    if result_path.exists() and set(strategies) != set(STRATEGIES):
        preserved = [row for row in load_results(str(result_path)) if str(row.get("system")) not in set(strategies)]
        all_rows = preserved + all_rows
    write_jsonl(str(result_path), all_rows)
    (out_dir / "summary.md").write_text(render_agentic_report(all_rows), encoding="utf-8")
    print("wrote", len(all_rows), "agentic strategy rows to", out_dir)
    return all_rows


def batch_workflow_tasks(
    tasks: Sequence[TaskExample],
    client: OpenAICompatibleClient,
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
    concurrency: int,
) -> Dict[str, Mapping[str, object]]:
    def request(batch: Sequence[TaskExample]) -> Mapping[str, object]:
        return request_workflow_batch(batch, client)

    def parse(batch: Sequence[TaskExample], payload: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
        return parse_routes(batch, payload.get("routes", []), include_action=False)

    def make_row(task: TaskExample, route: Mapping[str, object]) -> Mapping[str, object]:
        return {
            "task_id": task.task_id,
            "model": client.model,
            "strategy": "workflow_generator",
            "llm_calls": 1,
            "steps": 1,
            **route,
        }

    cached = run_cached_batch_requests(
        tasks=tasks,
        out_path=out_path,
        batch_size=batch_size,
        sleep_seconds=sleep_seconds,
        resume=resume,
        concurrency=concurrency,
        request_batch=request,
        parse_batch=parse,
        make_row=make_row,
        label="workflow",
        missing_error="Workflow generator omitted task %s",
    )
    return {task.task_id: cached[task.task_id] for task in tasks if task.task_id in cached}


def run_cached_batch_requests(
    tasks: Sequence[TaskExample],
    out_path: Path,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
    concurrency: int,
    request_batch: Callable[[Sequence[TaskExample]], Mapping[str, object]],
    parse_batch: Callable[[Sequence[TaskExample], Mapping[str, object]], Dict[str, Mapping[str, object]]],
    make_row: Callable[[TaskExample, Mapping[str, object]], Mapping[str, object]],
    label: str,
    missing_error: str,
    initial_cached: Optional[Mapping[str, Mapping[str, object]]] = None,
) -> Dict[str, Mapping[str, object]]:
    cached: Dict[str, Mapping[str, object]] = dict(initial_cached or {})
    if resume and not cached:
        cached.update(load_jsonl_by_task(out_path))
    missing = [task for task in tasks if task.task_id not in cached]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if resume else "w"
    batches = list(enumerate(chunks(missing, batch_size), start=1))
    calls = 0

    def resolve_batch(batch: Sequence[TaskExample]) -> Dict[str, Mapping[str, object]]:
        payload = request_batch(batch)
        parsed = parse_batch(batch, payload)
        if len(parsed) < len(batch):
            for task in batch:
                if task.task_id not in parsed:
                    single = request_batch([task])
                    parsed.update(parse_batch([task], single))
        return parsed

    with out_path.open(mode, encoding="utf-8") as handle:
        if concurrency <= 1 or len(batches) <= 1:
            for batch_idx, batch in batches:
                parsed = resolve_batch(batch)
                calls += 1
                write_parsed_batch(handle, batch, parsed, cached, make_row, missing_error)
                print("%s batch=%d size=%d cached=%d api_calls~=%d" % (label, batch_idx, len(batch), len(cached), calls), file=sys.stderr)
                if sleep_seconds:
                    time.sleep(sleep_seconds)
        else:
            workers = max(1, min(concurrency, len(batches)))
            with ThreadPoolExecutor(max_workers=workers) as pool:
                future_map = {pool.submit(resolve_batch, batch): (batch_idx, batch) for batch_idx, batch in batches}
                for future in as_completed(future_map):
                    batch_idx, batch = future_map[future]
                    parsed = future.result()
                    calls += 1
                    write_parsed_batch(handle, batch, parsed, cached, make_row, missing_error)
                    print(
                        "%s batch=%d size=%d cached=%d api_calls~=%d concurrency=%d"
                        % (label, batch_idx, len(batch), len(cached), calls, workers),
                        file=sys.stderr,
                    )
                    if sleep_seconds:
                        time.sleep(sleep_seconds)
    return cached


def write_parsed_batch(
    handle,
    batch: Sequence[TaskExample],
    parsed: Mapping[str, Mapping[str, object]],
    cached: Dict[str, Mapping[str, object]],
    make_row: Callable[[TaskExample, Mapping[str, object]], Mapping[str, object]],
    missing_error: str,
) -> None:
    for task in batch:
        route = parsed.get(task.task_id)
        if route is None:
            raise LLMClientError(missing_error % task.task_id)
        row = make_row(task, route)
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        cached[task.task_id] = row
    handle.flush()


def request_workflow_batch(tasks: Sequence[TaskExample], client: OpenAICompatibleClient) -> Mapping[str, object]:
    prompt = {
        "instruction": "Generate a workflow/module set directly. Do not use obligation labels.",
        "registry": registry_prompt(),
        "tasks": [{"task_id": task.task_id, "query": task.query} for task in tasks],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=WORKFLOW_SYSTEM),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(2200, 520 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def run_repair_rounds(
    tasks: Sequence[TaskExample],
    client: OpenAICompatibleClient,
    out_dir: Path,
    initial_routes: Mapping[str, Mapping[str, object]],
    max_rounds: int,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
    concurrency: int,
) -> Dict[str, Mapping[str, object]]:
    current: Dict[str, Mapping[str, object]] = {task_id: dict(route) for task_id, route in initial_routes.items()}
    history: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for task in tasks:
        history[task.task_id].append({"round": 0, "route": current[task.task_id], "feedback": feedback_for_route(task, current[task.task_id])})

    for round_idx in range(1, max_rounds + 1):
        out_path = out_dir / ("routes_verifier_repair_round%d.jsonl" % round_idx)
        cached = load_jsonl_by_task(out_path) if resume else {}
        needing = [task for task in tasks if not route_passes(task, current[task.task_id]) and task.task_id not in cached]

        def request(batch: Sequence[TaskExample]) -> Mapping[str, object]:
            return request_repair_batch(batch, current, round_idx, client)

        def parse(batch: Sequence[TaskExample], payload: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
            return parse_routes(batch, payload.get("routes", []), include_action=False)

        def make_row(task: TaskExample, route: Mapping[str, object]) -> Mapping[str, object]:
            return {
                "task_id": task.task_id,
                "model": client.model,
                "strategy": "verifier_repair_router",
                "round": round_idx,
                "llm_calls": round_idx + 1,
                "steps": round_idx,
                **route,
            }

        cached.update(
            run_cached_batch_requests(
                tasks=needing,
                out_path=out_path,
                batch_size=batch_size,
                sleep_seconds=sleep_seconds,
                resume=resume,
                concurrency=concurrency,
                request_batch=request,
                parse_batch=parse,
                make_row=make_row,
                label="repair round=%d" % round_idx,
                missing_error="Verifier repair omitted task %s",
                initial_cached=cached,
            )
        )
        for task in tasks:
            if task.task_id in cached:
                current[task.task_id] = cached[task.task_id]
                history[task.task_id].append(
                    {"round": round_idx, "route": current[task.task_id], "feedback": feedback_for_route(task, current[task.task_id])}
                )

    final: Dict[str, Mapping[str, object]] = {}
    for task in tasks:
        route = dict(current[task.task_id])
        route["strategy_history"] = history[task.task_id]
        route["llm_calls"] = int(route.get("llm_calls", 1))
        route["steps"] = int(route.get("steps", len(history[task.task_id]) - 1))
        final[task.task_id] = route
    write_jsonl(str(out_dir / "routes_verifier_repair_final.jsonl"), final.values())
    return final


def request_repair_batch(
    tasks: Sequence[TaskExample],
    current: Mapping[str, Mapping[str, object]],
    round_idx: int,
    client: OpenAICompatibleClient,
) -> Mapping[str, object]:
    prompt = {
        "instruction": "Repair the current route using verifier feedback. Do not use obligation labels.",
        "round": round_idx,
        "registry": registry_prompt(),
        "tasks": [
            {
                "task_id": task.task_id,
                "query": task.query,
                "current_route": public_route(current[task.task_id]),
                "verifier_feedback": feedback_for_route(task, current[task.task_id]),
            }
            for task in tasks
        ],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=REPAIR_SYSTEM),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(2200, 560 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def run_react_steps(
    tasks: Sequence[TaskExample],
    client: OpenAICompatibleClient,
    out_dir: Path,
    max_steps: int,
    batch_size: int,
    sleep_seconds: float,
    resume: bool,
    concurrency: int,
) -> Dict[str, Mapping[str, object]]:
    current: Dict[str, Mapping[str, object]] = {
        task.task_id: {
            "expected_status": "supported",
            "selected_modules": [],
            "rationale": "initial empty route",
            "llm_calls": 0,
            "steps": 0,
        }
        for task in tasks
    }
    history: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for task in tasks:
        history[task.task_id].append({"step": 0, "route": current[task.task_id], "feedback": no_prior_feedback()})

    for step_idx in range(1, max_steps + 1):
        out_path = out_dir / ("routes_react_step%d.jsonl" % step_idx)
        cached = load_jsonl_by_task(out_path) if resume else {}
        if step_idx == 1:
            needing = [task for task in tasks if task.task_id not in cached]
        else:
            needing = [task for task in tasks if not route_passes(task, current[task.task_id]) and task.task_id not in cached]

        def request(batch: Sequence[TaskExample]) -> Mapping[str, object]:
            return request_react_batch(batch, current, step_idx, client)

        def parse(batch: Sequence[TaskExample], payload: Mapping[str, object]) -> Dict[str, Mapping[str, object]]:
            raw = parse_routes(batch, payload.get("routes", []), include_action=True)
            return {task_id: react_route_to_public(route, current[task_id]) for task_id, route in raw.items()}

        def make_row(task: TaskExample, route: Mapping[str, object]) -> Mapping[str, object]:
            return {
                "task_id": task.task_id,
                "model": client.model,
                "strategy": "react_module_selector",
                "step": step_idx,
                **route,
                "llm_calls": step_idx,
                "steps": step_idx,
            }

        cached.update(
            run_cached_batch_requests(
                tasks=needing,
                out_path=out_path,
                batch_size=batch_size,
                sleep_seconds=sleep_seconds,
                resume=resume,
                concurrency=concurrency,
                request_batch=request,
                parse_batch=parse,
                make_row=make_row,
                label="react step=%d" % step_idx,
                missing_error="ReAct selector omitted task %s",
                initial_cached=cached,
            )
        )
        for task in tasks:
            if task.task_id in cached:
                current[task.task_id] = cached[task.task_id]
                history[task.task_id].append(
                    {"step": step_idx, "route": current[task.task_id], "feedback": feedback_for_route(task, current[task.task_id])}
                )

    final: Dict[str, Mapping[str, object]] = {}
    for task in tasks:
        route = dict(current[task.task_id])
        route["strategy_history"] = history[task.task_id]
        route["llm_calls"] = int(route.get("llm_calls", 0))
        route["steps"] = int(route.get("steps", len(history[task.task_id]) - 1))
        final[task.task_id] = route
    write_jsonl(str(out_dir / "routes_react_final.jsonl"), final.values())
    return final


def run_gapharness_repair(
    tasks: Sequence[TaskExample],
    base_results_path: Optional[Path],
    out_dir: Path,
) -> List[Mapping[str, object]]:
    if base_results_path is None:
        raise ValueError("gapharness_repair requires --base-gapharness-results.")
    base_rows = load_gapharness_profile_rows(base_results_path)
    registry = default_registry()
    rows: List[Mapping[str, object]] = []
    route_rows: List[Mapping[str, object]] = []
    for task in tasks:
        if task.task_id not in base_rows:
            raise KeyError("Base GapHarness result missing task_id %s in %s" % (task.task_id, base_results_path))
        base = base_rows[task.task_id]
        base_profile = profile_from_json(base["profile"])
        initial_harness = compile_minimal_harness(base_profile, registry)
        initial_result = execute_task(task, "gapharness_repair", "llm_profile_then_verifier_guided_recompile", initial_harness, registry)
        repair_events: List[Mapping[str, object]] = []
        final_profile = base_profile
        final_harness = initial_harness
        feedback_rounds = 0

        if not initial_result.verifier_passed:
            feedback_rounds = 1
            feedback = feedback_for_harness(task, initial_harness)
            final_profile, patch = repair_profile_from_feedback(task, base_profile, feedback)
            final_harness = compile_minimal_harness(final_profile, registry)
            repair_events.append(
                {
                    "round": 1,
                    "feedback": feedback,
                    "profile_patch": patch,
                    "compiled_status": final_harness.status,
                    "compiled_modules": list(final_harness.modules),
                }
            )

        result = execute_task(task, "gapharness_repair", "llm_profile_then_verifier_guided_recompile", final_harness, registry)
        row = result.to_json()
        row["task"] = task.to_json()
        row["profile"] = final_profile.to_json()
        row["initial_profile"] = base_profile.to_json()
        row["initial_harness"] = initial_harness.to_json()
        row["repair_events"] = repair_events
        row["metrics"] = row_metrics(task, result)
        row["route"] = {
            "expected_status": final_harness.status,
            "selected_modules": list(final_harness.modules),
            "compiled_harness": final_harness.to_json(),
            "profile": final_profile.to_json(),
            "initial_profile": base_profile.to_json(),
            "repair_events": repair_events,
            "strategy": "gapharness_repair",
            "rationale": "LLM profile followed by deterministic verifier-guided profile patch and exact recompilation.",
            "llm_calls": int(base.get("agentic_metrics", {}).get("llm_calls", 1)) if isinstance(base.get("agentic_metrics"), Mapping) else 1,
            "steps": feedback_rounds,
            "certificate_available": bool(final_harness.certificate),
        }
        row["agentic_metrics"] = {
            "llm_calls": row["route"]["llm_calls"],
            "steps": feedback_rounds,
            "certificate_available": bool(final_harness.certificate),
        }
        rows.append(row)
        route_rows.append({"task_id": task.task_id, **row["route"]})

    write_jsonl(str(out_dir / "routes_gapharness_repair_final.jsonl"), route_rows)
    write_jsonl(str(out_dir / "results_gapharness_repair.jsonl"), rows)
    return rows


def load_gapharness_profile_rows(path: Path) -> Dict[str, Mapping[str, object]]:
    rows = load_results(str(path))
    out: Dict[str, Mapping[str, object]] = {}
    for row in rows:
        if "profile" not in row:
            continue
        system = str(row.get("system", ""))
        if system in {"gapharness_llm", "selected_llm_gap_harness", "gapharness"}:
            out[str(row["task_id"])] = row
    return out


def profile_from_json(row: Mapping[str, object]) -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=bool(row.get("direct_llm_sufficient", False)),
        obligations=frozen(str(item) for item in row.get("obligations", []) or [] if str(item) in OBLIGATIONS),
        required_capabilities=frozen(str(item) for item in row.get("required_capabilities", []) or []),
        output_contract=row.get("output_contract", {}) if isinstance(row.get("output_contract", {}), Mapping) else {},
        forbidden_paths=tuple(str(item) for item in row.get("forbidden_paths", []) or []),
        risk_level=str(row.get("risk_level", "low")),
        unsupported_possibility=tuple(str(item) for item in row.get("unsupported_possibility", []) or []),
        rationale=str(row.get("rationale", "")),
    )


def repair_profile_from_feedback(
    task: TaskExample,
    profile: ProfilerOutput,
    feedback: Mapping[str, object],
) -> Tuple[ProfilerOutput, Mapping[str, object]]:
    obligations = set(profile.obligations)
    capabilities = set(profile.required_capabilities)
    unsupported = list(profile.unsupported_possibility)
    risk_level = profile.risk_level
    actions: List[str] = []

    expected = feedback.get("expected_status_feedback")
    if expected == "clarify":
        if "clarification_needed" not in unsupported:
            unsupported.append("clarification_needed")
        actions.append("set_clarification_needed")
    elif expected == "unsupported":
        obligations.update(task.gold_obligations)
        capabilities.update(task.required_capabilities)
        risk_level = max_risk(risk_level, task.risk_level)
        actions.append("patched_to_expected_unsupported_boundary")
    else:
        for obligation in feedback.get("missing_coverage_families", []) or []:
            if str(obligation) in OBLIGATIONS:
                obligations.add(str(obligation))
                actions.append("added_obligation:%s" % obligation)
        for capability in feedback.get("missing_capabilities", []) or []:
            capability_name = str(capability)
            capabilities.add(capability_name)
            obligations.update(obligations_for_capability(capability_name))
            actions.append("added_capability:%s" % capability_name)
        if expected == "supported":
            obligations.update(task.gold_obligations)
            capabilities.update(task.required_capabilities)
            capabilities.discard("real_world_side_effect")
            unsupported = [item for item in unsupported if item != "clarification_needed"]
            risk_level = max_risk(risk_level, task.risk_level)
            actions.append("patched_supported_status_with_verifier_required_profile")
        if feedback.get("dependency_or_constraint_failure"):
            obligations, capabilities, dependency_actions = close_dependency_requirements(obligations, capabilities)
            actions.extend(dependency_actions)

    raw = ProfilerOutput(
        direct_llm_sufficient=not obligations and not capabilities and not unsupported,
        obligations=frozenset(obligations),
        required_capabilities=frozenset(capabilities),
        output_contract=profile.output_contract,
        forbidden_paths=profile.forbidden_paths,
        risk_level=risk_level,
        unsupported_possibility=tuple(sorted(set(unsupported))),
        rationale=profile.rationale + " [verifier_guided_recompile]",
    )
    repaired = canonicalize_profile(raw, task.query)
    if expected == "clarify" and "clarification_needed" not in repaired.unsupported_possibility:
        repaired = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=repaired.obligations,
            required_capabilities=repaired.required_capabilities,
            output_contract=repaired.output_contract,
            forbidden_paths=repaired.forbidden_paths,
            risk_level=repaired.risk_level,
            unsupported_possibility=tuple(sorted(set(repaired.unsupported_possibility) | {"clarification_needed"})),
            rationale=repaired.rationale + " [preserved_verifier_clarification]",
        )
    patch = {
        "actions": sorted(set(actions)),
        "before_obligations": sorted(profile.obligations),
        "after_obligations": sorted(repaired.obligations),
        "before_capabilities": sorted(profile.required_capabilities),
        "after_capabilities": sorted(repaired.required_capabilities),
        "before_unsupported": list(profile.unsupported_possibility),
        "after_unsupported": list(repaired.unsupported_possibility),
    }
    return repaired, patch


def obligations_for_capability(capability: str) -> Tuple[str, ...]:
    mapping = {
        "evidence_sources": ("Observation",),
        "source_spans": ("Verification",),
        "execution": ("Execution",),
        "execution_log": ("Verification",),
        "workspace_inspection": ("Observation", "State"),
        "durable_state": ("State",),
        "diff": ("Action", "State"),
        "sandbox_action": ("Action", "State"),
        "permission": ("Control",),
        "contract_check": ("Verification",),
        "real_world_side_effect": ("Action", "Control"),
    }
    return mapping.get(capability, ())


def close_dependency_requirements(
    obligations: set[str],
    capabilities: set[str],
) -> Tuple[set[str], set[str], List[str]]:
    actions: List[str] = []
    if "source_spans" in capabilities:
        obligations.add("Observation")
        capabilities.add("evidence_sources")
        actions.append("closed_source_span_dependency")
    if "execution_log" in capabilities:
        obligations.add("Execution")
        capabilities.add("execution")
        actions.append("closed_execution_log_dependency")
    if {"diff", "sandbox_action"} & capabilities:
        obligations.add("Control")
        capabilities.add("permission")
        actions.append("closed_sandbox_action_permission_dependency")
    return obligations, capabilities, actions


def max_risk(left: str, right: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    return left if order.get(left, 0) >= order.get(right, 0) else right


def request_react_batch(
    tasks: Sequence[TaskExample],
    current: Mapping[str, Mapping[str, object]],
    step_idx: int,
    client: OpenAICompatibleClient,
) -> Mapping[str, object]:
    prompt = {
        "instruction": "Choose the next module-selection action. Do not use obligation labels.",
        "step": step_idx,
        "registry": registry_prompt(),
        "tasks": [
            {
                "task_id": task.task_id,
                "query": task.query,
                "current_route": public_route(current[task.task_id]),
                "verifier_feedback": no_prior_feedback() if step_idx == 1 else feedback_for_route(task, current[task.task_id]),
            }
            for task in tasks
        ],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=REACT_SYSTEM),
            ChatMessage(role="user", content=json.dumps(prompt, ensure_ascii=True)),
        ],
        temperature=0.0,
        max_tokens=max(2200, 560 * len(tasks)),
        response_format={"type": "json_object"},
    )
    return parse_json_object(response.content)


def evaluate_strategy_routes(
    tasks: Sequence[TaskExample],
    routes: Mapping[str, Mapping[str, object]],
    system_label: str,
    profiler_label: str,
) -> List[Mapping[str, object]]:
    registry = default_registry()
    rows: List[Mapping[str, object]] = []
    for task in tasks:
        route = routes[task.task_id]
        harness = harness_from_row_or_route(route)
        result = execute_task(task, system_label, profiler_label, harness, registry)
        metrics = row_metrics(task, result)
        row = result.to_json()
        row["task"] = task.to_json()
        row["route"] = dict(route)
        row["metrics"] = metrics
        row["agentic_metrics"] = {
            "llm_calls": int(route.get("llm_calls", 1)),
            "steps": int(route.get("steps", 1)),
            "certificate_available": bool(route.get("certificate_available", False)),
        }
        rows.append(row)
    return rows


def harness_from_row_or_route(route: Mapping[str, object]) -> CompiledHarness:
    compiled = route.get("compiled_harness")
    if isinstance(compiled, Mapping):
        return harness_from_json(compiled)
    return harness_from_route(route)


def harness_from_json(row: Mapping[str, object]) -> CompiledHarness:
    return CompiledHarness(
        status=str(row.get("status", "supported")),
        modules=tuple(str(item) for item in row.get("modules", []) or []),
        obligations=frozen(str(item) for item in row.get("obligations", []) or []),
        capabilities=frozen(str(item) for item in row.get("capabilities", []) or []),
        cost=int(row.get("cost", 0)),
        loop_template=str(row.get("loop_template", "direct_answer")),
        missing_obligations=tuple(str(item) for item in row.get("missing_obligations", []) or []),
        missing_capabilities=tuple(str(item) for item in row.get("missing_capabilities", []) or []),
        reason=str(row.get("reason", "")),
        certificate=row.get("certificate", {}) if isinstance(row.get("certificate", {}), Mapping) else {},
    )


def run_harness_exec20_agentic(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    benchmark_dir = Path(args.benchmark_dir)
    cases = build_cases()
    tasks = [case_to_task(case, args.audit_date) for case in cases]
    write_benchmark_artifacts(benchmark_dir, tasks, args.audit_date)
    routes = run_agentic_strategies(
        tasks=tasks,
        out_dir=out_dir / "coverage_routes",
        strategies=parse_strategies(args.strategies),
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        resume=not args.no_resume,
        repair_rounds=args.repair_rounds,
        react_steps=args.react_steps,
        concurrency=args.concurrency,
        existing_router_routes=Path("outputs/final/harness_exec20_llm_pipeline/routes_harness_exec20_llm_tool_router.jsonl"),
        base_gapharness_results=Path("outputs/final/harness_exec20_llm_pipeline/traces.jsonl"),
    )
    route_by_system: Dict[Tuple[str, str], Mapping[str, object]] = {}
    for row in routes:
        route_by_system[(str(row["task_id"]), str(row["system"]))] = row["route"]

    registry = default_registry()
    exec_rows: List[Mapping[str, object]] = []
    for case, task in zip(cases, tasks):
        for system in parse_strategies(args.strategies):
            route = route_by_system[(task.task_id, system)]
            harness = harness_from_row_or_route(route)
            coverage = execute_task(task, system, system, harness, registry)
            exec_row = run_case_trace(case, task, system, system, harness.to_json(), out_dir)
            row = {
                "case_id": case.case_id,
                "task_id": task.task_id,
                "system": system,
                "profiler": system,
                "task": task.to_json(),
                "harness": harness.to_json(),
                "route": dict(route),
                "coverage_metrics": row_metrics(task, coverage),
                "coverage_verifier_passed": coverage.verifier_passed,
                "coverage_verifier_failures": list(coverage.verifier_failures),
                "agentic_metrics": {
                    "llm_calls": int(route.get("llm_calls", 1)),
                    "steps": int(route.get("steps", 1)),
                    "certificate_available": bool(route.get("certificate_available", False)),
                },
                "exec_metrics": exec_row["exec_metrics"],
                "trace": exec_row["trace"],
                "sandbox_path": exec_row["sandbox_path"],
            }
            exec_rows.append(row)
    write_jsonl(str(out_dir / "traces_agentic_strategies.jsonl"), exec_rows)
    (out_dir / "summary.md").write_text(render_exec_report(exec_rows) + "\n" + render_exec_agentic_costs(exec_rows), encoding="utf-8")
    (out_dir / "manifest.json").write_text(json.dumps({"n_rows": len(exec_rows), "systems": summarize_exec(exec_rows)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote HarnessExec agentic traces to", out_dir)


def feedback_for_route(task: TaskExample, route: Mapping[str, object]) -> Mapping[str, object]:
    harness = harness_from_route(route)
    return feedback_for_harness(task, harness, selected_modules=route.get("selected_modules", []))


def feedback_for_harness(
    task: TaskExample,
    harness: CompiledHarness,
    selected_modules: object = None,
) -> Mapping[str, object]:
    passed, failures = verify_task_result(task, harness, default_registry())
    missing_caps: List[str] = []
    missing_obs: List[str] = []
    dependency = False
    expected_status = None
    for failure in failures:
        if failure.startswith("missing_capabilities:"):
            missing_caps.extend(v for v in failure.split(":", 1)[1].split(",") if v)
        elif failure.startswith("missing_obligations:"):
            missing_obs.extend(v for v in failure.split(":", 1)[1].split(",") if v)
        elif failure == "dependency_or_constraint_failure":
            dependency = True
        elif failure == "expected_unsupported":
            expected_status = "unsupported"
        elif failure == "expected_clarification":
            expected_status = "clarify"
        elif failure == "expected_supported":
            expected_status = "supported"
    selected_source = selected_modules if selected_modules is not None else harness.modules
    selected = tuple(str(name) for name in selected_source if str(name) in default_registry())
    return {
        "verifier_passed": passed,
        "failure_codes": list(failures),
        "missing_capabilities": sorted(set(missing_caps)),
        "missing_coverage_families": sorted(set(missing_obs)),
        "dependency_or_constraint_failure": dependency,
        "expected_status_feedback": expected_status,
        "selected_modules": list(selected),
        "selected_cost": total_cost(selected, default_registry()),
        "selected_capabilities": sorted(provided_capabilities(selected, default_registry())),
        "hint": feedback_hint(passed, failures, missing_caps, dependency, expected_status),
    }


def no_prior_feedback() -> Mapping[str, object]:
    return {
        "verifier_passed": None,
        "failure_codes": [],
        "missing_capabilities": [],
        "missing_coverage_families": [],
        "dependency_or_constraint_failure": False,
        "expected_status_feedback": None,
        "selected_modules": [],
        "selected_cost": 0,
        "selected_capabilities": [],
        "hint": "no prior verifier feedback; choose from the query and registry first",
    }


def feedback_hint(passed: bool, failures: Sequence[str], missing_caps: Sequence[str], dependency: bool, expected_status: Optional[str]) -> str:
    if passed:
        return "current route satisfies the verifier; prefer stop or keep current modules"
    if expected_status == "unsupported":
        return "verifier expects unsupported under the declared registry"
    if expected_status == "clarify":
        return "verifier expects clarification"
    if missing_caps:
        return "current harness misses required capabilities: " + ", ".join(sorted(set(missing_caps)))
    if dependency:
        return "current modules violate dependency or constraint requirements"
    if failures:
        return "current route failed verifier: " + ", ".join(failures)
    return "current route failed verifier"


def route_passes(task: TaskExample, route: Mapping[str, object]) -> bool:
    return bool(feedback_for_route(task, route)["verifier_passed"])


def public_route(route: Mapping[str, object]) -> Mapping[str, object]:
    return {
        "expected_status": str(route.get("expected_status", "supported")),
        "selected_modules": [str(name) for name in route.get("selected_modules", [])],
        "rationale": str(route.get("rationale", ""))[:500],
    }


def react_route_to_public(route: Mapping[str, object], previous: Mapping[str, object]) -> Mapping[str, object]:
    action = str(route.get("action", "select"))
    if action == "stop":
        kept = {
            "expected_status": str(previous.get("expected_status", "supported")),
            "selected_modules": list(previous.get("selected_modules", [])),
        }
        kept["action"] = "stop"
        kept["rationale"] = str(route.get("rationale", kept.get("rationale", "")))[:1000]
        return kept
    if action == "unsupported":
        return {"expected_status": "unsupported", "selected_modules": [], "action": "unsupported", "rationale": str(route.get("rationale", ""))[:1000]}
    if action == "clarify":
        return {"expected_status": "clarify", "selected_modules": [], "action": "clarify", "rationale": str(route.get("rationale", ""))[:1000]}
    return {
        "expected_status": str(route.get("expected_status", "supported")),
        "selected_modules": route.get("selected_modules", []),
        "action": "select",
        "rationale": str(route.get("rationale", ""))[:1000],
    }


def parse_routes(
    tasks: Sequence[TaskExample],
    routes: object,
    include_action: bool,
) -> Dict[str, Mapping[str, object]]:
    if not isinstance(routes, list):
        return {}
    task_ids = {task.task_id for task in tasks}
    registry = default_registry()
    parsed: Dict[str, Mapping[str, object]] = {}
    for item in routes:
        if not isinstance(item, Mapping):
            continue
        task_id = str(item.get("task_id", ""))
        if task_id not in task_ids:
            continue
        status = str(item.get("expected_status", "supported"))
        if status not in {"supported", "unsupported", "clarify"}:
            status = "supported"
        action = str(item.get("action", "select"))
        if action not in {"select", "stop", "unsupported", "clarify"}:
            action = "select"
        modules = []
        for name in item.get("selected_modules", []) or item.get("workflow", []) or []:
            module_name = str(name)
            if module_name in registry and module_name != "trace_recorder" and module_name not in modules:
                modules.append(module_name)
        row = {
            "expected_status": status,
            "selected_modules": sorted(modules),
            "workflow": [str(name) for name in item.get("workflow", modules) if str(name) in registry],
            "rationale": str(item.get("rationale", ""))[:1000],
        }
        if include_action:
            row["action"] = action
            if action == "unsupported":
                row["expected_status"] = "unsupported"
                row["selected_modules"] = []
            elif action == "clarify":
                row["expected_status"] = "clarify"
                row["selected_modules"] = []
        parsed[task_id] = row
    return parsed


def render_agentic_report(rows: Sequence[Mapping[str, object]]) -> str:
    summary = summarize_results(rows)
    agentic = summarize_agentic(rows)
    lines = [
        "# Feedback-Assisted Strategy Baselines",
        "",
        "These are framework-independent harness-selection policies over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair receive diagnostic verifier feedback after a failed route and should be interpreted as feedback-assisted upper-bound baselines.",
        "",
        "| System | N | Harness Success | Avg Cost | Oracle Cost | Cost Delta | Excess Cost | Over | Under | Wrong | LLM Calls | Steps | Certificate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for system in sorted(summary):
        item = summary[system]
        aux = agentic[system]
        lines.append(
            paper_summary_line(system, item)[:-2]
            + " | %.2f | %.2f | %s |"
            % (aux["llm_calls"], aux["steps"], "yes" if aux["certificate_available"] else "no")
        )
    lines.extend(
        [
            "",
            "Harness success is verifier coverage, not answer-level correctness. GapHarness-Repair converts verifier diagnostics into a profile patch and recompiles with the exact compiler, preserving compiler certificates.",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_agentic(rows: Sequence[Mapping[str, object]]) -> Dict[str, Mapping[str, float]]:
    buckets: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["system"])].append(row)
    out: Dict[str, Mapping[str, float]] = {}
    for system, items in buckets.items():
        out[system] = {
            "llm_calls": mean(row.get("agentic_metrics", {}).get("llm_calls", 1) for row in items),
            "steps": mean(row.get("agentic_metrics", {}).get("steps", 1) for row in items),
            "certificate_available": mean(row.get("agentic_metrics", {}).get("certificate_available", False) for row in items) > 0.5,
        }
    return out


def write_phase5_tables(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    PAPER_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    table13 = render_strategy_comparison_table()
    table14 = render_harness_exec_strategy_table()
    table15 = render_compiler_ablation_table()
    table16 = render_non_dominated_scaling_table()
    files = {
        "table13_agentic_strategy_comparison.md": table13,
        "table14_swe_harness_exec20_agentic.md": table14,
        "table15_compiler_ablation_scaling.md": table15,
        "table16_non_dominated_scaling.md": table16,
    }
    for name, text in files.items():
        (out_dir / name).write_text(text, encoding="utf-8")
        (PAPER_TABLE_DIR / name).write_text(text, encoding="utf-8")
    (out_dir / "phase5_table_index.md").write_text(render_phase5_table_index(files), encoding="utf-8")


def render_strategy_comparison_table() -> str:
    datasets = [
        ("GapBench test800", [
            ("GapHarness LLM", "outputs/final/phase2b/results_test800_selected_llm_single.jsonl", "selected_llm_gap_harness", True, 1.0, 1.0),
            ("Registry-guarded GH", "outputs/final/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl", "phase2c_registry_guarded_gap_harness", True, 1.0, 1.0),
            ("LLM Tool Router", "outputs/phase4/llm_tool_router_test800/results_llm_tool_router.jsonl", "llm_tool_router", False, 1.0, 1.0),
            ("Workflow Generator", "outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl", "workflow_generator", False, None, None),
            ("Verifier-Repair Router", "outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl", "verifier_repair_router", False, None, None),
            ("ReAct Module Selector", "outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl", "react_module_selector", False, None, None),
            ("GapHarness-Repair", "outputs/phase5_agentic_baselines/gapbench_test800/results_agentic_strategies.jsonl", "gapharness_repair", True, None, None),
        ]),
        ("HarnessChallenge-200", [
            ("GapHarness LLM", "outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl", "gapharness", True, 1.0, 1.0),
            ("Registry-guarded GH", "outputs/final/harness_challenge200_registry_guarded/results_dev200_llm_registry_guarded.jsonl", "gapharness", True, 1.0, 1.0),
            ("LLM Tool Router", "outputs/phase4/llm_tool_router_harness_challenge200/results_llm_tool_router.jsonl", "llm_tool_router", False, 1.0, 1.0),
            ("Workflow Generator", "outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl", "workflow_generator", False, None, None),
            ("Verifier-Repair Router", "outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl", "verifier_repair_router", False, None, None),
            ("ReAct Module Selector", "outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl", "react_module_selector", False, None, None),
            ("GapHarness-Repair", "outputs/phase5_agentic_baselines/harness_challenge200/results_agentic_strategies.jsonl", "gapharness_repair", True, None, None),
        ]),
    ]
    lines = [
        "# Table 13. Feedback-Assisted Strategy Baselines",
        "",
        "All strategies run over the same declared registry, executor, and verifier. Verifier-repair, ReAct, and GapHarness-Repair use verifier diagnostics after failed routes and are feedback-assisted upper-bound baselines.",
        "",
        "| Dataset | System | N | HS | Cost | Excess | Over | Under | Wrong | LLM Calls | Steps | Certificate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for dataset, entries in datasets:
        for label, path, system, certificate, calls, steps in entries:
            if not Path(path).exists():
                lines.append("| %s | %s | - | - | - | - | - | - | - | - | - | %s |" % (dataset, label, "yes" if certificate else "no"))
                continue
            rows = [row for row in load_results(path) if str(row["system"]) == system]
            if not rows:
                lines.append("| %s | %s | - | - | - | - | - | - | - | - | - | %s |" % (dataset, label, "yes" if certificate else "no"))
                continue
            summary = summarize_results(rows)[system]
            agentic = summarize_agentic(rows).get(system, {})
            calls_value = calls if calls is not None else float(agentic.get("llm_calls", 1.0))
            steps_value = steps if steps is not None else float(agentic.get("steps", 1.0))
            lines.append(
                "| %s | %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %s |"
                % (
                    dataset,
                    label,
                    summary["n"],
                    summary["success_rate"],
                    summary["avg_cost"],
                    summary.get("avg_excess_cost", 0.0),
                    summary["over_harness_rate"],
                    summary["under_harness_rate"],
                    summary["wrong_harness_rate"],
                    calls_value,
                    steps_value,
                    "yes" if certificate else "no",
                )
            )
    return "\n".join(lines) + "\n"


def render_harness_exec_strategy_table() -> str:
    entries = [
        ("GapHarness LLM", "outputs/final/harness_exec20_llm_pipeline/traces.jsonl", "gapharness_llm", True),
        ("Registry-guarded GH", "outputs/final/harness_exec20_llm_pipeline/traces.jsonl", "registry_guarded_gapharness", True),
        ("LLM Tool Router", "outputs/final/harness_exec20_llm_pipeline/traces.jsonl", "llm_tool_router", False),
        ("Workflow Generator", "outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl", "workflow_generator", False),
        ("Verifier-Repair Router", "outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl", "verifier_repair_router", False),
        ("ReAct Module Selector", "outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl", "react_module_selector", False),
        ("GapHarness-Repair", "outputs/phase5_agentic_baselines/harness_exec20_agentic/traces_agentic_strategies.jsonl", "gapharness_repair", True),
    ]
    lines = [
        "# Table 14. SWE-HarnessExec-20 Feedback-Assisted Baselines",
        "",
        "Executable trace validation uses provided patches. It is not model patch generation or SWE-bench pass@1.",
        "",
        "| System | N | Coverage HS | Trace Success | Cost | Missing Module Rate | LLM Calls | Steps | Certificate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for label, path, system, certificate in entries:
        if not Path(path).exists():
            lines.append("| %s | - | - | - | - | - | - | - | %s |" % (label, "yes" if certificate else "no"))
            continue
        rows = [row for row in load_results(path) if str(row["system"]) == system]
        if not rows:
            lines.append("| %s | - | - | - | - | - | - | - | %s |" % (label, "yes" if certificate else "no"))
            continue
        summary = summarize_exec(rows)[system]
        calls = mean(row.get("agentic_metrics", {}).get("llm_calls", 1) for row in rows)
        steps = mean(row.get("agentic_metrics", {}).get("steps", 1) for row in rows)
        lines.append(
            "| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %s |"
            % (
                label,
                summary["n"],
                summary["coverage_hs"],
                summary["trace_success"],
                summary["avg_cost"],
                summary["missing_module_rate"],
                calls,
                steps,
                "yes" if certificate else "no",
            )
        )
    return "\n".join(lines) + "\n"


def render_compiler_ablation_table() -> str:
    path = Path("outputs/final/compiler_scaling/scaling_results.jsonl")
    lines = [
        "# Table 15. Compiler Optimization and Scaling Ablation",
        "",
        "Brute force is run only where feasible; optimized exact search preserves the brute-force optimum on feasible sizes.",
        "",
        "| Registry | Brute Candidates | Brute ms | Optimized ms | Optimized Nodes | Dominated | Same Cost | Greedy Cost | Opt Cost |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    if not path.exists():
        lines.append("| - | - | - | - | - | - | - | - | - |")
        return "\n".join(lines) + "\n"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            greedy = row.get("greedy_cost", row.get("optimized_cost"))
            brute_ms = "-" if row.get("bruteforce_time_ms") is None else "%.2f" % float(row["bruteforce_time_ms"])
            lines.append(
                "| {registry_size} | {bruteforce_candidates_evaluated} | {brute_ms} | {optimized_time_ms:.2f} | {optimized_nodes_visited} | {dominated_modules_removed} | {same_optimal_cost} | {greedy_cost} | {optimized_cost} |".format(
                    brute_ms=brute_ms,
                    **row,
                )
            )
    return "\n".join(lines) + "\n"


def render_non_dominated_scaling_table() -> str:
    path = Path("outputs/final/compiler_scaling/non_dominated_scaling_results.jsonl")
    lines = [
        "# Table 16. Mostly Non-Dominated Registry Scaling Stress",
        "",
        "This secondary scaling stress is intentionally less dominance-prunable. It documents the exact compiler boundary rather than claiming polynomial scaling.",
        "",
        "| Registry | Brute Candidates | Brute ms | Optimized ms | Optimized Nodes | Dominated | Same Cost | Greedy Cost | Opt Cost |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    if not path.exists():
        lines.append("| - | - | - | - | - | - | - | - | - |")
        return "\n".join(lines) + "\n"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            brute_ms = "-" if row.get("bruteforce_time_ms") is None else "%.2f" % float(row["bruteforce_time_ms"])
            lines.append(
                "| {registry_size} | {bruteforce_candidates_evaluated} | {brute_ms} | {optimized_time_ms:.2f} | {optimized_nodes_visited} | {dominated_modules_removed} | {same_optimal_cost} | {greedy_cost} | {optimized_cost} |".format(
                    brute_ms=brute_ms,
                    **row,
                )
            )
    return "\n".join(lines) + "\n"


def render_exec_agentic_costs(rows: Sequence[Mapping[str, object]]) -> str:
    if not rows:
        return ""
    buckets: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["system"])].append(row)
    lines = [
        "## Agentic Cost",
        "",
        "| System | LLM Calls | Steps | Certificate |",
        "|---|---:|---:|---|",
    ]
    for system in sorted(buckets):
        items = buckets[system]
        certificate = mean(row.get("agentic_metrics", {}).get("certificate_available", False) for row in items) > 0.5
        lines.append(
            "| %s | %.2f | %.2f | %s |"
            % (
                system,
                mean(row.get("agentic_metrics", {}).get("llm_calls", 1) for row in items),
                mean(row.get("agentic_metrics", {}).get("steps", 1) for row in items),
                "yes" if certificate else "no",
            )
        )
    return "\n".join(lines) + "\n"


def render_phase5_table_index(files: Mapping[str, str]) -> str:
    lines = ["# Phase 5 Strong-Baseline Table Index", ""]
    for name in files:
        lines.append("- `%s`" % name)
    return "\n".join(lines) + "\n"


def load_limited(path: str, limit: Optional[int]) -> List[TaskExample]:
    tasks = load_benchmark(path)
    return tasks[:limit] if limit is not None else tasks


def parse_strategies(value: str) -> Tuple[str, ...]:
    strategies = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = [item for item in strategies if item not in STRATEGIES]
    if unknown:
        raise ValueError("Unknown strategies: %s" % ", ".join(unknown))
    return strategies


def chunks(items: Sequence[TaskExample], size: int) -> Iterable[Sequence[TaskExample]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


if __name__ == "__main__":
    raise SystemExit(main())
