"""Phase 2D stress tests for GapHarness paper evidence.

These tests are intentionally adversarial:
- registry perturbation verifies declared affordance boundaries,
- gold-label permutation verifies label semantics are not decorative,
- negative-control analysis verifies obligation sensitivity on pure/tool-bait tasks.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from gapharness.baselines import compile_for_system
from gapharness.compiler import compile_minimal_harness
from gapharness.evaluation import load_benchmark, load_results, row_metrics, summarize_results, write_jsonl
from gapharness.executor import execute_task
from gapharness.profiler import profile_from_gold
from gapharness.registry import default_registry
from gapharness.schema import ProfilerOutput, TaskExample, frozen


PERTURBATIONS: Tuple[Tuple[str, str, str], ...] = (
    ("remove_python_executor", "python_executor", "Execution subset"),
    ("remove_source_span_checker", "source_span_checker", "Observation + Verification subset"),
    ("remove_permission_gate", "permission_gate", "Action + Control subset"),
    ("remove_sandbox_file_editor", "sandbox_file_editor", "Action + Control subset"),
    ("remove_web_retrieval", "web_retrieval", "Observation + Verification subset"),
    ("remove_contract_verifier", "contract_verifier", "Verification subset"),
)

NEGATIVE_CATEGORIES = ("pure_language_negative", "tool_bait")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl")
    parser.add_argument("--out-dir", default="outputs/phase2d")
    parser.add_argument("--perturb-subset-size", type=int, default=60)
    parser.add_argument("--permutation-size", type=int, default=200)
    parser.add_argument(
        "command",
        choices=("all", "registry-perturbation", "gold-permutation", "negative-controls"),
        nargs="?",
        default="all",
    )
    args = parser.parse_args(argv)

    tasks = load_benchmark(args.benchmark)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.command in {"all", "registry-perturbation"}:
        run_registry_perturbation(tasks, out_dir / "registry_perturbation", args.perturb_subset_size)
    if args.command in {"all", "gold-permutation"}:
        run_gold_label_permutation(tasks, out_dir / "gold_label_permutation", args.permutation_size)
    if args.command in {"all", "negative-controls"}:
        run_negative_controls(tasks, out_dir / "negative_controls")
    write_phase2d_index(out_dir)
    return 0


def run_registry_perturbation(tasks: Sequence[TaskExample], out_dir: Path, subset_size: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    base_registry = default_registry()
    rows: List[Dict[str, object]] = []
    manifest: Dict[str, object] = {"subset_size": subset_size, "perturbations": []}

    for perturbation, removed_module, subset_label in PERTURBATIONS:
        subset = select_perturbation_subset(tasks, removed_module, subset_size)
        manifest["perturbations"].append(
            {
                "perturbation": perturbation,
                "removed_module": removed_module,
                "subset_label": subset_label,
                "n": len(subset),
                "task_ids": [task.task_id for task in subset],
            }
        )
        perturbed_registry = {name: spec for name, spec in base_registry.items() if name != removed_module}
        for task in subset:
            rows.append(evaluate_gold_with_registry(task, base_registry, perturbation, removed_module, "base_registry"))
            rows.append(evaluate_gold_with_registry(task, perturbed_registry, perturbation, removed_module, "perturbed_registry"))

    write_jsonl(str(out_dir / "results_registry_perturbation.jsonl"), rows)
    (out_dir / "subset_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir.parent / "registry_perturbation_report.md").write_text(
        render_registry_perturbation_report(rows),
        encoding="utf-8",
    )


def select_perturbation_subset(
    tasks: Sequence[TaskExample],
    removed_module: str,
    subset_size: int,
) -> List[TaskExample]:
    supported = [task for task in tasks if task.expected_status == "supported"]

    def has_cap(task: TaskExample, caps: Iterable[str]) -> bool:
        return bool(set(caps) & set(task.required_capabilities))

    if removed_module == "python_executor":
        selected = [task for task in supported if "Execution" in task.gold_obligations or has_cap(task, ("execution",))]
    elif removed_module == "source_span_checker":
        selected = [task for task in supported if has_cap(task, ("source_spans",)) or removed_module in task.oracle_minimal_harness]
    elif removed_module == "permission_gate":
        selected = [task for task in supported if has_cap(task, ("permission",)) or removed_module in task.oracle_minimal_harness]
    elif removed_module == "sandbox_file_editor":
        selected = [task for task in supported if has_cap(task, ("sandbox_action", "diff")) or removed_module in task.oracle_minimal_harness]
    elif removed_module == "web_retrieval":
        selected = [task for task in supported if has_cap(task, ("evidence_sources",)) or removed_module in task.oracle_minimal_harness]
    elif removed_module == "contract_verifier":
        selected = [task for task in supported if has_cap(task, ("contract_check",)) or removed_module in task.oracle_minimal_harness]
    else:
        raise ValueError(removed_module)
    return selected[:subset_size]


def evaluate_gold_with_registry(
    task: TaskExample,
    registry: Mapping[str, object],
    perturbation: str,
    removed_module: str,
    registry_condition: str,
) -> Dict[str, object]:
    profile = profile_from_gold(task)
    harness = compile_minimal_harness(profile, registry)
    result = execute_task(task, "gapharness_gold_%s" % registry_condition, "gold", harness, registry)
    row = result.to_json()
    row["task"] = task.to_json()
    row["profile"] = profile.to_json()
    row["perturbation"] = perturbation
    row["removed_module"] = removed_module
    row["registry_condition"] = registry_condition
    row["stress_metrics"] = registry_stress_metrics(task, row)
    return row


def registry_stress_metrics(task: TaskExample, row: Mapping[str, object]) -> Dict[str, object]:
    harness = row["harness"]
    status = str(harness["status"])
    verifier_failures = row.get("verifier_failures", [])
    supported_task = task.expected_status == "supported"
    return {
        "success": bool(row["verifier_passed"]),
        "unsupported": status == "unsupported",
        "clarify": status == "clarify",
        "under_covered": supported_task and not bool(row["verifier_passed"]),
        "verifier_fail": not bool(row["verifier_passed"]),
        "explicit_boundary_failure": status != "supported" or bool(verifier_failures),
        "missing_obligations": list(harness.get("missing_obligations", [])),
        "missing_capabilities": list(harness.get("missing_capabilities", [])),
        "verifier_failures": list(verifier_failures),
    }


def render_registry_perturbation_report(rows: Sequence[Mapping[str, object]]) -> str:
    buckets: Dict[Tuple[str, str], List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[(str(row["perturbation"]), str(row["registry_condition"]))].append(row)

    lines = [
        "# Phase 2D Stress Test 1: Registry Perturbation",
        "",
        "Registry perturbation verifies that GapHarness does not silently hallucinate support when required affordances are absent; it degrades into unsupported or under-covered status.",
        "",
        "| Perturbation | Removed Module | Condition | N | Success | Unsupported | Under-covered | Verifier Fail | Boundary Failure | Dominant Missing Capabilities |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for perturbation, removed_module, _label in PERTURBATIONS:
        for condition in ("base_registry", "perturbed_registry"):
            bucket = buckets[(perturbation, condition)]
            lines.append(
                "| %s | %s | %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %s |"
                % (
                    perturbation,
                    removed_module,
                    condition,
                    len(bucket),
                    mean(row["stress_metrics"]["success"] for row in bucket),
                    mean(row["stress_metrics"]["unsupported"] for row in bucket),
                    mean(row["stress_metrics"]["under_covered"] for row in bucket),
                    mean(row["stress_metrics"]["verifier_fail"] for row in bucket),
                    mean(row["stress_metrics"]["explicit_boundary_failure"] for row in bucket),
                    dominant_missing_capabilities(bucket),
                )
            )

    lines.extend(
        [
            "",
            "## Example Failures",
            "",
            "| Perturbation | Task | Status | Missing Capabilities | Verifier Failures | Query |",
            "|---|---|---|---|---|---|",
        ]
    )
    for perturbation, _removed_module, _label in PERTURBATIONS:
        examples = [
            row
            for row in rows
            if row["perturbation"] == perturbation
            and row["registry_condition"] == "perturbed_registry"
            and row["stress_metrics"]["explicit_boundary_failure"]
        ][:5]
        for row in examples:
            lines.append(
                "| %s | %s | %s | %s | %s | %s |"
                % (
                    perturbation,
                    row["task_id"],
                    row["harness"]["status"],
                    ",".join(row["stress_metrics"]["missing_capabilities"]) or "-",
                    ",".join(row["stress_metrics"]["verifier_failures"]) or "-",
                    trim(row["task"]["query"], 120),
                )
            )
    lines.append("")
    return "\n".join(lines)


def run_gold_label_permutation(tasks: Sequence[TaskExample], out_dir: Path, permutation_size: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    registry = default_registry()
    subset = [task for task in tasks if task.expected_status == "supported" and task.gold_obligations][:permutation_size]
    rows: List[Dict[str, object]] = []
    corrupted_profiles: List[Dict[str, object]] = []
    for index, task in enumerate(subset):
        correct_profile = profile_from_gold(task)
        correct_harness = compile_minimal_harness(correct_profile, registry)
        correct_result = execute_task(task, "gapharness_correct_gold", "gold", correct_harness, registry)
        correct_row = correct_result.to_json()
        correct_row["task"] = task.to_json()
        correct_row["profile"] = correct_profile.to_json()
        correct_row["metrics"] = row_metrics(task, correct_result)
        correct_row["corruption_condition"] = "correct_gold"
        rows.append(correct_row)

        corrupted_profile, actions = corrupt_gold_profile(task, index)
        corrupted_harness = compile_minimal_harness(corrupted_profile, registry)
        corrupted_result = execute_task(task, "gapharness_permuted_gold_input", "permuted_gold", corrupted_harness, registry)
        corrupted_row = corrupted_result.to_json()
        corrupted_row["task"] = task.to_json()
        corrupted_row["profile"] = corrupted_profile.to_json()
        corrupted_row["metrics"] = row_metrics(task, corrupted_result)
        corrupted_row["corruption_condition"] = "permuted_gold_input"
        corrupted_row["corruption_actions"] = actions
        corrupted_row["profile_changed"] = profile_changed(task, corrupted_profile)
        rows.append(corrupted_row)
        corrupted_profiles.append(
            {
                "task_id": task.task_id,
                "original_gold_obligations": sorted(task.gold_obligations),
                "original_required_capabilities": sorted(task.required_capabilities),
                "corrupted_profile": corrupted_profile.to_json(),
                "corruption_actions": actions,
                "profile_changed": profile_changed(task, corrupted_profile),
            }
        )

    write_jsonl(str(out_dir / "results_gold_label_permutation.jsonl"), rows)
    write_jsonl(str(out_dir / "permuted_profiles_200.jsonl"), corrupted_profiles)
    (out_dir.parent / "gold_label_permutation_report.md").write_text(
        render_gold_permutation_report(rows),
        encoding="utf-8",
    )


def corrupt_gold_profile(task: TaskExample, index: int) -> Tuple[ProfilerOutput, List[str]]:
    obligations = set(task.gold_obligations)
    capabilities = set(task.required_capabilities)
    actions: List[str] = []
    original_obligations = set(task.gold_obligations)
    original_capabilities = set(task.required_capabilities)
    mode = index % 5

    if mode == 0:
        swap_obligation(obligations, "Observation", "Execution")
        swap_capability_family(
            capabilities,
            ("evidence_sources", "workspace_inspection", "source_spans"),
            ("execution", "execution_log"),
        )
        actions.append("swap_observation_execution")
    elif mode == 1:
        swap_obligation(obligations, "Action", "State")
        if "sandbox_action" in capabilities or "diff" in capabilities:
            capabilities.difference_update({"sandbox_action", "diff"})
            capabilities.add("durable_state")
        elif "durable_state" in capabilities:
            capabilities.remove("durable_state")
            capabilities.update({"sandbox_action", "diff", "permission"})
            obligations.add("Control")
        actions.append("swap_action_state")
    elif mode == 2:
        obligations.discard("Verification")
        capabilities.difference_update({"source_spans", "execution_log", "contract_check"})
        if "Action" not in task.gold_obligations:
            capabilities.discard("diff")
        actions.append("delete_verification")
    elif mode == 3:
        obligations.add("Control")
        capabilities.add("permission")
        actions.append("add_control")
    else:
        if obligations:
            removed = sorted(obligations)[0]
            obligations.remove(removed)
            remove_capabilities_for_obligation(capabilities, removed)
            actions.append("drop_primary_%s" % removed.lower())

    if not obligations and not capabilities:
        obligations.add("Control")
        capabilities.add("permission")
        actions.append("avoid_empty_profile_by_adding_control")

    if obligations == original_obligations and capabilities == original_capabilities:
        force_semantic_corruption(obligations, capabilities, task)
        actions.append("forced_semantic_change")

    return (
        ProfilerOutput(
            direct_llm_sufficient=False,
            obligations=frozenset(obligations),
            required_capabilities=frozenset(capabilities),
            output_contract={"corruption_test": True},
            risk_level=task.risk_level,
            rationale="Anti-circularity stress test: corrupted obligation profile.",
        ),
        actions,
    )


def profile_changed(task: TaskExample, profile: ProfilerOutput) -> bool:
    return set(task.gold_obligations) != set(profile.obligations) or set(task.required_capabilities) != set(
        profile.required_capabilities
    )


def force_semantic_corruption(obligations: set, capabilities: set, task: TaskExample) -> None:
    if "Verification" in obligations:
        obligations.remove("Verification")
        capabilities.difference_update({"source_spans", "execution_log", "contract_check"})
        if "Action" not in task.gold_obligations:
            capabilities.discard("diff")
        return
    if "Observation" in obligations:
        obligations.remove("Observation")
        obligations.add("Execution")
        capabilities.difference_update({"evidence_sources", "workspace_inspection", "source_spans"})
        capabilities.update({"execution", "execution_log"})
        return
    if "Execution" in obligations:
        obligations.remove("Execution")
        obligations.add("Observation")
        capabilities.difference_update({"execution", "execution_log"})
        capabilities.update({"evidence_sources", "source_spans"})
        return
    if "Action" in obligations:
        obligations.remove("Action")
        capabilities.difference_update({"sandbox_action", "diff"})
        return
    if "State" in obligations:
        obligations.remove("State")
        obligations.add("Action")
        obligations.add("Control")
        capabilities.difference_update({"durable_state"})
        capabilities.update({"sandbox_action", "diff", "permission"})
        return
    if "Control" in obligations:
        obligations.remove("Control")
        capabilities.discard("permission")
        if not obligations:
            obligations.add("Execution")
            capabilities.add("execution")


def swap_obligation(obligations: set, left: str, right: str) -> None:
    has_left = left in obligations
    has_right = right in obligations
    if has_left:
        obligations.remove(left)
        obligations.add(right)
    if has_right:
        obligations.remove(right)
        obligations.add(left)


def swap_capability_family(capabilities: set, left: Sequence[str], right: Sequence[str]) -> None:
    has_left = bool(set(left) & capabilities)
    has_right = bool(set(right) & capabilities)
    if has_left:
        capabilities.difference_update(left)
        capabilities.update(right)
    if has_right:
        capabilities.difference_update(right)
        capabilities.update(("evidence_sources", "source_spans"))


def remove_capabilities_for_obligation(capabilities: set, obligation: str) -> None:
    mapping = {
        "Observation": {"evidence_sources", "source_spans", "workspace_inspection"},
        "Execution": {"execution", "execution_log"},
        "State": {"durable_state", "workspace_inspection"},
        "Action": {"sandbox_action", "diff"},
        "Control": {"permission"},
        "Verification": {"source_spans", "execution_log", "contract_check"},
    }
    capabilities.difference_update(mapping.get(obligation, set()))


def render_gold_permutation_report(rows: Sequence[Mapping[str, object]]) -> str:
    summary = summarize_results(rows)
    lines = [
        "# Phase 2D Stress Test 2: Gold Label Permutation",
        "",
        "This is not a realistic corruption model. It is an anti-circularity stress test showing that the compiler is sensitive to obligation semantics.",
        "",
        "Protocol: the compiler receives corrupted obligation profiles, while the verifier still checks against the original human-audited gold labels.",
        "",
        "| Condition | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Verifier Fail |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in ("gapharness_correct_gold", "gapharness_permuted_gold_input"):
        item = summary[system]
        bucket = [row for row in rows if row["system"] == system]
        lines.append(
            "| %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |"
            % (
                system,
                item["n"],
                item["success_rate"],
                item["avg_cost"],
                item["avg_oracle_cost"],
                item["avg_minimality_regret"],
                item["over_harness_rate"],
                item["under_harness_rate"],
                item["wrong_harness_rate"],
                1.0 - item["success_rate"],
            )
        )

    permuted = [row for row in rows if row["system"] == "gapharness_permuted_gold_input"]
    changed_count = sum(1 for row in permuted if row.get("profile_changed"))
    no_op_count = len(permuted) - changed_count
    lines.extend(
        [
            "",
            "Permutation integrity: %d / %d corrupted profiles changed obligations or required capabilities; no-op corruptions: %d."
            % (changed_count, len(permuted), no_op_count),
            "",
            "## Corruption Actions",
            "",
            "| Action | Count | Success | Under | Wrong |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for action, bucket in group_by_corruption_action(permuted).items():
        lines.append(
            "| %s | %d | %.2f | %.2f | %.2f |"
            % (
                action,
                len(bucket),
                mean(row["metrics"]["success"] for row in bucket),
                mean(row["metrics"]["under_harness"] for row in bucket),
                mean(row["metrics"]["wrong_harness"] for row in bucket),
            )
        )
    lines.extend(
        [
            "",
            "## Representative Failures",
            "",
            "| Task | Actions | Harness Status | Failures | Original Gold | Corrupted Profile | Query |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    failures = [row for row in permuted if not row["metrics"]["success"]][:20]
    for row in failures:
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s |"
            % (
                row["task_id"],
                ",".join(row.get("corruption_actions", [])),
                row["harness"]["status"],
                ",".join(row.get("verifier_failures", [])) or "-",
                ",".join(row["task"]["gold_obligations"]),
                ",".join(row["profile"]["obligations"]),
                trim(row["task"]["query"], 100),
            )
        )
    lines.append("")
    return "\n".join(lines)


def group_by_corruption_action(rows: Sequence[Mapping[str, object]]) -> Dict[str, List[Mapping[str, object]]]:
    grouped: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        action = ",".join(row.get("corruption_actions", []))
        grouped[action].append(row)
    return dict(sorted(grouped.items()))


def run_negative_controls(tasks: Sequence[TaskExample], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    negative_tasks = [task for task in tasks if task.category in NEGATIVE_CATEGORIES]
    rows: List[Dict[str, object]] = []
    registry = default_registry()
    deterministic_systems = (
        ("direct", "direct"),
        ("tool_router", "tool_router"),
        ("always_full", "always_full"),
        ("difficulty_router", "difficulty_router"),
        ("gapharness_gold", "gapharness"),
    )
    for task in negative_tasks:
        for output_label, system in deterministic_systems:
            harness, profiler = compile_for_system(task, system, "gold", registry)
            result = execute_task(task, output_label, profiler, harness, registry)
            row = result.to_json()
            row["task"] = task.to_json()
            row["metrics"] = row_metrics(task, result)
            row["source"] = "deterministic_recomputed"
            rows.append(row)

    rows.extend(load_cached_negative_rows("gapharness_llm_single", negative_tasks, phase2b_paths()))
    rows.extend(load_cached_negative_rows("gapharness_registry_guarded", negative_tasks, phase2c_paths()))

    write_jsonl(str(out_dir / "results_negative_controls.jsonl"), rows)
    (out_dir.parent / "negative_control_analysis_report.md").write_text(
        render_negative_control_report(rows),
        encoding="utf-8",
    )


def phase2b_paths() -> Sequence[str]:
    return (
        "outputs/phase2b/results_dev200_llm_single.jsonl",
        "outputs/phase2b/results_test800_selected_llm_single.jsonl",
    )


def phase2c_paths() -> Sequence[str]:
    return (
        "outputs/phase2c/dev200_registry_guarded/results_dev200_llm_registry_guarded.jsonl",
        "outputs/phase2c/test800_registry_guarded/results_test800_llm_registry_guarded.jsonl",
    )


def load_cached_negative_rows(
    system_label: str,
    negative_tasks: Sequence[TaskExample],
    paths: Sequence[str],
) -> List[Dict[str, object]]:
    wanted = {task.task_id for task in negative_tasks}
    rows: List[Dict[str, object]] = []
    seen = set()
    for path in paths:
        source = Path(path)
        if not source.exists():
            continue
        for row in load_results(str(source)):
            if row["task_id"] not in wanted or row["task_id"] in seen:
                continue
            copied = dict(row)
            copied["system"] = system_label
            copied["source"] = str(source)
            rows.append(copied)
            seen.add(row["task_id"])
    missing = sorted(wanted - seen)
    if missing:
        raise RuntimeError("Missing cached rows for %s: %s" % (system_label, ",".join(missing[:20])))
    return rows


def render_negative_control_report(rows: Sequence[Mapping[str, object]]) -> str:
    systems = (
        "direct",
        "tool_router",
        "always_full",
        "difficulty_router",
        "gapharness_gold",
        "gapharness_llm_single",
        "gapharness_registry_guarded",
    )
    lines = [
        "# Phase 2D Negative-Control Analysis: Pure Language and Tool-Bait",
        "",
        "This analysis tests whether systems are obligation-sensitive rather than keyword/tool-sensitive.",
        "",
        "## Category-Level Results",
        "",
        "| Category | System | N | Success | Avg Cost | Over | Under | Wrong |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for category in NEGATIVE_CATEGORIES:
        for system in systems:
            bucket = [row for row in rows if row["task"]["category"] == category and row["system"] == system]
            if not bucket:
                continue
            lines.append(metric_line(category, system, bucket))

    lines.extend(
        [
            "",
            "## Combined Negative Controls",
            "",
            "| System | N | Success | Avg Cost | Over | Under | Wrong |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for system in systems:
        bucket = [row for row in rows if row["system"] == system]
        if not bucket:
            continue
        lines.append(
            "| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f |"
            % (
                system,
                len(bucket),
                mean(row["metrics"]["success"] for row in bucket),
                mean(row["metrics"]["predicted_cost"] for row in bucket),
                mean(row["metrics"]["over_harness"] for row in bucket),
                mean(row["metrics"]["under_harness"] for row in bucket),
                mean(row["metrics"]["wrong_harness"] for row in bucket),
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: GapHarness gold and calibrated LLM variants should avoid over-harnessing pure language and explicit no-tool bait, while Always-full necessarily over-harnesses.",
            "",
        ]
    )
    return "\n".join(lines)


def metric_line(category: str, system: str, rows: Sequence[Mapping[str, object]]) -> str:
    return (
        "| %s | %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f |"
        % (
            category,
            system,
            len(rows),
            mean(row["metrics"]["success"] for row in rows),
            mean(row["metrics"]["predicted_cost"] for row in rows),
            mean(row["metrics"]["over_harness"] for row in rows),
            mean(row["metrics"]["under_harness"] for row in rows),
            mean(row["metrics"]["wrong_harness"] for row in rows),
        )
    )


def write_phase2d_index(out_dir: Path) -> None:
    lines = [
        "# Phase 2D Stress Test Index",
        "",
        "- `registry_perturbation_report.md`: declared registry boundary stress test.",
        "- `gold_label_permutation_report.md`: anti-circularity label corruption stress test.",
        "- `negative_control_analysis_report.md`: pure-language and tool-bait negative controls.",
        "",
    ]
    (out_dir / "phase2d_summary.md").write_text("\n".join(lines), encoding="utf-8")


def dominant_missing_capabilities(rows: Sequence[Mapping[str, object]]) -> str:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row["stress_metrics"].get("missing_capabilities", []))
        for failure in row["stress_metrics"].get("verifier_failures", []):
            if failure.startswith("missing_capabilities:"):
                counter.update(failure.split(":", 1)[1].split(","))
    if not counter:
        return "-"
    return ", ".join("%s:%d" % (name, count) for name, count in counter.most_common(4))


def mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / float(len(values_list))


def trim(value: str, limit: int) -> str:
    value = value.replace("|", "/").replace("\n", " ")
    return value if len(value) <= limit else value[: limit - 3] + "..."


if __name__ == "__main__":
    raise SystemExit(main())
