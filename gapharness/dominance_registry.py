"""A module registry in which dominance pruning genuinely fires.

The default research registry (:mod:`gapharness.registry`) contains nine modules,
none of which strictly dominates another: every module either provides a unique
obligation/capability or carries a dependency that blocks the tie-safe dominance
rule in :func:`gapharness.compiler.module_dominates`. As a result the equivalence
replay over the default registry reports ``Avg Dominated = 0.0`` everywhere, which
makes the "dominance-pruned branch-and-bound" claim vacuous on that track.

This module supplies a *separate* registry that is explicitly engineered so that
several modules are strictly dominated by cheaper-or-equal alternatives offering a
superset of obligations/capabilities with no stricter dependencies. Compiling any
profile against it exercises the dominance-pruning code path with a nonzero
``dominated_module_count`` while remaining extensionally equal to an exact
brute-force search over the *same* registry.

The registry is intentionally small and self-contained so a brute-force reference
over its full power set is cheap, which lets the replay assert exact equivalence
rather than merely "no observed change".
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .schema import ModuleSpec, ProfilerOutput, frozen


def _module(
    name: str,
    provides,
    capabilities,
    cost: int,
    requires_obligations=(),
    requires_capabilities=(),
) -> ModuleSpec:
    return ModuleSpec(
        name=name,
        provides=frozen(provides),
        capabilities=frozen(capabilities),
        cost=cost,
        requires_obligations=frozen(requires_obligations),
        requires_capabilities=frozen(requires_capabilities),
        risk=(),
        verifier="%s_checker" % name,
        module_type="dominance_demo",
    )


# Each "_basic" module is strictly dominated by a "_pro" sibling that provides a
# superset of obligations/capabilities, requires no more dependencies, and costs
# the same or less (satisfying the tie-safe dominance rule in the compiler).
DOMINANCE_MODULES: List[ModuleSpec] = [
    # retriever_pro dominates retriever_basic: same Observation/evidence_sources,
    # an extra capability (fresh_index), strictly cheaper.
    _module("retriever_basic", ["Observation"], ["evidence_sources"], 4),
    _module("retriever_pro", ["Observation"], ["evidence_sources", "fresh_index"], 3),
    # exec_fast dominates exec_slow: identical provides/capabilities, cheaper.
    _module("exec_slow", ["Execution"], ["execution"], 5),
    _module("exec_fast", ["Execution"], ["execution"], 2),
    # state_pro dominates state_basic: identical provides/capabilities, cheaper.
    _module("state_basic", ["State"], ["durable_state"], 3),
    _module("state_pro", ["State"], ["durable_state"], 1),
    # Non-dominated verifiers so "supported" profiles still need real search and
    # so dominance does not collapse the whole registry to a trivial chain.
    _module(
        "span_verifier",
        ["Verification"],
        ["source_spans"],
        1,
        requires_obligations=["Observation"],
        requires_capabilities=["evidence_sources"],
    ),
    _module("contract_verifier", ["Verification"], ["contract_check"], 1),
]


def dominance_registry() -> Dict[str, ModuleSpec]:
    """Return the dominance-bearing registry keyed by module name."""

    return {module.name: module for module in DOMINANCE_MODULES}


def dominated_pairs() -> Tuple[Tuple[str, str], ...]:
    """Return the (dominated, dominator) pairs this registry is built to expose.

    Kept in sync with :data:`DOMINANCE_MODULES` so tests can assert the intended
    pruning actually fires rather than silently regressing to zero.
    """

    return (
        ("exec_slow", "exec_fast"),
        ("retriever_basic", "retriever_pro"),
        ("state_basic", "state_pro"),
    )


def _profile(obligations, capabilities, unsupported_possibility=()) -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=False,
        obligations=frozen(obligations),
        required_capabilities=frozen(capabilities),
        unsupported_possibility=tuple(unsupported_possibility),
        rationale="dominance replay probe",
    )


def replay_profiles() -> Tuple[Tuple[str, ProfilerOutput], ...]:
    """A spread of profiles that exercise the dominance/branch-and-bound path.

    The set deliberately covers: dominated-module preference, dependency chains,
    multi-obligation cover, the clarify short-circuit, the direct-answer
    short-circuit, and an unsatisfiable capability (``unsupported``).
    """

    return (
        ("direct_answer", _profile([], [])),
        ("observation_only", _profile(["Observation"], ["evidence_sources"])),
        ("observation_fresh_index", _profile(["Observation"], ["fresh_index"])),
        (
            "observation_plus_span_verification",
            _profile(["Observation", "Verification"], ["evidence_sources", "source_spans"]),
        ),
        ("execution_only", _profile(["Execution"], ["execution"])),
        (
            "execution_plus_contract",
            _profile(["Execution", "Verification"], ["execution", "contract_check"]),
        ),
        ("state_only", _profile(["State"], ["durable_state"])),
        (
            "full_cover",
            _profile(
                ["Observation", "Execution", "State", "Verification"],
                ["evidence_sources", "fresh_index", "execution", "durable_state", "contract_check"],
            ),
        ),
        ("clarify", _profile(["Observation"], ["evidence_sources"], ["clarification_needed"])),
        (
            "unsupported_capability",
            _profile(["Observation"], ["evidence_sources", "real_world_side_effect"]),
        ),
    )
