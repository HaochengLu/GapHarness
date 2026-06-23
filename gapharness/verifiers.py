"""Deterministic sufficiency and minimality verification."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Tuple

from .compiler import _candidate_valid
from .registry import provided_capabilities, provided_obligations, total_cost
from .schema import CompiledHarness, ModuleSpec, TaskExample


def verify_task_result(
    task: TaskExample,
    harness: CompiledHarness,
    registry: Mapping[str, ModuleSpec],
) -> Tuple[bool, Tuple[str, ...]]:
    failures: List[str] = []

    if task.expected_status == "clarify":
        if harness.status != "clarify":
            failures.append("expected_clarification")
        return (not failures, tuple(failures))

    if task.expected_status == "unsupported":
        if harness.status != "unsupported":
            failures.append("expected_unsupported")
        return (not failures, tuple(failures))

    if harness.status != "supported":
        failures.append("expected_supported")
        return (False, tuple(failures))

    provided_obs = provided_obligations(harness.modules, registry)
    provided_caps = provided_capabilities(harness.modules, registry)

    missing_obligations = set(task.gold_obligations) - set(provided_obs)
    if missing_obligations:
        failures.append("missing_obligations:%s" % ",".join(sorted(missing_obligations)))

    missing_caps = set(task.required_capabilities) - set(provided_caps)
    if missing_caps:
        failures.append("missing_capabilities:%s" % ",".join(sorted(missing_caps)))

    if not _candidate_valid(harness.modules, task.gold_obligations, task.required_capabilities, registry):
        failures.append("dependency_or_constraint_failure")

    return (not failures, tuple(failures))


def minimality_report(
    task: TaskExample,
    harness: CompiledHarness,
    registry: Mapping[str, ModuleSpec],
) -> Dict[str, object]:
    if harness.status != "supported" or not harness.modules:
        return {
            "drop_one": {},
            "redundant_modules": [],
            "redundancy": 0.0,
            "all_modules_necessary": True,
        }

    drop_one = {}
    redundant = []
    for module_name in harness.modules:
        remaining = tuple(name for name in harness.modules if name != module_name)
        still_valid = _candidate_valid(remaining, task.gold_obligations, task.required_capabilities, registry)
        drop_one[module_name] = {
            "remaining_modules": list(remaining),
            "verifier_passed": still_valid,
            "necessity": not still_valid,
        }
        if still_valid:
            redundant.append(module_name)

    redundancy = float(len(redundant)) / float(len(harness.modules))
    return {
        "drop_one": drop_one,
        "redundant_modules": redundant,
        "redundancy": redundancy,
        "all_modules_necessary": not redundant,
    }


def oracle_cost(task: TaskExample, registry: Mapping[str, ModuleSpec]) -> int:
    return total_cost(task.oracle_minimal_harness, registry)
