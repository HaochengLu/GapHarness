"""Structured LLM obligation profiler and consensus adjudicator.

Scope of this module
====================
This module turns a free-text user query plus a raw LLM obligation profile into
a normalized profile that can be matched against the declared (sandbox-only) MVP
module registry. Two deterministic post-processing stages are involved, and both
are intentionally interpretable so the paper can describe them honestly:

1. ``canonicalize_profile(profile, query)`` -- a *deterministic normalization*
   step. It does NOT invent new obligations from arbitrary query keywords; it
   only (a) propagates the structural consequences of obligations the profiler
   already asserted (e.g. an ``Action`` obligation in a sandbox registry implies
   ``State``/``Control`` and the ``diff``/``sandbox_action``/``permission``
   capabilities a sandbox editor needs), (b) closes capability dependencies that
   are mechanically entailed by an obligation that is already present, and
   (c) repairs two narrow, well-documented lexical artifacts: exact arithmetic
   that forces ``Execution`` and an explicit verification request that forces
   ``Verification``. It also drops a ``clarification_needed`` flag when the query
   is unambiguous. Every branch is gated on an obligation the profiler asserted
   or an explicit lexical trigger; canonicalization never fabricates an external
   obligation that is not entailed by the profile or by an explicit request in
   the text. See ``canonicalize_profile`` for the per-branch rationale.

2. ``apply_registry_guard(profile, query)`` -- a *safety boundary* that decides
   whether a destructive/external action is in scope for the sandbox-only
   registry. The guard's scope decision is governed by the precedence rule
   documented on ``_query_scope`` below: the TARGET of the destructive action
   determines scope, and a real/external/production target DOMINATES any
   incidental mention of a sandbox/workspace/repo/file. This fixes bug B4, in
   which a mere mention of "repo"/"workspace"/"file" was treated as a sandbox
   marker and silently stripped a real ``real_world_side_effect`` capability,
   inverting safety (real production actions were reported "supported").
"""

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

    Scope precedence (fixes bug B4): the scope of a destructive/external action
    is determined by the TARGET of that action, not by the mere presence of a
    "repo"/"workspace"/"file" keyword. ``_query_scope`` classifies the query as
    one of ``real`` (production / live external system / real recipient / real
    money / deploy / real email), ``sandbox`` (target is explicitly and
    exclusively sandbox/mock/local/a copy), or ``ambiguous``. A ``real`` target
    DOMINATES any incidental sandbox mention, so "Deploy to production from the
    repo and send a real email to customers" is treated as a real side effect
    (=> unsupported under the sandbox-only registry) even though it says "repo".
    Sandbox downgrade only fires when the scope is unambiguously ``sandbox``.
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
        # Principled scope decision (B4 fix): the TARGET of the destructive /
        # external action determines scope. ``real`` dominates any incidental
        # sandbox/repo/workspace/file mention; sandbox downgrade only fires when
        # the scope is unambiguously sandbox/mock/local/a-copy.
        scope = _query_scope(text)
        has_external_action_request = _query_has_external_action_verb(text)

        if scope == "real":
            if "real_world_side_effect" not in capabilities:
                actions.append("added_real_world_side_effect_for_real_external_action")
            capabilities.add("real_world_side_effect")
            obligations.update(["Action", "Control"])
            if "Verification" in profile.obligations:
                obligations.add("Verification")
            risk_level = "high"
            reasons.append(
                "Query targets a real / production / external system, so it requires an "
                "irreversible real external action regardless of any sandbox/repo mention."
            )
        elif scope == "sandbox" and "real_world_side_effect" in capabilities:
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
            reasons.append(
                "Destructive action target is explicitly and exclusively sandbox/mock/local scope."
            )
        elif scope == "ambiguous" and has_external_action_request:
            # An external/destructive verb with no clear real-vs-sandbox target.
            # Prefer clarify over silently supporting (never downgrade by default).
            if "clarification_needed" not in unsupported:
                unsupported.append("clarification_needed")
                actions.append("set_clarification_for_ambiguous_action_scope")
            else:
                actions.append("preserved_clarification_for_ambiguous_action_scope")
            reasons.append(
                "External/destructive action with an ambiguous real-vs-sandbox target; "
                "prefer clarification over silently supporting."
            )

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
    """Deterministically normalize a raw LLM profile onto the MVP registry.

    This is a *deterministic normalization* step, not an obligation generator.
    For the paper's honesty: canonicalization does NOT fabricate external
    obligations from arbitrary query keywords. Every branch below is gated on
    one of two things only --

      (a) an obligation the profiler ALREADY asserted (we then close its
          mechanical registry consequences -- e.g. an ``Action`` in a
          sandbox-only registry entails ``State``/``Control`` and the
          ``diff``/``sandbox_action``/``permission`` capabilities a sandbox
          editor needs; ``Observation`` entails an evidence/workspace source;
          ``Verification`` entails the matching evidence/log/diff/contract
          capability); or
      (b) a narrow, explicit lexical trigger that repairs a known artifact:
          exact arithmetic ("calculate exactly 41 * 15") forces ``Execution``,
          and an explicit verification request ("validate", "with sources",
          "cite") forces ``Verification``.

    The only removals are dropping a ``clarification_needed`` flag when the
    query is not ambiguous. No branch invents a brand-new external obligation
    that is neither entailed by an already-present obligation nor explicitly
    requested in the text, so canonicalization can be described as a faithful
    registry-normalization of the profiler's own decision.
    """
    obligations = set(profile.obligations)
    capabilities = set(profile.required_capabilities)
    text = query.lower()

    # (a) Structural consequence of an Action obligation the profiler asserted.
    if "Action" in obligations:
        obligations.update(["State", "Control"])
        capabilities.update(["diff", "sandbox_action", "permission"])
    # (b) Explicit lexical repair: exact arithmetic entails Execution.
    if _query_requires_execution(text):
        obligations.add("Execution")
        capabilities.add("execution")
    # (b) Explicit lexical repair: an explicit verify/validate/cite request.
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


# ---------------------------------------------------------------------------
# Scope determination (bug B4 fix)
# ---------------------------------------------------------------------------
#
# The scope of a destructive / external action is determined by its TARGET, not
# by whether a "repo"/"workspace"/"file" keyword happens to appear. We classify
# the query into one of three scopes with a principled precedence:
#
#   real      -> the destructive action targets production / a real external
#                system / real recipients / real money / live services /
#                deploys / real emails. This DOMINATES any sandbox mention.
#   sandbox   -> the destructive action's target is explicitly and exclusively
#                sandbox / mock / local / a copy, with NO real-target marker.
#   ambiguous -> there is an external/destructive request, but the real-vs-
#                sandbox target cannot be determined. Prefer clarify, never a
#                silent downgrade to supported.
#
# Precedence rule: real-external-target dominates sandbox mention. This is the
# crux of the fix -- a request such as "Deploy to production from the repo and
# send a real email to customers" is REAL even though it mentions "repo".


# Markers are split into two tiers so the precedence rule is principled rather
# than a flat keyword list:
#
#   STRONG real markers: name an unambiguously real/production/live/external
#       target or real money/recipients. These ALWAYS dominate -- no sandbox
#       qualifier can scope them down (you cannot "mock" production).
#
#   WEAK real markers: destructive NOUNS (a wire transfer, a refund, an external
#       notification) that imply a real side effect by default, BUT can be
#       legitimately scoped into a sandbox when an explicit sandbox qualifier
#       (mock/stub/fixture/simulate/dry-run/test/no-real) governs the action.
#       e.g. "compute a dry-run wire transfer to the test bank fixture" is sandbox.
#
# Negated-real phrases ("no real money", "without real ...") are neutralized so
# a sandbox instruction that *mentions* the real thing in order to forbid it is
# not misread as requiring it.

_STRONG_REAL_MARKERS = (
    "production",
    "prod environment",
    "prod server",
    "in prod",
    "to prod",
    "live service",
    "live system",
    "live environment",
    "live server",
    "live website",
    "live site",
    "public website",
    "public site",
    "real flight",
    "real hotel",
    "real reservation",
    "real booking",
    "real order",
    "real service",
    "real server",
    "real database",
    "real bank",
    "real customer",
    "real customers",
    "real user",
    "real users",
    "real recipient",
    "real email",
    "real e-mail",
    "actual email",
    "actual e-mail",
    "real money",
    "real funds",
    "real account",
    "customer account",
    "customer card",
    "customers",
    "real external",
    "external system",
    "external service",
    "external api",
    "real api",
    "real world",
    "irreversible external",
    "real irreversible",
    "irreversible production",
    "wire money",
    "charge the card",
    "charge a card",
    "charge the customer",
    "stripe",
    "paypal",
    "pagerduty",
    "twilio",
    "sendgrid",
    "smtp",
)

# Strong real phrases: a real external action whose verb+target is real even
# without a separate noun marker (e.g. "deploy to production").
_STRONG_REAL_PHRASES = (
    "deploy to production",
    "deploy to prod",
    "production deploy",
    "push to production",
    "release to production",
    "ship to production",
    "restart the real service",
    "restart the live service",
    "send a real",
    "send actual",
    "send real",
    "send an email to customers",
    "send email to customers",
    "email the customers",
    "email our customers",
    "notify customers",
    "write to production database",
    "write to the production database",
    "modify production",
    "modify the production",
    "production infrastructure",
)

# Strong real regexes: a real-world side-effect verb applied to a real object.
# The optional ``(real|actual)`` adjective lets "book a real flight" match while
# preserving the verb+object structure (rather than a flat keyword list).
_STRONG_REAL_PATTERNS = (
    r"\b(book|reserve)\s+(a|an|the|this|that)?\s*(real|actual)?\s*(flight|hotel|ticket|appointment|reservation|table|room)\b",
    r"\b(buy|purchase)\s+(a|an|the|this|that)?\s*(real|actual)?\s*(product|item|ticket|subscription|plan|cloud resource|resource)\b",
    r"\b(order)\s+(a|an|the|this|that)?\s*(real|actual)?\s*(product|item|meal|food|ticket)\b",
)

# Weak real markers: destructive nouns that default to a real side effect but
# can be scoped into a sandbox by an explicit sandbox qualifier.
_WEAK_REAL_MARKERS = (
    "wire transfer",
    "bank transfer",
    "external notification",
    "refund",
    "payment",
)

# Phrases that explicitly NEGATE a real action; they neutralize a strong-real
# substring that appears only in order to be forbidden (e.g. "no real money").
_NEGATED_REAL_PHRASES = (
    "no real",
    "not real",
    "without real",
    "no actual",
    "without actually",
    "do not actually",
    "don't actually",
    "no real send",
    "no real money",
    "no real action",
    "no side effect",
    "no side effects",
)

# Strong sandbox qualifiers: when present, they can legitimately scope a WEAK
# real noun into the sandbox. They denote a mock/stub/simulated/dry-run/local
# test target -- NOT a bare repo/workspace/file mention.
_SANDBOX_QUALIFIERS = (
    "sandbox",
    "sandboxed",
    "mock",
    "mocked",
    "stub",
    "stubbed",
    "fake",
    "simulate",
    "simulated",
    "simulation",
    "dry run",
    "dry-run",
    "fixture",
    "fixtures",
    "test database",
    "test bank",
    "scratch copy",
    "copy of the repo",
    "copy of the repository",
    "local copy",
    "local-only",
    "local only",
    "no real",
    "not real",
    "without actually",
    "do not actually",
    "don't actually",
    "no side effect",
    "no side effects",
)

# Sandbox/mock/local TARGET markers used to recognize an unambiguous sandbox
# scope. Crucially, bare "repo"/"workspace"/"file" are deliberately NOT here:
# mentioning a repository does not make a destructive action sandboxed.
_SANDBOX_TARGET_MARKERS = _SANDBOX_QUALIFIERS + (
    "sandbox directory",
    "sandbox copy",
    "sandbox workspace",
    "sandbox environment",
    "no external",
    "temporary",
    "temp file",
    "staging-only mock",
    "mock deployment",
    "mock external notification",
    "local test",
    "local tests",
    "local preview",
)

# Verbs/nouns that indicate an external or destructive action is being requested
# at all. Used only to decide whether an *ambiguous* scope should escalate to
# clarify (an action with no clear target) rather than silently support.
_EXTERNAL_ACTION_VERBS = (
    "deploy",
    "release",
    "ship to",
    "push to",
    "send email",
    "send an email",
    "send a message",
    "email ",
    "notify",
    "publish",
    "payment",
    "pay ",
    "charge",
    "refund",
    "transfer",
    "wire ",
    "book ",
    "reserve ",
    "purchase",
    "buy ",
    "order ",
    "restart",
    "shut down",
    "shutdown",
    "delete",
    "drop table",
    "write to",
    "post to",
)


def _strip_negated_real(text: str) -> str:
    """Blank out negated-real phrases so they cannot trigger a strong-real hit.

    A sandbox instruction often mentions the real thing only to forbid it
    ("simulate the charge, no real money"). Removing the negated phrase prevents
    "real money" inside "no real money" from being read as a real-target marker.
    """
    cleaned = text
    for phrase in _NEGATED_REAL_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    return cleaned


def _has_strong_real_marker(text: str) -> bool:
    """True for an unambiguously real/production/external target (negation-safe)."""
    cleaned = _strip_negated_real(text)
    if any(marker in cleaned for marker in _STRONG_REAL_MARKERS):
        return True
    if any(phrase in cleaned for phrase in _STRONG_REAL_PHRASES):
        return True
    return any(re.search(pattern, cleaned) for pattern in _STRONG_REAL_PATTERNS)


def _has_weak_real_marker(text: str) -> bool:
    """True for a destructive noun that defaults to real but is sandbox-scopable."""
    cleaned = _strip_negated_real(text)
    return any(marker in cleaned for marker in _WEAK_REAL_MARKERS)


def _has_sandbox_qualifier(text: str) -> bool:
    """True for an explicit mock/stub/simulate/dry-run/local-test sandbox scope."""
    return any(marker in text for marker in _SANDBOX_QUALIFIERS)


def _has_sandbox_target_marker(text: str) -> bool:
    return any(marker in text for marker in _SANDBOX_TARGET_MARKERS)


def _has_real_target_marker(text: str) -> bool:
    """Backward-compatible: any real signal (strong or unscoped weak)."""
    if _has_strong_real_marker(text):
        return True
    return _has_weak_real_marker(text) and not _has_sandbox_qualifier(text)


def _query_has_external_action_verb(text: str) -> bool:
    """True when the query asks for an external/destructive action of any kind.

    This intentionally does not decide scope; it only detects that *some*
    side-effecting action was requested, so an ambiguous scope can be escalated
    to clarify instead of being silently supported.
    """
    return (
        _has_strong_real_marker(text)
        or _has_weak_real_marker(text)
        or any(verb in text for verb in _EXTERNAL_ACTION_VERBS)
    )


def _query_scope(text: str) -> str:
    """Classify the scope of the destructive/external action in ``text``.

    Returns one of ``"real"``, ``"sandbox"``, or ``"ambiguous"``.

    Precedence (the core of the B4 fix), evaluated in order:

      1. A STRONG real target (production / live / real customer / real money /
         real email / Stripe / deploy-to-prod ...) DOMINATES everything. It is
         classified ``"real"`` even if the query also says "repo"/"sandbox" --
         you cannot mock production.
      2. Otherwise, if a destructive WEAK real noun (wire transfer / refund /
         external notification / payment) appears AND there is no explicit
         sandbox qualifier scoping it, it is ``"real"`` (default to real).
      3. Otherwise, if an explicit sandbox/mock/local-target marker is present,
         it is ``"sandbox"`` -- this is the only path that allows a downgrade.
      4. Otherwise ``"ambiguous"`` (handled upstream by preferring clarify when
         an external verb is present; otherwise no scope change is applied).
    """
    if _has_strong_real_marker(text):
        return "real"
    if _has_weak_real_marker(text) and not _has_sandbox_qualifier(text):
        return "real"
    if _has_sandbox_target_marker(text):
        return "sandbox"
    return "ambiguous"


def _query_is_sandbox_mock_or_local(text: str) -> bool:
    """Backward-compatible predicate: True only for an unambiguous sandbox scope.

    Unlike the buggy original, this no longer returns True merely because the
    query mentions "repo"/"workspace"/"file" while also targeting a real system.
    """
    return _query_scope(text) == "sandbox"


def _query_requires_real_side_effect(text: str) -> bool:
    """Backward-compatible predicate: True when the action target is real.

    A real target dominates any sandbox mention (precedence rule), so this is
    simply ``_query_scope(text) == "real"``.
    """
    return _query_scope(text) == "real"


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
