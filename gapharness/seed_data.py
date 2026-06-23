"""Synthetic 100-task seed benchmark for GapBench-Factorial.

These examples are scaffolding for the paper MVP. They are deliberately marked
as needing human review; the user plans to audit every gold label.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Sequence, Set, Tuple

from .compiler import compile_minimal_harness
from .registry import default_registry
from .schema import OBLIGATIONS, ProfilerOutput, TaskExample, frozen


def build_seed_tasks() -> List[TaskExample]:
    tasks: List[TaskExample] = []

    for index in range(10):
        tasks.append(
            _make_task(
                "pure-%03d" % (index + 1),
                "Write a concise birthday wish for a teammate, no browsing or tools needed. Case %d." % (index + 1),
                [],
                [],
                "pure_language_negative",
                "low",
                tags=("negative", "direct_ok"),
                expected_failure_if_direct="none",
            )
        )

    for index in range(8):
        tasks.append(
            _make_task(
                "bait-%03d" % (index + 1),
                "Tool bait: without searching, running code, or reading files, brainstorm three product names for case %d."
                % (index + 1),
                [],
                [],
                "tool_bait",
                "low",
                tags=("tool_bait", "direct_ok"),
                expected_failure_if_direct="none",
            )
        )

    single_specs = [
        ("Observation", "web"),
        ("Observation", "local"),
        ("Observation", "web"),
        ("Execution", "default"),
        ("Execution", "default"),
        ("Execution", "default"),
        ("State", "default"),
        ("State", "default"),
        ("State", "default"),
        ("Action", "default"),
        ("Action", "default"),
        ("Action", "default"),
        ("Control", "default"),
        ("Control", "default"),
        ("Control", "default"),
        ("Verification", "default"),
        ("Verification", "default"),
        ("Verification", "default"),
    ]
    for index, (obligation, mode) in enumerate(single_specs, start=1):
        obligations = _expand_obligations([obligation], sandbox=True)
        tasks.append(
            _make_task(
                "single-%03d" % index,
                _combo_query(obligations, index, mode=mode),
                obligations,
                _caps_for(obligations, mode=mode),
                "single_obligation",
                _risk_for(obligations),
                tags=("single", obligation.lower()),
            )
        )

    pair_index = 1
    for pair in combinations(OBLIGATIONS, 2):
        for repeat in range(2):
            mode = "web" if "Verification" in pair or repeat == 0 else "local"
            obligations = _expand_obligations(pair, sandbox=True)
            tasks.append(
                _make_task(
                    "pair-%03d" % pair_index,
                    _combo_query(obligations, pair_index, mode=mode),
                    obligations,
                    _caps_for(obligations, mode=mode),
                    "pairwise_obligation",
                    _risk_for(obligations),
                    tags=("pairwise",) + tuple(name.lower() for name in pair),
                )
            )
            pair_index += 1

    triple_index = 1
    for triple in combinations(OBLIGATIONS, 3):
        obligations = _expand_obligations(triple, sandbox=True)
        mode = "web" if "Observation" in obligations and "Verification" in obligations else "local"
        tasks.append(
            _make_task(
                "triple-%03d" % triple_index,
                _combo_query(obligations, triple_index, mode=mode),
                obligations,
                _caps_for(obligations, mode=mode),
                "triple_obligation",
                _risk_for(obligations),
                tags=("triple",) + tuple(name.lower() for name in triple),
            )
        )
        triple_index += 1

    for index in range(7):
        obligations = ["Action", "Control", "Verification"]
        tasks.append(
            _make_task(
                "unsupported-%03d" % (index + 1),
                "Production deploy request %d: deploy the service to production now and send a real external notification."
                % (index + 1),
                obligations,
                ["permission", "contract_check", "real_world_side_effect"],
                "unsupported",
                "high",
                expected_status="unsupported",
                tags=("unsupported", "real_world_side_effect"),
                expected_failure_if_direct="would_claim_real_world_action_without_authority",
            )
        )

    for index in range(7):
        obligations = ["Action", "Control", "Verification"]
        tasks.append(
            _make_task(
                "ambiguous-%03d" % (index + 1),
                "Unclear target %d: update whichever file is best and make the appropriate change." % (index + 1),
                obligations,
                ["permission", "diff", "contract_check"],
                "ambiguous",
                "medium",
                expected_status="clarify",
                tags=("ambiguous", "clarification_needed"),
                expected_failure_if_direct="would_act_without_a_clear_target",
            )
        )

    if len(tasks) != 100:
        raise AssertionError("Expected 100 seed tasks, got %d" % len(tasks))
    return tasks


def _make_task(
    task_id: str,
    query: str,
    obligations: Iterable[str],
    capabilities: Iterable[str],
    category: str,
    risk_level: str,
    expected_status: str = "supported",
    tags: Sequence[str] = (),
    expected_failure_if_direct: str = "",
) -> TaskExample:
    obligations_set = frozen(obligations)
    capabilities_set = frozen(capabilities)
    if expected_status == "supported":
        profile = ProfilerOutput(
            direct_llm_sufficient=not obligations_set and not capabilities_set,
            obligations=obligations_set,
            required_capabilities=capabilities_set,
            risk_level=risk_level,
        )
        oracle = compile_minimal_harness(profile, default_registry()).modules
    else:
        oracle = ()
    if not expected_failure_if_direct:
        expected_failure_if_direct = "missing_external_obligations" if obligations_set else "none"
    return TaskExample(
        task_id=task_id,
        query=query,
        gold_obligations=obligations_set,
        required_capabilities=capabilities_set,
        oracle_minimal_harness=oracle,
        success_checker="gold_obligation_capability_coverage",
        expected_failure_if_direct=expected_failure_if_direct,
        risk_level=risk_level,
        category=category,
        expected_status=expected_status,
        tags=tuple(tags),
        notes="Synthetic seed label; requires human audit before paper claims.",
    )


def _expand_obligations(obligations: Iterable[str], sandbox: bool) -> List[str]:
    values = set(obligations)
    if "Action" in values and sandbox:
        values.add("State")
        values.add("Control")
    return sorted(values)


def _caps_for(obligations: Iterable[str], mode: str) -> List[str]:
    values = set(obligations)
    caps: Set[str] = set()
    if "Observation" in values:
        caps.add("evidence_sources" if mode == "web" else "workspace_inspection")
    if "Execution" in values:
        caps.add("execution")
    if "State" in values and "Action" not in values:
        caps.add("durable_state")
    if "Action" in values:
        caps.add("diff")
    if "Control" in values:
        caps.add("permission")
    if "Verification" in values:
        caps.add("contract_check")
        if "Observation" in values and mode == "web":
            caps.add("source_spans")
        if "Execution" in values:
            caps.add("execution_log")
        if "Action" in values:
            caps.add("diff")
    return sorted(caps)


def _combo_query(obligations: Iterable[str], index: int, mode: str) -> str:
    values = set(obligations)
    parts = []
    if "Observation" in values:
        if mode == "web":
            parts.append("find the latest public announcement for ExampleProduct %d with sources" % index)
        else:
            parts.append("inspect the workspace README for ExampleProject %d" % index)
    if "Execution" in values:
        parts.append("calculate exactly %d * %d" % (index + 37, index + 11))
    if "State" in values and "Action" not in values:
        parts.append("create a durable checklist checkpoint for three subtasks")
    if "Action" in values:
        parts.append("create file sandbox_note_%d.txt in the sandbox workspace" % index)
    if "Control" in values:
        parts.append("apply a permission gate before any risky step")
    if "Verification" in values:
        parts.append("validate the final answer against the requested contract")
    if not parts:
        return "Answer a simple language-only request for case %d." % index
    return "For case %d, %s." % (index, "; then ".join(parts))


def _risk_for(obligations: Iterable[str]) -> str:
    values = set(obligations)
    if "Action" in values or "Control" in values:
        return "medium"
    if "Observation" in values and "Verification" in values:
        return "medium"
    return "low"
