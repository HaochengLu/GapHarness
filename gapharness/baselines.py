"""Baseline harness policies."""

from __future__ import annotations

import re
from typing import Mapping, Tuple

from .compiler import choose_loop_template, compile_minimal_harness
from .profiler import profile_heuristic, profile_task
from .registry import provided_capabilities, provided_obligations, total_cost
from .schema import CompiledHarness, ModuleSpec, ProfilerOutput, TaskExample, frozen


SYSTEMS: Tuple[str, ...] = (
    "gapharness",
    "direct",
    "tool_router",
    "always_full",
    "difficulty_router",
    "oracle_minimal",
)


def compile_for_system(
    task: TaskExample,
    system: str,
    profiler_mode: str,
    registry: Mapping[str, ModuleSpec],
) -> Tuple[CompiledHarness, str]:
    if system == "gapharness":
        profile = profile_task(task, profiler_mode)
        return compile_minimal_harness(profile, registry), profiler_mode
    if system == "direct":
        return _direct(task), "none"
    if system == "tool_router":
        return _tool_router(task, registry), "router"
    if system == "always_full":
        return _always_full(task, registry), "none"
    if system == "difficulty_router":
        return _difficulty_router(task, registry), "difficulty"
    if system == "oracle_minimal":
        return _oracle(task, registry), "gold"
    raise ValueError("Unknown system: %s" % system)


def _direct(task: TaskExample) -> CompiledHarness:
    return CompiledHarness(
        status="supported",
        modules=(),
        obligations=frozen([]),
        capabilities=frozen([]),
        cost=0,
        loop_template="direct_answer",
        reason="Direct LLM baseline.",
    )


def _tool_router(task: TaskExample, registry: Mapping[str, ModuleSpec]) -> CompiledHarness:
    text = task.query.lower()
    modules = set()
    if any(marker in text for marker in ("latest", "today", "current", "web", "news", "price")):
        modules.add("web_retrieval")
    if any(marker in text for marker in ("calculate", "compute", "lint", "schema")) or _has_word(text, ("run", "test")):
        modules.add("python_executor")
    if any(marker in text for marker in ("repo", "workspace", "file", "readme", "pdf", "logs")):
        modules.add("file_state_reader")
    if any(marker in text for marker in ("edit file", "modify", "create file", "write file")):
        modules.add("sandbox_file_editor")
    if any(marker in text for marker in ("permission", "payment", "delete", "deploy")):
        modules.add("permission_gate")
    selected = tuple(sorted(name for name in modules if name in registry))
    obligations = provided_obligations(selected, registry)
    capabilities = provided_capabilities(selected, registry)
    return CompiledHarness(
        status="supported",
        modules=selected,
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(selected, registry),
        loop_template=choose_loop_template(obligations, capabilities),
        reason="Tool-first router baseline; no obligation-level verifier planning.",
    )


def _always_full(task: TaskExample, registry: Mapping[str, ModuleSpec]) -> CompiledHarness:
    selected = tuple(sorted(name for name in registry if name != "trace_recorder"))
    obligations = provided_obligations(selected, registry)
    capabilities = provided_capabilities(selected, registry)
    return CompiledHarness(
        status="supported",
        modules=selected,
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(selected, registry),
        loop_template="always_full_agent",
        reason="Always-full agent baseline.",
    )


def _difficulty_router(task: TaskExample, registry: Mapping[str, ModuleSpec]) -> CompiledHarness:
    text = task.query.lower()
    hard_markers = ("deploy", "delete", "database", "commit", "multi-step", "latest", "today")
    medium_markers = ("calculate", "compute", "file", "repo", "schema", "checklist")
    if any(marker in text for marker in hard_markers):
        return _always_full(task, registry)
    if any(marker in text for marker in medium_markers):
        profile = profile_heuristic(task.query)
        light_profile = ProfilerOutput(
            direct_llm_sufficient=profile.direct_llm_sufficient,
            obligations=profile.obligations,
            required_capabilities=frozen(
                cap
                for cap in profile.required_capabilities
                if cap in {"execution", "evidence_sources", "workspace_inspection", "durable_state"}
            ),
            risk_level=profile.risk_level,
            rationale="Difficulty router light harness.",
        )
        return compile_minimal_harness(light_profile, registry)
    return _direct(task)


def _oracle(task: TaskExample, registry: Mapping[str, ModuleSpec]) -> CompiledHarness:
    if task.expected_status == "clarify":
        return CompiledHarness(
            status="clarify",
            modules=(),
            obligations=task.gold_obligations,
            capabilities=task.required_capabilities,
            cost=0,
            loop_template="unsupported_or_clarify",
            reason="Oracle clarification.",
        )
    if task.expected_status == "unsupported":
        return CompiledHarness(
            status="unsupported",
            modules=(),
            obligations=task.gold_obligations,
            capabilities=task.required_capabilities,
            cost=0,
            loop_template="unsupported_or_clarify",
            missing_capabilities=tuple(sorted(task.required_capabilities)),
            reason="Oracle unsupported.",
        )
    selected = tuple(name for name in task.oracle_minimal_harness if name in registry)
    obligations = provided_obligations(selected, registry)
    capabilities = provided_capabilities(selected, registry)
    return CompiledHarness(
        status="supported",
        modules=selected,
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(selected, registry),
        loop_template=choose_loop_template(obligations, capabilities),
        reason="Oracle minimal harness from benchmark gold.",
    )


def _has_word(text: str, words) -> bool:
    return any(re.search(r"\b%s\b" % re.escape(word), text) for word in words)
