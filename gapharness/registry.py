"""Default module registry for the research MVP."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping

from .schema import ModuleSpec, frozen


DEFAULT_MODULES: List[ModuleSpec] = [
    ModuleSpec(
        name="web_retrieval",
        provides=frozen(["Observation"]),
        capabilities=frozen(["evidence_sources"]),
        cost=3,
        risk=("stale_source", "source_conflict"),
        verifier="source_availability_checker",
        module_type="observation",
    ),
    ModuleSpec(
        name="source_span_checker",
        provides=frozen(["Verification"]),
        capabilities=frozen(["source_spans"]),
        requires_obligations=frozen(["Observation"]),
        requires_capabilities=frozen(["evidence_sources"]),
        cost=1,
        risk=("unsupported_claim",),
        verifier="source_span_checker",
        module_type="verification",
    ),
    ModuleSpec(
        name="python_executor",
        provides=frozen(["Execution"]),
        capabilities=frozen(["execution"]),
        cost=2,
        risk=("runtime_error",),
        verifier="execution_started_checker",
        module_type="execution",
    ),
    ModuleSpec(
        name="execution_log_checker",
        provides=frozen(["Verification"]),
        capabilities=frozen(["execution_log"]),
        requires_obligations=frozen(["Execution"]),
        requires_capabilities=frozen(["execution"]),
        cost=1,
        risk=("missing_log",),
        verifier="execution_log_checker",
        module_type="verification",
    ),
    ModuleSpec(
        name="file_state_reader",
        provides=frozen(["Observation", "State"]),
        capabilities=frozen(["workspace_inspection"]),
        cost=2,
        risk=("stale_workspace",),
        verifier="workspace_snapshot_checker",
        module_type="observation",
    ),
    ModuleSpec(
        name="state_store",
        provides=frozen(["State"]),
        capabilities=frozen(["durable_state"]),
        cost=1,
        risk=("state_drift",),
        verifier="state_artifact_checker",
        module_type="state",
    ),
    ModuleSpec(
        name="sandbox_file_editor",
        provides=frozen(["Action", "State"]),
        capabilities=frozen(["diff", "sandbox_action"]),
        requires_obligations=frozen(["Control"]),
        requires_capabilities=frozen(["permission"]),
        cost=4,
        risk=("irreversible_change_if_not_sandboxed",),
        verifier="diff_checker",
        module_type="action",
    ),
    ModuleSpec(
        name="permission_gate",
        provides=frozen(["Control"]),
        capabilities=frozen(["permission"]),
        cost=1,
        risk=("approval_missing",),
        verifier="permission_checker",
        module_type="control",
    ),
    ModuleSpec(
        name="contract_verifier",
        provides=frozen(["Verification"]),
        capabilities=frozen(["contract_check"]),
        cost=1,
        risk=("judge_error",),
        verifier="contract_checker",
        module_type="verification",
    ),
    ModuleSpec(
        name="trace_recorder",
        provides=frozen([]),
        capabilities=frozen(["trace"]),
        cost=1,
        risk=("trace_noise",),
        verifier="trace_shape_checker",
        module_type="observability",
    ),
]


def default_registry() -> Dict[str, ModuleSpec]:
    return {module.name: module for module in DEFAULT_MODULES}


def subset_registry(module_names: Iterable[str]) -> Dict[str, ModuleSpec]:
    registry = default_registry()
    return {name: registry[name] for name in module_names if name in registry}


def provided_obligations(module_names: Iterable[str], registry: Mapping[str, ModuleSpec]) -> frozenset:
    values = set()
    for name in module_names:
        if name in registry:
            values.update(registry[name].provides)
    return frozenset(values)


def provided_capabilities(module_names: Iterable[str], registry: Mapping[str, ModuleSpec]) -> frozenset:
    values = set()
    for name in module_names:
        if name in registry:
            values.update(registry[name].capabilities)
    return frozenset(values)


def total_cost(module_names: Iterable[str], registry: Mapping[str, ModuleSpec]) -> int:
    return sum(registry[name].cost for name in module_names if name in registry)
