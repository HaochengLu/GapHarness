"""Independent exact minimum-cost valid-harness solver.

Why this file exists
--------------------
The gold ``oracle_minimal_harness`` labels in the GapBench benchmarks are
produced by :func:`gapharness.compiler.compile_minimal_harness` (``seed_data.py``
calls it at build time). Checking that GapHarness "matches the oracle" is
therefore tautological: the same code generated both sides of the comparison.

To turn "exact compiler == optimum" into a *real* cross-check of the compiler
implementation, this module re-derives the minimum-cost valid harness with a
deliberately DIFFERENT algorithm and an INDEPENDENT re-statement of the
validity predicate. It does not import any solver internals from
``compiler.py`` (no ``compile_minimal_harness``, no ``branch_and_bound_search``,
no ``_candidate_valid``, no ``dominance_prune``). The coverage / capability /
module-dependency semantics below are re-implemented from reading
``registry.py`` and ``schema.py`` only.

Algorithm (independent of compiler.py)
--------------------------------------
The selection problem is a 0/1 integer program: choose a binary vector
``x in {0,1}^M`` minimizing ``sum_i cost_i * x_i`` subject to

  * coverage:      for each required obligation o, sum of x_i over modules that
                   provide o is >= 1;
  * capabilities:  for each required capability c, sum of x_i over modules that
                   provide c is >= 1;
  * dependencies:  for every selected module i, each obligation it requires is
                   provided by some selected module, and likewise for each
                   capability it requires.

Rather than branch-and-bound with dominance pruning (the compiler's method),
this solver enumerates candidate subsets via :func:`itertools.combinations` in
non-decreasing total-cost order and returns the FIRST feasible subset under a
fully specified, deterministic tie-break. Because subsets are visited by
increasing cost, the first feasible subset is provably a minimum-cost solution;
ties at the minimum cost are resolved by an independent lexicographic key.

The dependency constraint is non-monotone in the sense that adding a module can
introduce a new unmet requirement, so feasibility is checked on each concrete
subset (the same situation the compiler handles by validating concrete
candidates). Enumerating by increasing cost and stopping at the first feasible
subset is an exact ILP solution by exhaustive certified search.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from .schema import ModuleSpec, ProfilerOutput, ordered

# Modules that never carry obligations/capabilities and exist only for
# observability are excluded from the optimisation pool, mirroring the registry
# contract (``trace_recorder`` provides no obligations). This name is read from
# the registry semantics, not imported from the compiler.
EXCLUDED_FROM_POOL: FrozenSet[str] = frozenset({"trace_recorder"})

CLARIFY_MARKER = "clarification_needed"


@dataclass(frozen=True)
class IndependentSolution:
    """Result of the independent minimum-cost-cover solver.

    ``status`` is one of ``supported`` / ``unsupported`` / ``clarify`` to mirror
    the compiler's notion. ``modules`` is the chosen subset (sorted). ``cost`` is
    the total registry cost of that subset. For ``unsupported`` / ``clarify`` the
    module set is empty and cost is 0.
    """

    status: str
    modules: Tuple[str, ...]
    cost: int
    obligations: Tuple[str, ...]
    capabilities: Tuple[str, ...]
    missing_obligations: Tuple[str, ...] = ()
    missing_capabilities: Tuple[str, ...] = ()
    candidates_enumerated: int = 0
    feasible_found: int = 0
    method: str = "increasing_cost_ilp_enumeration"

    def to_json(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "modules": list(self.modules),
            "cost": self.cost,
            "obligations": list(self.obligations),
            "capabilities": list(self.capabilities),
            "missing_obligations": list(self.missing_obligations),
            "missing_capabilities": list(self.missing_capabilities),
            "candidates_enumerated": self.candidates_enumerated,
            "feasible_found": self.feasible_found,
            "method": self.method,
        }


# ---------------------------------------------------------------------------
# Independent re-implementations of registry/schema semantics.
# These intentionally do NOT call gapharness.registry helpers either, so the
# coverage/cost arithmetic is a second, independent implementation.
# ---------------------------------------------------------------------------


def _pool_modules(registry: Mapping[str, ModuleSpec]) -> List[str]:
    """Candidate module names, deterministically ordered, pool exclusions applied."""
    return sorted(name for name in registry if name not in EXCLUDED_FROM_POOL)


def _provided_obligations(subset: Sequence[str], registry: Mapping[str, ModuleSpec]) -> FrozenSet[str]:
    out: set = set()
    for name in subset:
        out.update(registry[name].provides)
    return frozenset(out)


def _provided_capabilities(subset: Sequence[str], registry: Mapping[str, ModuleSpec]) -> FrozenSet[str]:
    out: set = set()
    for name in subset:
        out.update(registry[name].capabilities)
    return frozenset(out)


def _subset_cost(subset: Sequence[str], registry: Mapping[str, ModuleSpec]) -> int:
    return sum(registry[name].cost for name in subset)


def _is_feasible(
    subset: Sequence[str],
    required_obligations: FrozenSet[str],
    required_capabilities: FrozenSet[str],
    registry: Mapping[str, ModuleSpec],
) -> bool:
    """Independent re-statement of the ILP feasibility constraints.

    Mirrors validity as O_p subset O(S), C_p subset C(S), and every selected
    module's obligation/capability requirements satisfied by the subset.
    """
    provided_obs = _provided_obligations(subset, registry)
    provided_caps = _provided_capabilities(subset, registry)

    # Coverage constraints.
    if not required_obligations <= provided_obs:
        return False
    if not required_capabilities <= provided_caps:
        return False

    # Module dependency constraints.
    for name in subset:
        module = registry[name]
        if not frozenset(module.requires_obligations) <= provided_obs:
            return False
        if not frozenset(module.requires_capabilities) <= provided_caps:
            return False
    return True


def _tie_break_key(subset: Tuple[str, ...], registry: Mapping[str, ModuleSpec]) -> Tuple[int, int, Tuple[str, ...]]:
    """Deterministic, independent tie-break.

    Among subsets of equal minimum cost, prefer the smallest cardinality, then
    the lexicographically smallest sorted tuple of module names. This is the same
    deterministic ordering one would obtain from a min-cost ILP with a fixed
    lexicographic secondary objective; it matches the brute-force reference's
    ``(cost, len, sorted-names)`` key so the two exact methods agree on ties.
    """
    names = tuple(sorted(subset))
    return (_subset_cost(names, registry), len(names), names)


def solve_min_cost_harness(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
) -> IndependentSolution:
    """Solve the minimum-cost valid harness for ``profile`` over ``registry``.

    This is the independent counterpart to ``compile_minimal_harness``. It
    returns the same notion of validity and the same status taxonomy, computed
    by increasing-cost ILP enumeration rather than dominance-pruned
    branch-and-bound.
    """
    # Clarify short-circuit, mirroring the profiler contract.
    if CLARIFY_MARKER in tuple(profile.unsupported_possibility):
        return IndependentSolution(
            status="clarify",
            modules=(),
            cost=0,
            obligations=ordered(profile.obligations),
            capabilities=ordered(profile.required_capabilities),
        )

    required_obligations = frozenset(profile.obligations)
    required_capabilities = frozenset(profile.required_capabilities)

    # Direct-answer case: nothing required.
    if not required_obligations and not required_capabilities:
        return IndependentSolution(
            status="supported",
            modules=(),
            cost=0,
            obligations=(),
            capabilities=(),
        )

    pool = _pool_modules(registry)

    # Cheap infeasibility certificate: if the union of everything still fails to
    # cover a required obligation/capability, no subset can. (The compiler emits
    # the same missing-* lists; we recompute them independently.)
    all_obs = _provided_obligations(pool, registry)
    all_caps = _provided_capabilities(pool, registry)
    missing_obligations = ordered(required_obligations - all_obs)
    missing_capabilities = ordered(required_capabilities - all_caps)

    best: Optional[Tuple[str, ...]] = None
    best_key: Optional[Tuple[int, int, Tuple[str, ...]]] = None
    candidates_enumerated = 0
    feasible_found = 0

    if not missing_obligations and not missing_capabilities:
        # Enumerate subsets ordered by their tie-break key, which sorts by total
        # cost first. We materialise all subsets, attach their key, and walk in
        # increasing-cost order; the first feasible subset is a certified
        # optimum. The pool is small (<= ~10 modules) so full enumeration is
        # cheap and keeps the proof of optimality fully explicit. We continue
        # within the same minimum-cost tier to apply the deterministic tie-break
        # independently of enumeration order.
        keyed: List[Tuple[Tuple[int, int, Tuple[str, ...]], Tuple[str, ...]]] = []
        for size in range(len(pool) + 1):
            for combo in combinations(pool, size):
                keyed.append((_tie_break_key(combo, registry), combo))
        keyed.sort(key=lambda item: item[0])

        for key, combo in keyed:
            candidates_enumerated += 1
            # Prune: once we have an optimum, no strictly higher cost can win.
            if best_key is not None and key[0] > best_key[0]:
                break
            if _is_feasible(combo, required_obligations, required_capabilities, registry):
                feasible_found += 1
                if best_key is None or key < best_key:
                    best = tuple(sorted(combo))
                    best_key = key

    if best is None:
        return IndependentSolution(
            status="unsupported",
            modules=(),
            cost=0,
            obligations=ordered(required_obligations),
            capabilities=ordered(required_capabilities),
            missing_obligations=missing_obligations,
            missing_capabilities=missing_capabilities,
            candidates_enumerated=candidates_enumerated,
            feasible_found=feasible_found,
        )

    return IndependentSolution(
        status="supported",
        modules=best,
        cost=_subset_cost(best, registry),
        obligations=ordered(_provided_obligations(best, registry)),
        capabilities=ordered(_provided_capabilities(best, registry)),
        candidates_enumerated=candidates_enumerated,
        feasible_found=feasible_found,
    )


def independent_oracle(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
) -> IndependentSolution:
    """Public alias for :func:`solve_min_cost_harness`."""
    return solve_min_cost_harness(profile, registry)
