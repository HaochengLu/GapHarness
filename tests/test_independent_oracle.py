"""Tests for the independent minimum-cost harness solver.

These tests turn "compiler == oracle" into a real cross-check: the independent
solver (``gapharness.independent_oracle``) re-derives the minimum-cost valid
harness with a different algorithm and an independent validity predicate, then
we assert it agrees with ``compile_minimal_harness`` on COST. Module sets may
differ on ties, so we assert cost equality (not necessarily set equality) plus
the optimality invariant that the compiler's cost is <= any valid subset's cost.
"""

from __future__ import annotations

import random
import unittest
from itertools import combinations
from typing import FrozenSet, Mapping, Sequence

from gapharness.compiler import compile_minimal_harness
from gapharness.independent_oracle import (
    EXCLUDED_FROM_POOL,
    independent_oracle,
    solve_min_cost_harness,
)
from gapharness.registry import default_registry
from gapharness.schema import ModuleSpec, ProfilerOutput, frozen


def _all_obligations(registry: Mapping[str, ModuleSpec]) -> FrozenSet[str]:
    out: set = set()
    for module in registry.values():
        out.update(module.provides)
    return frozenset(out)


def _all_capabilities(registry: Mapping[str, ModuleSpec]) -> FrozenSet[str]:
    out: set = set()
    for module in registry.values():
        out.update(module.capabilities)
    return frozenset(out)


def _independent_valid(
    subset: Sequence[str],
    req_obs: FrozenSet[str],
    req_caps: FrozenSet[str],
    registry: Mapping[str, ModuleSpec],
) -> bool:
    """Reference validity predicate, re-implemented locally for the test."""
    provided_obs: set = set()
    provided_caps: set = set()
    for name in subset:
        provided_obs.update(registry[name].provides)
        provided_caps.update(registry[name].capabilities)
    if not req_obs <= provided_obs:
        return False
    if not req_caps <= provided_caps:
        return False
    for name in subset:
        module = registry[name]
        if not set(module.requires_obligations) <= provided_obs:
            return False
        if not set(module.requires_capabilities) <= provided_caps:
            return False
    return True


def _min_valid_cost(
    req_obs: FrozenSet[str],
    req_caps: FrozenSet[str],
    registry: Mapping[str, ModuleSpec],
):
    """Brute reference: minimum cost over all valid subsets, or None if none."""
    pool = sorted(name for name in registry if name not in EXCLUDED_FROM_POOL)
    best = None
    for size in range(len(pool) + 1):
        for combo in combinations(pool, size):
            if _independent_valid(combo, req_obs, req_caps, registry):
                cost = sum(registry[name].cost for name in combo)
                if best is None or cost < best:
                    best = cost
    return best


class IndependentOracleHandCases(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = default_registry()

    def test_direct_answer_empty_profile(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=True,
            obligations=frozen([]),
            required_capabilities=frozen([]),
        )
        compiled = compile_minimal_harness(profile, self.registry)
        solved = independent_oracle(profile, self.registry)
        self.assertEqual(solved.status, "supported")
        self.assertEqual(solved.modules, ())
        self.assertEqual(solved.cost, 0)
        self.assertEqual(compiled.cost, solved.cost)

    def test_sandbox_action_dependency_case(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "State", "Verification"]),
            required_capabilities=frozen(["diff", "contract_check"]),
        )
        compiled = compile_minimal_harness(profile, self.registry)
        solved = independent_oracle(profile, self.registry)
        self.assertEqual(compiled.status, "supported")
        self.assertEqual(solved.status, "supported")
        # The dependency on permission must be pulled in independently.
        self.assertIn("permission_gate", solved.modules)
        self.assertIn("sandbox_file_editor", solved.modules)
        self.assertEqual(compiled.cost, solved.cost)

    def test_full_obligation_capability_case(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(
                ["Action", "Control", "Execution", "Observation", "State", "Verification"]
            ),
            required_capabilities=frozen(
                [
                    "workspace_inspection",
                    "execution",
                    "execution_log",
                    "durable_state",
                    "diff",
                    "sandbox_action",
                    "permission",
                    "contract_check",
                ]
            ),
        )
        compiled = compile_minimal_harness(profile, self.registry)
        solved = independent_oracle(profile, self.registry)
        self.assertEqual(compiled.status, "supported")
        self.assertEqual(solved.status, "supported")
        self.assertEqual(compiled.cost, solved.cost)
        self.assertEqual(tuple(sorted(compiled.modules)), solved.modules)

    def test_unsupported_missing_capability(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "Control"]),
            required_capabilities=frozen(["real_world_side_effect"]),
        )
        compiled = compile_minimal_harness(profile, self.registry)
        solved = independent_oracle(profile, self.registry)
        self.assertEqual(compiled.status, "unsupported")
        self.assertEqual(solved.status, "unsupported")
        self.assertIn("real_world_side_effect", solved.missing_capabilities)
        self.assertEqual(compiled.cost, solved.cost)

    def test_clarify_short_circuit(self):
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Action", "Control", "Verification"]),
            required_capabilities=frozen(["permission", "diff", "contract_check"]),
            unsupported_possibility=("clarification_needed",),
        )
        compiled = compile_minimal_harness(profile, self.registry)
        solved = independent_oracle(profile, self.registry)
        self.assertEqual(compiled.status, "clarify")
        self.assertEqual(solved.status, "clarify")
        self.assertEqual(solved.modules, ())
        self.assertEqual(compiled.cost, solved.cost)

    def test_trace_recorder_excluded_from_pool(self):
        # trace_recorder provides no obligations; it must never be selected.
        profile = ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozen(["Observation"]),
            required_capabilities=frozen(["evidence_sources"]),
        )
        solved = independent_oracle(profile, self.registry)
        self.assertNotIn("trace_recorder", solved.modules)
        self.assertIn("trace_recorder", EXCLUDED_FROM_POOL)


class IndependentOracleFuzz(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = default_registry()
        self.all_obligations = sorted(_all_obligations(self.registry))
        # Capabilities the registry can actually provide, plus one impossible
        # capability so some random profiles land in the unsupported region.
        self.providable_caps = sorted(_all_capabilities(self.registry))
        self.extra_caps = ["real_world_side_effect"]

    def _random_profile(self, rng: random.Random) -> ProfilerOutput:
        n_obs = rng.randint(0, len(self.all_obligations))
        obs = rng.sample(self.all_obligations, n_obs)
        cap_pool = self.providable_caps + (
            self.extra_caps if rng.random() < 0.15 else []
        )
        n_caps = rng.randint(0, len(cap_pool))
        caps = rng.sample(cap_pool, n_caps)
        return ProfilerOutput(
            direct_llm_sufficient=not obs and not caps,
            obligations=frozen(obs),
            required_capabilities=frozen(caps),
        )

    def test_fuzz_cost_agreement(self):
        rng = random.Random(20260624)
        n_samples = 300
        supported_seen = 0
        unsupported_seen = 0
        for _ in range(n_samples):
            profile = self._random_profile(rng)
            compiled = compile_minimal_harness(profile, self.registry)
            solved = solve_min_cost_harness(profile, self.registry)

            # Status must agree between the two independent methods.
            self.assertEqual(
                compiled.status,
                solved.status,
                msg="status mismatch for obligations=%s caps=%s"
                % (sorted(profile.obligations), sorted(profile.required_capabilities)),
            )

            # Cost must agree (module sets may differ on ties).
            self.assertEqual(
                compiled.cost,
                solved.cost,
                msg="cost mismatch for obligations=%s caps=%s: compiler=%s vs independent=%s"
                % (
                    sorted(profile.obligations),
                    sorted(profile.required_capabilities),
                    list(compiled.modules),
                    list(solved.modules),
                ),
            )

            if compiled.status == "supported":
                supported_seen += 1
                req_obs = frozenset(profile.obligations)
                req_caps = frozenset(profile.required_capabilities)
                # Optimality invariant: compiler cost <= any valid subset cost.
                ref_min = _min_valid_cost(req_obs, req_caps, self.registry)
                self.assertIsNotNone(ref_min)
                self.assertLessEqual(compiled.cost, ref_min)
                self.assertEqual(compiled.cost, ref_min)
                # The independently selected subset is itself valid.
                self.assertTrue(
                    _independent_valid(solved.modules, req_obs, req_caps, self.registry)
                )
            elif compiled.status == "unsupported":
                unsupported_seen += 1

        # Sanity: the fuzz actually exercised both branches and >= 200 samples.
        self.assertGreaterEqual(n_samples, 200)
        self.assertGreater(supported_seen, 0)
        self.assertGreater(unsupported_seen, 0)

    def test_independent_subset_is_minimal_over_random_registries(self):
        # Build small random registries and confirm the solver returns a true
        # minimum-cost cover (independent of the production registry's shape).
        rng = random.Random(7)
        obligations_universe = ["O1", "O2", "O3"]
        caps_universe = ["c1", "c2", "c3"]
        for trial in range(40):
            registry = {}
            n_modules = rng.randint(2, 5)
            for i in range(n_modules):
                provides = frozen(
                    rng.sample(
                        obligations_universe, rng.randint(0, len(obligations_universe))
                    )
                )
                caps = frozen(
                    rng.sample(caps_universe, rng.randint(0, len(caps_universe)))
                )
                registry["m%d" % i] = ModuleSpec(
                    name="m%d" % i,
                    provides=provides,
                    capabilities=caps,
                    cost=rng.randint(1, 5),
                )
            req_obs = frozen(
                rng.sample(obligations_universe, rng.randint(0, len(obligations_universe)))
            )
            req_caps = frozen(rng.sample(caps_universe, rng.randint(0, len(caps_universe))))
            profile = ProfilerOutput(
                direct_llm_sufficient=not req_obs and not req_caps,
                obligations=req_obs,
                required_capabilities=req_caps,
            )
            solved = solve_min_cost_harness(profile, registry)
            ref_min = _min_valid_cost(
                frozenset(req_obs), frozenset(req_caps), registry
            )
            if ref_min is None:
                self.assertEqual(solved.status, "unsupported")
            else:
                self.assertEqual(solved.status, "supported")
                self.assertEqual(solved.cost, ref_min)
                self.assertTrue(
                    _independent_valid(
                        solved.modules,
                        frozenset(req_obs),
                        frozenset(req_caps),
                        registry,
                    )
                )


if __name__ == "__main__":
    unittest.main()
