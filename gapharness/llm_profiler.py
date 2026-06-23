"""Structured LLM obligation profiler and consensus adjudicator."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .llm_client import ChatMessage, OpenAICompatibleClient, parse_json_object
from .schema import OBLIGATIONS, ProfilerOutput, frozen
from .registry import default_registry, provided_capabilities


PROFILER_SYSTEM_PROMPT = """You are an obligation profiler for GapHarness.

Your job is not to choose tools. Your job is to decide which external obligations
must be satisfied before an LLM answer or action is warranted.

Allowed obligations:
- Observation: needs information outside prompt/model memory.
- Execution: needs deterministic computation, tests, code execution, parsing, validation, or simulation.
- State: needs durable task/workspace/intermediate state.
- Action: needs a sandboxed external mutation.
- Control: cross-cutting constraint that becomes explicit for permissions, privacy, budget, risk, irreversible actions, or user confirmation.
- Verification: independent proof such as citations, source spans, execution logs, contract checks, or diff checks. Light verification may be default, but include this obligation when a warranted answer depends on evidence, tests, exactness, risky action, or output contract.

Return one JSON object only. Schema:
{
  "direct_llm_sufficient": boolean,
  "obligations": ["Observation" | "Execution" | "State" | "Action" | "Control" | "Verification"],
  "required_capabilities": string[],
  "output_contract": object,
  "forbidden_paths": string[],
  "risk_level": "low" | "medium" | "high",
  "unsupported_possibility": string[],
  "rationale": string
}

Use required_capabilities from this vocabulary when applicable:
evidence_sources, source_spans, execution, execution_log, workspace_inspection,
durable_state, diff, sandbox_action, permission, contract_check, real_world_side_effect.

Important:
- Do not add Execution just because the query includes "latest".
- If the task asks for real deployment/email/payment/database write, include real_world_side_effect and Control.
- If the target is ambiguous, include "clarification_needed" in unsupported_possibility.
- Prefer minimal obligations, but never omit an obligation needed for a warranted answer.
"""

RECALL_BIAS = """
Calibration mode: recall-biased.
When uncertain, include an external obligation rather than omit it. The main failure to avoid is under-harnessing: answering or acting without a necessary observation, execution, state, action, control, or verification step.
"""

MINIMALITY_BIAS = """
Calibration mode: minimality-biased.
Only include an external obligation if omitting it would likely make the answer or action unwarranted. The main failure to avoid is over-harnessing: adding unnecessary modules, costs, latency, or risk.
"""


ADJUDICATOR_SYSTEM_PROMPT = """You adjudicate two independent GapHarness obligation profiles.
Return a single conservative-but-minimal JSON profile with the same schema.

Rules:
- Include an obligation if either profile gives a convincing reason for it.
- Remove obligations caused only by lexical accidents or over-broad routing.
- Preserve clarification_needed and real_world_side_effect when warranted.
- Keep required_capabilities aligned with the final obligations.
Return JSON only.
"""


def profile_llm(query: str, client: OpenAICompatibleClient, variant: str = "A", style: str = "single") -> ProfilerOutput:
    system_prompt = PROFILER_SYSTEM_PROMPT
    if style == "recall":
        system_prompt += "\n" + RECALL_BIAS
    elif style == "minimality":
        system_prompt += "\n" + MINIMALITY_BIAS
    prompt = (
        "Variant %s (%s). Profile this user query for external obligations.\n\n"
        "User query:\n%s" % (variant, style, query)
    )
    response = client.chat_json(
        [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=prompt),
        ],
        temperature=0.0,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )
    raw = _profile_from_payload(parse_json_object(response.content), source="llm_profiler_%s_%s" % (style, variant))
    return canonicalize_profile(raw, query)


def profile_consensus(query: str, client: OpenAICompatibleClient) -> ProfilerOutput:
    first = profile_llm(query, client, variant="A", style="recall")
    second = profile_llm(
        "Use a skeptical minimality lens. " + query,
        client,
        variant="B",
        style="minimality",
    )
    response = client.chat_json(
        [
            ChatMessage(role="system", content=ADJUDICATOR_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content="Query:\n%s\n\nProfile A:\n%s\n\nProfile B:\n%s"
                % (query, first.to_json(), second.to_json()),
            ),
        ],
        temperature=0.0,
        max_tokens=1200,
        response_format={"type": "json_object"},
    )
    raw = _profile_from_payload(parse_json_object(response.content), source="llm_consensus")
    return canonicalize_profile(raw, query)


def profile_variant(query: str, client: OpenAICompatibleClient, mode: str) -> ProfilerOutput:
    if mode in {"llm", "llm_single"}:
        return profile_llm(query, client, variant="A", style="single")
    if mode == "llm_recall":
        return profile_llm(query, client, variant="A", style="recall")
    if mode == "llm_minimality":
        return profile_llm(query, client, variant="A", style="minimality")
    if mode in {"consensus", "llm_cascade"}:
        return profile_consensus(query, client)
    if mode == "llm_registry_guarded":
        profile = profile_llm(query, client, variant="A", style="single")
        guarded, _metadata = apply_registry_guard(profile, query)
        return guarded
    raise ValueError("Unknown LLM profiler mode: %s" % mode)


def apply_registry_guard(
    profile: ProfilerOutput,
    query: str,
    registry: Optional[Mapping[str, object]] = None,
) -> Tuple[ProfilerOutput, Dict[str, object]]:
    """Post-process an LLM profile using declared registry boundaries.

    The guard is intentionally deterministic and only uses the query text, the
    predicted profile, and registry-supported capabilities. It corrects the
    Phase 2B calibration failure where sandbox/mock/local actions were lowered
    into unsupported real-world side effects.
    """
    active_registry = registry or default_registry()
    raw_status = infer_profile_status(profile, active_registry)
    text = query.lower()
    obligations = set(profile.obligations)
    capabilities = set(profile.required_capabilities)
    unsupported = list(profile.unsupported_possibility)
    risk_level = profile.risk_level
    actions: List[str] = []
    reasons: List[str] = []

    if _is_explicit_no_tool_language_request(text):
        if obligations or capabilities or unsupported:
            obligations.clear()
            capabilities.clear()
            unsupported = []
            risk_level = "low"
            actions.append("cleared_external_obligations_for_no_tool_language_request")
            reasons.append("Query explicitly forbids tools and asks for pure language work.")
    else:
        ambiguous_target = _query_has_ambiguous_action_target(text)
        real_side_effect = _query_requires_real_side_effect(text)
        sandbox_or_local = _query_is_sandbox_mock_or_local(text)

        if real_side_effect:
            if "real_world_side_effect" not in capabilities:
                actions.append("added_real_world_side_effect_for_real_external_action")
            capabilities.add("real_world_side_effect")
            obligations.update(["Action", "Control"])
            if "Verification" in profile.obligations:
                obligations.add("Verification")
            risk_level = "high"
            reasons.append("Query clearly asks for an irreversible real external action.")
        elif "real_world_side_effect" in capabilities and sandbox_or_local:
            capabilities.remove("real_world_side_effect")
            unsupported = [
                item
                for item in unsupported
                if item
                not in {
                    "real_world_side_effect",
                    "unsupported_real_world_side_effect",
                    "unsupported_external_side_effect",
                    "external_side_effect",
                }
            ]
            if risk_level == "high":
                risk_level = "medium"
            actions.append("removed_real_world_side_effect_for_sandbox_action")
            reasons.append("Query explicitly limits the action to sandbox/mock/local workspace scope.")

        if ambiguous_target:
            if "clarification_needed" not in unsupported:
                unsupported.append("clarification_needed")
                actions.append("set_clarification_for_ambiguous_action_target")
            else:
                actions.append("preserved_clarification_for_ambiguous_action_target")
            reasons.append("Query lacks a clear action target.")

    guarded = ProfilerOutput(
        direct_llm_sufficient=not obligations and not capabilities and not unsupported,
        obligations=frozenset(obligations),
        required_capabilities=frozenset(capabilities),
        output_contract=profile.output_contract,
        forbidden_paths=profile.forbidden_paths,
        risk_level=risk_level,
        unsupported_possibility=tuple(unsupported),
        rationale=profile.rationale + " [registry_guarded]",
    )
    guarded_status = infer_profile_status(guarded, active_registry)
    if raw_status == "unsupported" and guarded_status == "supported":
        actions.append("converted_unsupported_to_supported")
    elif raw_status != guarded_status:
        actions.append("converted_%s_to_%s" % (raw_status, guarded_status))

    actions = _dedupe(actions)
    metadata = {
        "profiler_variant": "llm_registry_guarded",
        "guard_applied": bool(actions),
        "guard_actions": actions,
        "guard_reason": " ".join(_dedupe(reasons)) if actions else "",
        "raw_predicted_obligations": sorted(profile.obligations),
        "guarded_predicted_obligations": sorted(guarded.obligations),
        "raw_required_capabilities": sorted(profile.required_capabilities),
        "guarded_required_capabilities": sorted(guarded.required_capabilities),
        "raw_expected_status": raw_status,
        "guarded_expected_status": guarded_status,
    }
    return guarded, metadata


def infer_profile_status(
    profile: ProfilerOutput,
    registry: Optional[Mapping[str, object]] = None,
) -> str:
    if "clarification_needed" in profile.unsupported_possibility:
        return "clarify"
    active_registry = registry or default_registry()
    module_names = [name for name in sorted(active_registry) if name != "trace_recorder"]
    available_capabilities = set(provided_capabilities(module_names, active_registry))
    missing_capabilities = set(profile.required_capabilities) - available_capabilities
    if missing_capabilities:
        return "unsupported"
    return "supported"


def _profile_from_payload(payload: Mapping[str, object], source: str) -> ProfilerOutput:
    obligations = _valid_obligations(payload.get("obligations", []))
    unsupported = tuple(str(item) for item in payload.get("unsupported_possibility", []) or [])
    return ProfilerOutput(
        direct_llm_sufficient=bool(payload.get("direct_llm_sufficient", not obligations)),
        obligations=frozen(obligations),
        required_capabilities=frozen(str(item) for item in payload.get("required_capabilities", []) or []),
        output_contract=payload.get("output_contract", {}) if isinstance(payload.get("output_contract", {}), dict) else {},
        forbidden_paths=tuple(str(item) for item in payload.get("forbidden_paths", []) or []),
        risk_level=str(payload.get("risk_level", "low")),
        unsupported_possibility=unsupported,
        rationale="%s: %s" % (source, str(payload.get("rationale", ""))[:800]),
    )


def canonicalize_profile(profile: ProfilerOutput, query: str) -> ProfilerOutput:
    """Map raw LLM profiler output onto the declared MVP registry semantics."""
    obligations = set(profile.obligations)
    capabilities = set(profile.required_capabilities)
    text = query.lower()

    if "Action" in obligations:
        obligations.update(["State", "Control"])
        capabilities.update(["diff", "sandbox_action", "permission"])
    if _query_requires_execution(text):
        obligations.add("Execution")
        capabilities.add("execution")
    if _query_requires_verification(text):
        obligations.add("Verification")
        capabilities.add("contract_check")
    if "Control" in obligations:
        capabilities.add("permission")
    if "State" in obligations and "Action" not in obligations:
        if not ({"durable_state", "workspace_inspection"} & capabilities):
            capabilities.add("durable_state")
    if "Observation" in obligations:
        if not ({"evidence_sources", "workspace_inspection"} & capabilities):
            if any(marker in text for marker in ("workspace", "repo", "file", "readme", "logs", "pdf", "image")):
                capabilities.add("workspace_inspection")
            else:
                capabilities.add("evidence_sources")
    if "Execution" in obligations:
        capabilities.add("execution")
    if "Verification" in obligations:
        if "Observation" in obligations and "evidence_sources" in capabilities:
            capabilities.add("source_spans")
        if "Execution" in obligations:
            capabilities.add("execution_log")
        if "Action" in obligations:
            capabilities.add("diff")
        if not ({"source_spans", "execution_log", "diff", "contract_check"} & capabilities):
            capabilities.add("contract_check")

    unsupported = list(profile.unsupported_possibility)
    if "clarification_needed" in unsupported and not _query_is_ambiguous(text):
        unsupported = [item for item in unsupported if item != "clarification_needed"]

    return ProfilerOutput(
        direct_llm_sufficient=not obligations and not capabilities and not unsupported,
        obligations=frozenset(obligations),
        required_capabilities=frozenset(capabilities),
        output_contract=profile.output_contract,
        forbidden_paths=profile.forbidden_paths,
        risk_level=profile.risk_level,
        unsupported_possibility=tuple(unsupported),
        rationale=profile.rationale + " [canonicalized_to_registry]",
    )


def _valid_obligations(values: object) -> List[str]:
    allowed = set(OBLIGATIONS)
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        text = str(value)
        if text in allowed and text not in result:
            result.append(text)
    return result


def _query_is_ambiguous(text: str) -> bool:
    markers = (
        "unclear target",
        "whichever file",
        "whatever file",
        "whatever is best",
        "which one should",
        "appropriate change",
        "some file",
        "maybe",
    )
    return any(marker in text for marker in markers)


def _query_requires_execution(text: str) -> bool:
    if any(marker in text for marker in ("calculate exactly", "compute exactly", "run test", "run tests", "lint", "schema validation")):
        return True
    return bool(re.search(r"\b\d+\s*[\*\+/%-]\s*\d+\b", text))


def _query_requires_verification(text: str) -> bool:
    return any(marker in text for marker in ("validate", "contract", "verify", "with sources", "cite", "source span"))


def _query_is_sandbox_mock_or_local(text: str) -> bool:
    markers = (
        "sandbox",
        "mock",
        "simulate",
        "simulated",
        "simulation",
        "dry run",
        "no real",
        "without actually",
        "do not actually",
        "local workspace",
        "workspace",
        "repo",
        "repository",
        "fixture",
        "temporary",
        "temp file",
        "sandbox directory",
        "sandboxed",
        "local file",
        "mock deployment",
        "mock external notification",
        "produce a diff",
        "patch in a sandbox",
    )
    return any(marker in text for marker in markers)


def _query_requires_real_side_effect(text: str) -> bool:
    if _query_is_sandbox_mock_or_local(text):
        return False
    markers = (
        "deploy to production",
        "production deploy",
        "restart the real service",
        "send a real",
        "actual email",
        "send actual",
        "send an email",
        "external notification",
        "wire money",
        "real bank",
        "write to a real database",
        "write to production database",
        "real database",
        "call a real external api",
        "modify production",
        "production infrastructure",
        "live service",
        "customer account",
        "real external",
        "irreversible external",
        "real irreversible",
        "irreversible production",
    )
    if any(marker in text for marker in markers):
        return True
    real_action_patterns = (
        r"\b(book|reserve)\s+(a|an|the|this|that)?\s*(flight|hotel|ticket|appointment|reservation|table|room)\b",
        r"\b(buy|purchase)\s+(a|an|the|this|that)?\s*(product|item|ticket|subscription|plan|cloud resource|resource)\b",
        r"\b(send|make|submit)\s+(a|an|the|this|that)?\s*(payment|wire transfer|bank transfer)\b",
        r"\b(order)\s+(a|an|the|this|that)?\s*(product|item|meal|food|ticket)\b",
    )
    return any(re.search(pattern, text) for pattern in real_action_patterns)


def _query_has_ambiguous_action_target(text: str) -> bool:
    markers = (
        "unclear target",
        "whichever file",
        "whatever file",
        "whatever is best",
        "which file is best",
        "appropriate change",
        "some file",
        "fix the project",
        "fix this project",
        "make the best change",
        "choose the best file",
    )
    return any(marker in text for marker in markers)


def _is_explicit_no_tool_language_request(text: str) -> bool:
    no_tool_markers = (
        "without browsing",
        "without web",
        "without running code",
        "without reading files",
        "do not browse",
        "don't browse",
        "do not run code",
        "don't run code",
        "do not read files",
        "don't read files",
        "no tools",
        "no external tools",
    )
    language_markers = (
        "brainstorm",
        "draft",
        "write",
        "rewrite",
        "outline",
        "explain",
        "translate",
        "summarize",
        "poem",
        "haiku",
        "tagline",
        "names",
    )
    action_markers = (
        "edit file",
        "modify file",
        "create file",
        "write file",
        "repo task",
        "workspace task",
        "run test",
        "run tests",
        "lint",
        "execute",
        "deploy",
        "send email",
        "database",
        "api",
    )
    return (
        any(marker in text for marker in no_tool_markers)
        and any(marker in text for marker in language_markers)
        and not any(marker in text for marker in action_markers)
    )


def _dedupe(values: Sequence[str]) -> List[str]:
    result = []
    seen = set()
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
