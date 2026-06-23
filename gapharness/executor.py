"""Sandbox/mock executor for reproducible experiments."""

from __future__ import annotations

from typing import Mapping, Tuple

from .schema import CompiledHarness, RunResult, TaskExample, TraceEvent
from .verifiers import minimality_report, verify_task_result
from .schema import ModuleSpec


def execute_task(
    task: TaskExample,
    system: str,
    profiler: str,
    harness: CompiledHarness,
    registry: Mapping[str, ModuleSpec],
) -> RunResult:
    trace = []
    if harness.status == "clarify":
        trace.append(
            TraceEvent(
                step=0,
                module="compiler",
                event_type="clarify",
                message="Clarification required before a warranted harness can be compiled.",
            )
        )
        final_output = "Clarification needed before proceeding."
    elif harness.status == "unsupported":
        trace.append(
            TraceEvent(
                step=0,
                module="compiler",
                event_type="unsupported",
                message="No sufficient harness exists in the declared registry.",
                evidence={
                    "missing_obligations": list(harness.missing_obligations),
                    "missing_capabilities": list(harness.missing_capabilities),
                },
            )
        )
        final_output = "Unsupported under the declared registry."
    elif not harness.modules:
        trace.append(
            TraceEvent(
                step=0,
                module="direct_answer",
                event_type="model_output",
                message="Direct answer produced without external modules.",
            )
        )
        final_output = "Direct answer."
    else:
        for index, module_name in enumerate(harness.modules, start=1):
            module = registry[module_name]
            trace.append(
                TraceEvent(
                    step=index,
                    module=module_name,
                    event_type=module.module_type,
                    message="Executed sandbox module %s." % module_name,
                    evidence={
                        "provides": sorted(module.provides),
                        "capabilities": sorted(module.capabilities),
                        "verifier": module.verifier,
                    },
                )
            )
        final_output = "Sandbox answer with modules: %s." % ", ".join(harness.modules)

    passed, failures = verify_task_result(task, harness, registry)
    min_report = minimality_report(task, harness, registry)
    return RunResult(
        task_id=task.task_id,
        system=system,
        profiler=profiler,
        harness=harness,
        trace=tuple(trace),
        final_output=final_output,
        verifier_passed=passed,
        verifier_failures=failures,
        minimality_report=min_report,
    )
