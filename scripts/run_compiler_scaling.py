"""Synthetic registry scaling for the exact optimizing compiler."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.compiler import compile_minimal_harness, compile_minimal_harness_bruteforce
from gapharness.schema import ModuleSpec, ProfilerOutput, frozen


OBLIGATION_BY_INDEX = ("Observation", "Execution", "State", "Action", "Control", "Verification")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", default="10,20,40,80,160")
    parser.add_argument("--hard-sizes", default="20,30,40")
    parser.add_argument("--out-dir", default="outputs/final/compiler_scaling")
    parser.add_argument("--bruteforce-max-size", type=int, default=20)
    parser.add_argument("--hard-bruteforce-max-size", type=int, default=20)
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes = [int(item) for item in args.sizes.split(",") if item.strip()]
    rows = [run_size(size, args.bruteforce_max_size) for size in sizes]
    write_jsonl(out_dir / "scaling_results.jsonl", rows)
    hard_sizes = [int(item) for item in args.hard_sizes.split(",") if item.strip()]
    hard_rows = [run_hard_size(size, args.hard_bruteforce_max_size) for size in hard_sizes]
    write_jsonl(out_dir / "non_dominated_scaling_results.jsonl", hard_rows)
    (out_dir / "scaling_report.md").write_text(render_report(rows, hard_rows), encoding="utf-8")
    print("wrote compiler scaling experiment to %s" % out_dir)
    return 0


def run_size(size: int, bruteforce_max_size: int) -> Mapping[str, object]:
    registry = synthetic_registry(size)
    profile = synthetic_profile()

    start = time.perf_counter()
    optimized = compile_minimal_harness(profile, registry, strategy="optimized")
    optimized_time = time.perf_counter() - start
    cert = optimized.certificate
    greedy_modules, greedy_cost = greedy_cover(profile, registry)

    row = {
        "registry_size": size,
        "required_obligations": sorted(profile.obligations),
        "required_capabilities": sorted(profile.required_capabilities),
        "optimized_status": optimized.status,
        "optimized_cost": optimized.cost,
        "optimized_modules": list(optimized.modules),
        "optimized_time_ms": optimized_time * 1000.0,
        "optimized_nodes_visited": cert.get("search_stats", {}).get("nodes_visited", 0),
        "optimized_validity_checks": cert.get("search_stats", {}).get("candidate_validity_checks", 0),
        "optimized_pruned_by_cost": cert.get("search_stats", {}).get("branches_pruned_by_cost", 0),
        "optimized_pruned_by_coverage": cert.get("search_stats", {}).get("branches_pruned_by_coverage", 0),
        "dominated_modules_removed": cert.get("dominated_module_count", 0),
        "greedy_cost": greedy_cost,
        "greedy_modules": list(greedy_modules),
        "bruteforce_run": size <= bruteforce_max_size,
    }
    if size <= bruteforce_max_size:
        start = time.perf_counter()
        brute = compile_minimal_harness_bruteforce(profile, registry)
        brute_time = time.perf_counter() - start
        brute_stats = brute.certificate.get("search_stats", {})
        row.update(
            {
                "bruteforce_status": brute.status,
                "bruteforce_cost": brute.cost,
                "bruteforce_modules": list(brute.modules),
                "bruteforce_time_ms": brute_time * 1000.0,
                "bruteforce_candidates_evaluated": brute_stats.get("candidates_evaluated", 0),
                "same_optimal_cost": brute.cost == optimized.cost,
                "same_selected_modules": list(brute.modules) == list(optimized.modules),
            }
        )
    else:
        row.update(
            {
                "bruteforce_status": "skipped_exponential",
                "bruteforce_cost": None,
                "bruteforce_modules": [],
                "bruteforce_time_ms": None,
                "bruteforce_candidates_evaluated": "2^%d skipped" % size,
                "same_optimal_cost": None,
                "same_selected_modules": None,
            }
        )
    return row


def run_hard_size(size: int, bruteforce_max_size: int) -> Mapping[str, object]:
    registry = non_dominated_registry(size)
    profile = hard_profile()

    start = time.perf_counter()
    optimized = compile_minimal_harness(profile, registry, strategy="optimized")
    optimized_time = time.perf_counter() - start
    cert = optimized.certificate
    greedy_modules, greedy_cost = greedy_cover(profile, registry)

    row = {
        "registry_size": size,
        "setting": "mostly_non_dominated_overlap",
        "required_obligations": sorted(profile.obligations),
        "required_capabilities": sorted(profile.required_capabilities),
        "optimized_status": optimized.status,
        "optimized_cost": optimized.cost,
        "optimized_modules": list(optimized.modules),
        "optimized_time_ms": optimized_time * 1000.0,
        "optimized_nodes_visited": cert.get("search_stats", {}).get("nodes_visited", 0),
        "optimized_validity_checks": cert.get("search_stats", {}).get("candidate_validity_checks", 0),
        "optimized_pruned_by_cost": cert.get("search_stats", {}).get("branches_pruned_by_cost", 0),
        "optimized_pruned_by_coverage": cert.get("search_stats", {}).get("branches_pruned_by_coverage", 0),
        "dominated_modules_removed": cert.get("dominated_module_count", 0),
        "greedy_cost": greedy_cost,
        "greedy_modules": list(greedy_modules),
        "bruteforce_run": size <= bruteforce_max_size,
    }
    if size <= bruteforce_max_size:
        start = time.perf_counter()
        brute = compile_minimal_harness_bruteforce(profile, registry)
        brute_time = time.perf_counter() - start
        brute_stats = brute.certificate.get("search_stats", {})
        row.update(
            {
                "bruteforce_status": brute.status,
                "bruteforce_cost": brute.cost,
                "bruteforce_modules": list(brute.modules),
                "bruteforce_time_ms": brute_time * 1000.0,
                "bruteforce_candidates_evaluated": brute_stats.get("candidates_evaluated", 0),
                "same_optimal_cost": brute.cost == optimized.cost,
                "same_selected_modules": list(brute.modules) == list(optimized.modules),
            }
        )
    else:
        row.update(
            {
                "bruteforce_status": "skipped_exponential",
                "bruteforce_cost": None,
                "bruteforce_modules": [],
                "bruteforce_time_ms": None,
                "bruteforce_candidates_evaluated": "2^%d skipped" % size,
                "same_optimal_cost": None,
                "same_selected_modules": None,
            }
        )
    return row


def synthetic_profile() -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=False,
        obligations=frozen(OBLIGATION_BY_INDEX),
        required_capabilities=frozen("cap_%d" % idx for idx in range(6)),
        output_contract={"synthetic_scaling": True},
        risk_level="medium",
        rationale="Synthetic registry scaling profile.",
    )


def synthetic_registry(size: int) -> dict[str, ModuleSpec]:
    if size < 10:
        raise ValueError("Synthetic scaling registry size must be >= 10.")
    modules: list[ModuleSpec] = []
    for idx, obligation in enumerate(OBLIGATION_BY_INDEX):
        modules.append(
            ModuleSpec(
                name="atomic_%02d" % idx,
                provides=frozen([obligation]),
                capabilities=frozen(["cap_%d" % idx]),
                cost=2,
                verifier="synthetic_atomic",
            )
        )
    pair_specs = ((0, 1), (2, 3), (4, 5))
    for idx, pair in enumerate(pair_specs):
        modules.append(
            ModuleSpec(
                name="pair_%02d" % idx,
                provides=frozen(OBLIGATION_BY_INDEX[item] for item in pair),
                capabilities=frozen("cap_%d" % item for item in pair),
                cost=3,
                verifier="synthetic_pair",
            )
        )
    fill_index = 0
    while len(modules) < size:
        base = fill_index % 6
        modules.append(
            ModuleSpec(
                name="dominated_%03d" % fill_index,
                provides=frozen([OBLIGATION_BY_INDEX[base]]),
                capabilities=frozen(["cap_%d" % base]),
                cost=4 + (fill_index % 3),
                verifier="synthetic_dominated",
            )
        )
        fill_index += 1
    return {module.name: module for module in modules[:size]}


def hard_profile() -> ProfilerOutput:
    return ProfilerOutput(
        direct_llm_sufficient=False,
        obligations=frozen(OBLIGATION_BY_INDEX),
        required_capabilities=frozen("hard_cap_%d" % idx for idx in range(8)),
        output_contract={"non_dominated_scaling": True},
        risk_level="medium",
        rationale="Synthetic mostly non-dominated exact-cover stress profile.",
    )


def non_dominated_registry(size: int) -> dict[str, ModuleSpec]:
    if size < 12:
        raise ValueError("Non-dominated scaling registry size must be >= 12.")
    modules: list[ModuleSpec] = []
    for idx in range(8):
        modules.append(
            ModuleSpec(
                name="hard_single_%02d" % idx,
                provides=frozen([OBLIGATION_BY_INDEX[idx % len(OBLIGATION_BY_INDEX)]]),
                capabilities=frozen(["hard_cap_%d" % idx]),
                cost=2,
                verifier="synthetic_hard_single",
            )
        )
    pair_index = 0
    for left in range(8):
        for right in range(left + 1, 8):
            modules.append(
                ModuleSpec(
                    name="hard_pair_%02d_%02d" % (left, right),
                    provides=frozen([OBLIGATION_BY_INDEX[left % len(OBLIGATION_BY_INDEX)], OBLIGATION_BY_INDEX[right % len(OBLIGATION_BY_INDEX)]]),
                    capabilities=frozen(["hard_cap_%d" % left, "hard_cap_%d" % right]),
                    cost=4,
                    verifier="synthetic_hard_pair",
                )
            )
            pair_index += 1
            if len(modules) >= size:
                return {module.name: module for module in modules[:size]}
    triple_index = 0
    while len(modules) < size:
        a = triple_index % 8
        b = (triple_index + 3) % 8
        c = (triple_index + 5) % 8
        modules.append(
            ModuleSpec(
                name="hard_triple_%02d" % triple_index,
                provides=frozen([OBLIGATION_BY_INDEX[a % len(OBLIGATION_BY_INDEX)], OBLIGATION_BY_INDEX[b % len(OBLIGATION_BY_INDEX)], OBLIGATION_BY_INDEX[c % len(OBLIGATION_BY_INDEX)]]),
                capabilities=frozen(["hard_cap_%d" % a, "hard_cap_%d" % b, "hard_cap_%d" % c]),
                cost=7,
                verifier="synthetic_hard_triple",
            )
        )
        triple_index += 1
    return {module.name: module for module in modules[:size]}


def greedy_cover(profile: ProfilerOutput, registry: Mapping[str, ModuleSpec]) -> tuple[tuple[str, ...], int | None]:
    required_obligations = set(profile.obligations)
    required_capabilities = set(profile.required_capabilities)
    selected: list[str] = []
    remaining = set(registry)
    covered_obligations: set[str] = set()
    covered_capabilities: set[str] = set()
    while not required_obligations.issubset(covered_obligations) or not required_capabilities.issubset(covered_capabilities):
        best_name = None
        best_key = None
        for name in sorted(remaining):
            if name == "trace_recorder":
                continue
            module = registry[name]
            new_obligations = set(module.provides) - covered_obligations
            new_capabilities = set(module.capabilities) - covered_capabilities
            gain = len(new_obligations & required_obligations) + len(new_capabilities & required_capabilities)
            if gain <= 0:
                continue
            key = (float(module.cost) / float(gain), module.cost, name)
            if best_key is None or key < best_key:
                best_name = name
                best_key = key
        if best_name is None:
            return tuple(selected), None
        selected.append(best_name)
        remaining.remove(best_name)
        covered_obligations.update(registry[best_name].provides)
        covered_capabilities.update(registry[best_name].capabilities)
    return tuple(sorted(selected)), sum(registry[name].cost for name in selected)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def render_report(rows: Sequence[Mapping[str, object]], hard_rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# Synthetic Registry Scaling",
        "",
        "The optimized compiler remains exact. Dominance pruning removes strictly dominated modules, and branch-and-bound prunes branches that cannot cover the profile or cannot beat the current best cost. Naive brute force is run only where feasible.",
        "",
        "| Registry | Brute run | Brute candidates | Brute ms | Opt ms | Opt nodes | Dominated | Same cost | Greedy cost | Opt cost |",
        "|---:|---|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {registry_size} | {bruteforce_run} | {bruteforce_candidates_evaluated} | {brute_ms} | {optimized_time_ms:.2f} | {optimized_nodes_visited} | {dominated_modules_removed} | {same_optimal_cost} | {greedy_cost} | {optimized_cost} |".format(
                brute_ms=fmt_optional(row.get("bruteforce_time_ms")),
                **row,
            )
        )
    lines.extend(
        [
            "",
            "Worst-case exact search remains exponential. The point of this experiment is narrower: for declared agent registries with many redundant or dominated affordance declarations, exact compilation can remain practical while preserving the same optimum as brute force on feasible sizes.",
            "",
            "## Mostly Non-Dominated Stress",
            "",
            "This secondary stress uses overlapping modules that are intentionally much less dominance-prunable. It is a boundary diagnostic, not a performance claim.",
            "",
            "| Registry | Brute run | Brute candidates | Brute ms | Opt ms | Opt nodes | Dominated | Same cost | Greedy cost | Opt cost |",
            "|---:|---|---:|---:|---:|---:|---:|---|---:|---:|",
        ]
    )
    for row in hard_rows:
        lines.append(
            "| {registry_size} | {bruteforce_run} | {bruteforce_candidates_evaluated} | {brute_ms} | {optimized_time_ms:.2f} | {optimized_nodes_visited} | {dominated_modules_removed} | {same_optimal_cost} | {greedy_cost} | {optimized_cost} |".format(
                brute_ms=fmt_optional(row.get("bruteforce_time_ms")),
                **row,
            )
        )
    lines.append("")
    return "\n".join(lines)


def fmt_optional(value: object) -> str:
    if value is None:
        return "-"
    return "%.2f" % float(value)


if __name__ == "__main__":
    raise SystemExit(main())
