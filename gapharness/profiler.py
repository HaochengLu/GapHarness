"""Obligation profilers.

The heuristic profiler is a deterministic placeholder for rapid experiments.
The interface is intentionally narrow so an OpenAI structured-output profiler
can replace it without changing the compiler or evaluation code.
"""

from __future__ import annotations

import re

from .schema import ProfilerOutput, TaskExample, frozen


def profile_from_gold(task: TaskExample) -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=not task.gold_obligations and task.expected_status == "supported",
        obligations=task.gold_obligations,
        required_capabilities=task.required_capabilities,
        output_contract={"success_checker": task.success_checker},
        forbidden_paths=(
            "answer_from_parametric_memory_without_evidence",
        )
        if "Observation" in task.gold_obligations
        else (),
        risk_level=task.risk_level,
        unsupported_possibility=("clarification_needed",) if task.expected_status == "clarify" else (),
        rationale="Gold benchmark profile.",
    )


def profile_heuristic(query: str) -> ProfilerOutput:
    text = query.lower()
    obligations = set()
    capabilities = set()
    unsupported = []
    risk_level = "low"

    pure_language_markers = (
        "birthday wish",
        "haiku",
        "poem",
        "rewrite this sentence",
        "brainstorm names",
        "tagline",
    )
    if any(marker in text for marker in pure_language_markers) and "file" not in text:
        return ProfilerOutput(
            direct_llm_sufficient=True,
            obligations=frozen([]),
            required_capabilities=frozen([]),
            output_contract={"basic_answer": True},
            risk_level="low",
            rationale="Pure language request with no external warrant requirement.",
        )

    if any(marker in text for marker in ("latest", "today", "current", "news", "price", "web", "announcement")):
        obligations.update(["Observation", "Verification"])
        capabilities.update(["evidence_sources", "source_spans", "contract_check"])
        risk_level = "medium"

    if any(marker in text for marker in ("calculate", "compute", "exactly", "simulate", "lint", "schema")) or _has_word(
        text, ("run", "test")
    ):
        obligations.update(["Execution", "Verification"])
        capabilities.update(["execution", "execution_log", "contract_check"])

    if any(marker in text for marker in ("repo", "workspace", "file", "readme", "pdf", "database", "image", "logs")):
        obligations.add("Observation")
        capabilities.add("workspace_inspection")

    if any(marker in text for marker in ("checklist", "checkpoint", "remember", "resume", "intermediate artifact", "state")):
        obligations.add("State")
        capabilities.add("durable_state")

    action_markers = (
        "edit file",
        "modify",
        "create file",
        "write file",
        "commit",
        "open pr",
        "deploy",
        "send email",
        "call api",
        "write database",
        "delete",
    )
    if any(marker in text for marker in action_markers):
        obligations.update(["Action", "State", "Control", "Verification"])
        capabilities.update(["permission", "diff", "contract_check"])
        risk_level = "high" if any(marker in text for marker in ("deploy", "send email", "delete", "database")) else "medium"

    if any(marker in text for marker in ("payment", "production", "irreversible", "secret", "private key")):
        obligations.add("Control")
        capabilities.add("permission")
        risk_level = "high"

    if any(marker in text for marker in ("maybe", "whatever is best", "unclear target", "which one should i")):
        unsupported.append("clarification_needed")

    if any(marker in text for marker in ("wire money", "real bank", "send real email", "production deploy")):
        capabilities.add("real_world_side_effect")
        obligations.update(["Action", "Control", "Verification"])
        risk_level = "high"

    return ProfilerOutput(
        direct_llm_sufficient=not obligations and not capabilities and not unsupported,
        obligations=frozen(obligations),
        required_capabilities=frozen(capabilities),
        output_contract={
            "must_include_source": "source_spans" in capabilities,
            "must_include_execution_log": "execution_log" in capabilities,
            "must_include_diff": "diff" in capabilities,
        },
        forbidden_paths=(
            "answer_from_parametric_memory_without_evidence",
        )
        if "Observation" in obligations
        else (),
        risk_level=risk_level,
        unsupported_possibility=tuple(unsupported),
        rationale="Deterministic keyword profiler.",
    )


def profile_task(task: TaskExample, mode: str) -> ProfilerOutput:
    if mode == "gold":
        return profile_from_gold(task)
    if mode == "heuristic":
        return profile_heuristic(task.query)
    if mode in {"llm", "consensus", "llm_single", "llm_recall", "llm_minimality", "llm_cascade", "llm_registry_guarded"}:
        from .llm_client import OpenAICompatibleClient
        from .llm_profiler import profile_variant

        client = OpenAICompatibleClient()
        return profile_variant(task.query, client, mode)
    raise ValueError("Unknown profiler mode: %s" % mode)


def _has_word(text: str, words) -> bool:
    return any(re.search(r"\b%s\b" % re.escape(word), text) for word in words)
