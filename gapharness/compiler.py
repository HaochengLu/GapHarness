"""Exact minimal harness compiler.

The public compiler remains exact: optimizations only prune modules or search
branches that cannot improve a minimum-cost valid harness under the declared
registry. A brute-force entrypoint is kept for regression and scaling studies.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .registry import provided_capabilities, provided_obligations, total_cost
from .schema import CompiledHarness, ModuleSpec, ProfilerOutput, ordered


def compile_minimal_harness(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
    include_trace_recorder: bool = False,
    strategy: str = "optimized",
) -> CompiledHarness:
    if strategy == "bruteforce":
        return compile_minimal_harness_bruteforce(profile, registry, include_trace_recorder=include_trace_recorder)
    if strategy != "optimized":
        raise ValueError("Unknown compiler strategy: %s" % strategy)

    if "clarification_needed" in profile.unsupported_possibility:
        return CompiledHarness(
            status="clarify",
            modules=(),
            obligations=profile.obligations,
            capabilities=profile.required_capabilities,
            cost=0,
            loop_template="unsupported_or_clarify",
            reason="Profiler marked the query as needing clarification.",
            certificate=base_certificate(
                profile,
                registry,
                algorithm="dominance_pruned_branch_and_bound",
                extra={"termination": "clarification_needed"},
            ),
        )

    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)

    if not required_obligations and not required_capabilities:
        return CompiledHarness(
            status="supported",
            modules=(),
            obligations=frozenset(),
            capabilities=frozenset(),
            cost=0,
            loop_template="direct_answer",
            reason="Direct LLM answer is sufficient under the profiler contract.",
            certificate=base_certificate(
                profile,
                registry,
                algorithm="dominance_pruned_branch_and_bound",
                extra={"termination": "direct_answer", "dependencies_satisfied": True},
            ),
        )

    module_names = [name for name in sorted(registry) if name != "trace_recorder"]
    active_names, dominated = dominance_prune(module_names, registry)
    best, stats = branch_and_bound_search(active_names, required_obligations, required_capabilities, registry)

    if best is None:
        all_obligations = provided_obligations(module_names, registry)
        all_capabilities = provided_capabilities(module_names, registry)
        missing_obligations = ordered(required_obligations - set(all_obligations))
        missing_capabilities = ordered(required_capabilities - set(all_capabilities))
        return CompiledHarness(
            status="unsupported",
            modules=(),
            obligations=frozenset(required_obligations),
            capabilities=frozenset(required_capabilities),
            cost=0,
            loop_template="unsupported_or_clarify",
            missing_obligations=missing_obligations,
            missing_capabilities=missing_capabilities,
            reason="No registry subset covers the required obligations and capabilities.",
            certificate=base_certificate(
                profile,
                registry,
                algorithm="dominance_pruned_branch_and_bound",
                dominated=dominated,
                stats=stats,
                extra={
                    "termination": "unsupported",
                    "missing_obligations": list(missing_obligations),
                    "missing_capabilities": list(missing_capabilities),
                    "active_module_count": len(active_names),
                },
            ),
        )

    if include_trace_recorder and "trace_recorder" in registry:
        best = tuple(sorted(set(best) | {"trace_recorder"}))

    obligations = provided_obligations(best, registry)
    capabilities = provided_capabilities(best, registry)
    return CompiledHarness(
        status="supported",
        modules=tuple(sorted(best)),
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(best, registry),
        loop_template=choose_loop_template(obligations, capabilities),
        reason="Dominance-pruned branch-and-bound exact search found the lowest-cost sufficient module subset.",
        certificate=build_certificate(
            profile,
            registry,
            best,
            algorithm="dominance_pruned_branch_and_bound",
            dominated=dominated,
            stats=stats,
            active_module_count=len(active_names),
        ),
    )


def compile_minimal_harness_bruteforce(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
    include_trace_recorder: bool = False,
) -> CompiledHarness:
    if "clarification_needed" in profile.unsupported_possibility:
        return CompiledHarness(
            status="clarify",
            modules=(),
            obligations=profile.obligations,
            capabilities=profile.required_capabilities,
            cost=0,
            loop_template="unsupported_or_clarify",
            reason="Profiler marked the query as needing clarification.",
            certificate=base_certificate(profile, registry, algorithm="bruteforce_exact", extra={"termination": "clarification_needed"}),
        )

    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)
    if not required_obligations and not required_capabilities:
        return CompiledHarness(
            status="supported",
            modules=(),
            obligations=frozenset(),
            capabilities=frozenset(),
            cost=0,
            loop_template="direct_answer",
            reason="Direct LLM answer is sufficient under the profiler contract.",
            certificate=base_certificate(profile, registry, algorithm="bruteforce_exact", extra={"termination": "direct_answer"}),
        )

    module_names = [name for name in sorted(registry) if name != "trace_recorder"]
    valid = []
    candidates_evaluated = 0
    for candidate in _powerset(module_names):
        candidates_evaluated += 1
        if _candidate_valid(candidate, required_obligations, required_capabilities, registry):
            valid.append(candidate)

    if not valid:
        all_obligations = provided_obligations(module_names, registry)
        all_capabilities = provided_capabilities(module_names, registry)
        missing_obligations = ordered(required_obligations - set(all_obligations))
        missing_capabilities = ordered(required_capabilities - set(all_capabilities))
        return CompiledHarness(
            status="unsupported",
            modules=(),
            obligations=frozenset(required_obligations),
            capabilities=frozenset(required_capabilities),
            cost=0,
            loop_template="unsupported_or_clarify",
            missing_obligations=missing_obligations,
            missing_capabilities=missing_capabilities,
            reason="No registry subset covers the required obligations and capabilities.",
            certificate=base_certificate(
                profile,
                registry,
                algorithm="bruteforce_exact",
                stats={"candidates_evaluated": candidates_evaluated, "valid_candidates": 0},
                extra={"termination": "unsupported", "missing_obligations": list(missing_obligations), "missing_capabilities": list(missing_capabilities)},
            ),
        )

    best = min(valid, key=lambda names: (total_cost(names, registry), len(names), tuple(sorted(names))))
    if include_trace_recorder and "trace_recorder" in registry:
        best = tuple(sorted(set(best) | {"trace_recorder"}))
    obligations = provided_obligations(best, registry)
    capabilities = provided_capabilities(best, registry)
    return CompiledHarness(
        status="supported",
        modules=tuple(sorted(best)),
        obligations=obligations,
        capabilities=capabilities,
        cost=total_cost(best, registry),
        loop_template=choose_loop_template(obligations, capabilities),
        reason="Brute-force exact search found the lowest-cost sufficient module subset.",
        certificate=build_certificate(
            profile,
            registry,
            best,
            algorithm="bruteforce_exact",
            stats={"candidates_evaluated": candidates_evaluated, "valid_candidates": len(valid)},
            active_module_count=len(module_names),
        ),
    )


def dominance_prune(
    module_names: Sequence[str],
    registry: Mapping[str, ModuleSpec],
) -> Tuple[Tuple[str, ...], Tuple[Mapping[str, object], ...]]:
    removed = []
    active = []
    for name in module_names:
        dominator = first_dominator(name, module_names, registry)
        if dominator is None:
            active.append(name)
        else:
            removed.append(
                {
                    "removed": name,
                    "dominated_by": dominator,
                    "reason": "dominator covers a superset of obligations/capabilities with no stricter dependencies and tie-safe cost.",
                }
            )
    return tuple(active), tuple(removed)


def first_dominator(
    module_name: str,
    module_names: Sequence[str],
    registry: Mapping[str, ModuleSpec],
) -> Optional[str]:
    for candidate in module_names:
        if candidate == module_name:
            continue
        if module_dominates(candidate, module_name, registry):
            return candidate
    return None


def module_dominates(
    left_name: str,
    right_name: str,
    registry: Mapping[str, ModuleSpec],
) -> bool:
    left = registry[left_name]
    right = registry[right_name]
    if not set(left.provides).issuperset(right.provides):
        return False
    if not set(left.capabilities).issuperset(right.capabilities):
        return False
    if not set(left.requires_obligations).issubset(right.requires_obligations):
        return False
    if not set(left.requires_capabilities).issubset(right.requires_capabilities):
        return False
    if left.cost > right.cost:
        return False
    # Tie-safe dominance preserves the deterministic brute-force tie-breaker.
    return left.cost < right.cost or left.name <= right.name


def branch_and_bound_search(
    module_names: Sequence[str],
    required_obligations: Iterable[str],
    required_capabilities: Iterable[str],
    registry: Mapping[str, ModuleSpec],
) -> Tuple[Optional[Tuple[str, ...]], Dict[str, int]]:
    names = tuple(sorted(module_names))
    req_obs = set(required_obligations)
    req_caps = set(required_capabilities)
    suffix_obligations, suffix_capabilities = suffix_coverage(names, registry)
    stats: Dict[str, int] = {
        "nodes_visited": 0,
        "candidate_validity_checks": 0,
        "branches_pruned_by_cost": 0,
        "branches_pruned_by_coverage": 0,
        "branches_pruned_after_valid": 0,
        "valid_candidates_seen": 0,
    }
    best: Optional[Tuple[str, ...]] = None
    best_key: Optional[Tuple[int, int, Tuple[str, ...]]] = None

    def dfs(index: int, selected: Tuple[str, ...], cost: int) -> None:
        nonlocal best, best_key
        stats["nodes_visited"] += 1

        if best_key is not None and cost > best_key[0]:
            stats["branches_pruned_by_cost"] += 1
            return

        future_obligations = set(provided_obligations(selected, registry)) | suffix_obligations[index]
        future_capabilities = set(provided_capabilities(selected, registry)) | suffix_capabilities[index]
        if not req_obs.issubset(future_obligations) or not req_caps.issubset(future_capabilities):
            stats["branches_pruned_by_coverage"] += 1
            return

        stats["candidate_validity_checks"] += 1
        if _candidate_valid(selected, req_obs, req_caps, registry):
            stats["valid_candidates_seen"] += 1
            key = (cost, len(selected), tuple(sorted(selected)))
            if best_key is None or key < best_key:
                best = tuple(sorted(selected))
                best_key = key
            stats["branches_pruned_after_valid"] += 1
            return

        if index >= len(names):
            return

        name = names[index]
        dfs(index + 1, tuple(sorted(selected + (name,))), cost + registry[name].cost)
        dfs(index + 1, selected, cost)

    dfs(0, (), 0)
    return best, stats


def suffix_coverage(
    module_names: Sequence[str],
    registry: Mapping[str, ModuleSpec],
) -> Tuple[List[set], List[set]]:
    suffix_obligations: List[set] = [set() for _ in range(len(module_names) + 1)]
    suffix_capabilities: List[set] = [set() for _ in range(len(module_names) + 1)]
    for index in range(len(module_names) - 1, -1, -1):
        module = registry[module_names[index]]
        suffix_obligations[index] = set(suffix_obligations[index + 1]) | set(module.provides)
        suffix_capabilities[index] = set(suffix_capabilities[index + 1]) | set(module.capabilities)
    return suffix_obligations, suffix_capabilities


def build_certificate(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
    selected: Sequence[str],
    algorithm: str,
    dominated: Sequence[Mapping[str, object]] = (),
    stats: Optional[Mapping[str, int]] = None,
    active_module_count: Optional[int] = None,
) -> Mapping[str, object]:
    selected_tuple = tuple(sorted(selected))
    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)
    covered_obligations = provided_obligations(selected_tuple, registry)
    covered_capabilities = provided_capabilities(selected_tuple, registry)
    dependency_failures = dependency_failures_for(selected_tuple, registry)
    missing_obligations = ordered(required_obligations - set(covered_obligations))
    missing_capabilities = ordered(required_capabilities - set(covered_capabilities))
    total = total_cost(selected_tuple, registry)
    cert: MutableMapping[str, object] = dict(
        base_certificate(
            profile,
            registry,
            algorithm=algorithm,
            dominated=dominated,
            stats=stats,
            extra={
                "termination": "supported",
                "active_module_count": active_module_count if active_module_count is not None else len(registry),
            },
        )
    )
    cert.update(
        {
            "selected_modules": list(selected_tuple),
            "covered_obligations": ordered(covered_obligations),
            "covered_capabilities": ordered(covered_capabilities),
            "total_cost": total,
            "dependencies_satisfied": not dependency_failures,
            "dependency_failures": dependency_failures,
            "missing_obligations": list(missing_obligations),
            "missing_capabilities": list(missing_capabilities),
            "minimality_certificate": {
                "lower_cost_candidate_examples": lower_cost_failure_examples(
                    profile,
                    registry,
                    max_cost=total,
                    limit=5,
                ),
                "drop_one_requires_failure_check": "see minimality_report.drop_one",
            },
        }
    )
    return dict(cert)


def base_certificate(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
    algorithm: str,
    dominated: Sequence[Mapping[str, object]] = (),
    stats: Optional[Mapping[str, int]] = None,
    extra: Optional[Mapping[str, object]] = None,
) -> Mapping[str, object]:
    payload: MutableMapping[str, object] = {
        "compiler_algorithm": algorithm,
        "registry_module_count": len([name for name in registry if name != "trace_recorder"]),
        "required_obligations": ordered(profile.obligations),
        "required_capabilities": ordered(profile.required_capabilities),
        "dominated_modules_removed": list(dominated),
        "dominated_module_count": len(dominated),
        "search_stats": dict(stats or {}),
    }
    if extra:
        payload.update(dict(extra))
    return dict(payload)


def dependency_failures_for(
    module_names: Sequence[str],
    registry: Mapping[str, ModuleSpec],
) -> List[Mapping[str, object]]:
    obligations = set(provided_obligations(module_names, registry))
    capabilities = set(provided_capabilities(module_names, registry))
    failures: List[Mapping[str, object]] = []
    for name in module_names:
        module = registry[name]
        missing_obligations = set(module.requires_obligations) - obligations
        missing_capabilities = set(module.requires_capabilities) - capabilities
        if missing_obligations or missing_capabilities:
            failures.append(
                {
                    "module": name,
                    "missing_obligations": sorted(missing_obligations),
                    "missing_capabilities": sorted(missing_capabilities),
                }
            )
    return failures


def lower_cost_failure_examples(
    profile: ProfilerOutput,
    registry: Mapping[str, ModuleSpec],
    max_cost: int,
    limit: int,
) -> List[Mapping[str, object]]:
    module_names = [name for name in sorted(registry) if name != "trace_recorder"]
    if len(module_names) > 20:
        return []
    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)
    examples: List[Mapping[str, object]] = []
    for candidate in _powerset(module_names):
        cost = total_cost(candidate, registry)
        if cost >= max_cost:
            continue
        if _candidate_valid(candidate, required_obligations, required_capabilities, registry):
            continue
        covered_obligations = set(provided_obligations(candidate, registry))
        covered_capabilities = set(provided_capabilities(candidate, registry))
        examples.append(
            {
                "candidate": list(candidate),
                "cost": cost,
                "missing_obligations": sorted(required_obligations - covered_obligations),
                "missing_capabilities": sorted(required_capabilities - covered_capabilities),
                "dependency_failures": dependency_failures_for(candidate, registry),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def _powerset(names: Sequence[str]) -> Iterator[Tuple[str, ...]]:
    for size in range(len(names) + 1):
        for combo in combinations(names, size):
            yield combo


def _candidate_valid(
    module_names: Iterable[str],
    required_obligations: Iterable[str],
    required_capabilities: Iterable[str],
    registry: Mapping[str, ModuleSpec],
) -> bool:
    names = tuple(module_names)
    obligations = set(provided_obligations(names, registry))
    capabilities = set(provided_capabilities(names, registry))
    if not set(required_obligations).issubset(obligations):
        return False
    if not set(required_capabilities).issubset(capabilities):
        return False
    for name in names:
        module = registry[name]
        if not set(module.requires_obligations).issubset(obligations):
            return False
        if not set(module.requires_capabilities).issubset(capabilities):
            return False
    return True


def choose_loop_template(obligations: Iterable[str], capabilities: Iterable[str]) -> str:
    obligation_set = set(obligations)
    capability_set = set(capabilities)
    if "Action" in obligation_set:
        if "permission" in capability_set:
            return "permission_act_verify"
        return "inspect_edit_verify"
    if "Observation" in obligation_set and "Execution" in obligation_set:
        return "retrieve_compute_verify"
    if "Execution" in obligation_set:
        return "compute_then_answer"
    if "Observation" in obligation_set:
        if "workspace_inspection" in capability_set:
            return "inspect_then_answer"
        return "retrieve_then_answer"
    if "State" in obligation_set:
        return "stateful_answer"
    if "Control" in obligation_set:
        return "permission_or_refusal"
    if "Verification" in obligation_set:
        return "verify_then_answer"
    return "direct_answer"
