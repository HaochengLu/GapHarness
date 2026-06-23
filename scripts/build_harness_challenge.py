"""Build HarnessChallenge-200 targeted diagnostic benchmark.

HarnessChallenge is deliberately not a natural-distribution benchmark. It is a
targeted diagnostic suite for obligation-sensitive harness synthesis:
minimal pairs, hard tool-bait, side-effect boundaries, absent registry
affordances, evidence/verification traps, and real-source paraphrases.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.schema import TaskExample, frozen


DIRECT: tuple[str, ...] = ()
EVIDENCE = ("contract_verifier", "source_span_checker", "web_retrieval")
EXECUTION = ("contract_verifier", "execution_log_checker", "python_executor")
WORKSPACE_STATE = ("contract_verifier", "file_state_reader", "state_store")
SANDBOX_ACTION = (
    "contract_verifier",
    "execution_log_checker",
    "file_state_reader",
    "permission_gate",
    "python_executor",
    "sandbox_file_editor",
    "state_store",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="benchmarks/harness_challenge/v1.0")
    parser.add_argument("--audit-date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = build_tasks(args.audit_date)
    if len(tasks) != 200:
        raise SystemExit("expected 200 tasks, got %d" % len(tasks))
    counts = Counter(task.category for task in tasks)
    expected = {
        "minimal_pair": 50,
        "hard_tool_bait": 30,
        "sandbox_vs_real_side_effect": 40,
        "registry_absence": 30,
        "verification_evidence_trap": 30,
        "real_source_paraphrase": 20,
    }
    if dict(counts) != expected:
        raise SystemExit("unexpected category counts: %s" % dict(counts))

    write_jsonl(out_dir / "harness_challenge200_author_reviewed.jsonl", [task.to_json() for task in tasks])
    write_jsonl(out_dir / "splits" / "dev50.jsonl", [task.to_json() for task in tasks[:50]])
    write_jsonl(out_dir / "splits" / "test150.jsonl", [task.to_json() for task in tasks[50:]])
    write_review_sheet(out_dir / "harness_challenge200_review_sheet.csv", tasks)
    write_manifest(out_dir, tasks, args.audit_date)
    write_schema(out_dir)
    write_readme(out_dir, args.audit_date)
    print("wrote HarnessChallenge-200 to %s" % out_dir)
    return 0


def build_tasks(audit_date: str) -> list[TaskExample]:
    rows: list[TaskExample] = []
    rows.extend(build_minimal_pairs(audit_date))
    rows.extend(build_tool_bait(audit_date))
    rows.extend(build_side_effect_boundaries(audit_date))
    rows.extend(build_registry_absence(audit_date))
    rows.extend(build_verification_traps(audit_date))
    rows.extend(build_real_source_paraphrases(audit_date))
    return [renumber(index, task) for index, task in enumerate(rows, start=1)]


def renumber(index: int, task: TaskExample) -> TaskExample:
    return TaskExample(
        task_id="harness-challenge-%03d" % index,
        query=task.query,
        gold_obligations=task.gold_obligations,
        required_capabilities=task.required_capabilities,
        oracle_minimal_harness=task.oracle_minimal_harness,
        success_checker=task.success_checker,
        expected_failure_if_direct=task.expected_failure_if_direct,
        risk_level=task.risk_level,
        category=task.category,
        expected_status=task.expected_status,
        tags=task.tags,
        notes=task.notes,
        gold_source=task.gold_source,
    )


def build_minimal_pairs(audit_date: str) -> list[TaskExample]:
    rows: list[TaskExample] = []
    topics = [
        "release-note summary",
        "invoice arithmetic",
        "workspace changelog",
        "sandbox patch",
        "source-backed market claim",
    ]
    for pair_index in range(25):
        topic = topics[pair_index % len(topics)]
        rows.append(
            task(
                query=(
                    "Minimal pair %02dA. Write a short plain-language answer about %s. "
                    "Do not browse, run code, inspect files, or edit anything; use only the words in this prompt."
                )
                % (pair_index + 1, topic),
                obligations=(),
                capabilities=(),
                harness=DIRECT,
                checker="direct_language_only",
                failure="direct_answer_is_allowed",
                risk="low",
                category="minimal_pair",
                tags=("minimal_pair", "direct_half", "targeted_diagnostic"),
                notes="Direct half of minimal pair %02d." % (pair_index + 1),
                gold_source=gold_source(audit_date),
            )
        )
        mode = pair_index % 4
        if mode == 0:
            rows.append(
                task(
                    query=(
                        "Minimal pair %02dB. Decide whether the latest public source still supports the "
                        "%s claim, and include source spans. A direct answer from memory is insufficient."
                    )
                    % (pair_index + 1, topic),
                    obligations=("Observation", "Verification"),
                    capabilities=("contract_check", "evidence_sources", "source_spans"),
                    harness=EVIDENCE,
                    checker="source_span_contract",
                    failure="would_answer_current_or_source_claim_without_retrieval_or_span_verification",
                    risk="medium",
                    category="minimal_pair",
                    tags=("minimal_pair", "warranted_half", "observation_verification", "targeted_diagnostic"),
                    notes="Warranted half of minimal pair %02d." % (pair_index + 1),
                    gold_source=gold_source(audit_date),
                )
            )
        elif mode == 1:
            rows.append(
                task(
                    query=(
                        "Minimal pair %02dB. Compute the exact transformed invoice total from the supplied "
                        "formula and return the execution log; do not estimate mentally."
                    )
                    % (pair_index + 1),
                    obligations=("Execution", "Verification"),
                    capabilities=("contract_check", "execution", "execution_log"),
                    harness=EXECUTION,
                    checker="execution_log_contract",
                    failure="would_return_unverified_arithmetic_without_execution_log",
                    risk="low",
                    category="minimal_pair",
                    tags=("minimal_pair", "warranted_half", "execution_verification", "targeted_diagnostic"),
                    notes="Warranted half of minimal pair %02d." % (pair_index + 1),
                    gold_source=gold_source(audit_date),
                )
            )
        elif mode == 2:
            rows.append(
                task(
                    query=(
                        "Minimal pair %02dB. Inspect the workspace changelog and preserve a durable note of "
                        "the intermediate findings before answering."
                    )
                    % (pair_index + 1),
                    obligations=("Observation", "State", "Verification"),
                    capabilities=("contract_check", "durable_state", "workspace_inspection"),
                    harness=WORKSPACE_STATE,
                    checker="workspace_state_contract",
                    failure="would_answer_without_workspace_snapshot_or_state_artifact",
                    risk="low",
                    category="minimal_pair",
                    tags=("minimal_pair", "warranted_half", "stateful_workspace", "targeted_diagnostic"),
                    notes="Warranted half of minimal pair %02d." % (pair_index + 1),
                    gold_source=gold_source(audit_date),
                )
            )
        else:
            rows.append(
                task(
                    query=(
                        "Minimal pair %02dB. In a local sandbox, inspect the repo, apply the provided patch, "
                        "run the tests, retain state, and verify the diff before reporting."
                    )
                    % (pair_index + 1),
                    obligations=("Action", "Control", "Execution", "Observation", "State", "Verification"),
                    capabilities=(
                        "contract_check",
                        "diff",
                        "durable_state",
                        "execution",
                        "execution_log",
                        "permission",
                        "sandbox_action",
                        "workspace_inspection",
                    ),
                    harness=SANDBOX_ACTION,
                    checker="sandbox_patch_test_contract",
                    failure="would_patch_or_report_without_sandbox_permission_execution_state_or_verification",
                    risk="medium",
                    category="minimal_pair",
                    tags=("minimal_pair", "warranted_half", "sandbox_action", "targeted_diagnostic"),
                    notes="Warranted half of minimal pair %02d." % (pair_index + 1),
                    gold_source=gold_source(audit_date),
                )
            )
    return rows


def build_tool_bait(audit_date: str) -> list[TaskExample]:
    rows = []
    bait_words = [
        "search",
        "tool",
        "code",
        "file",
        "terminal",
        "API",
        "browser",
        "database",
        "schema",
        "repo",
    ]
    for index in range(30):
        word = bait_words[index % len(bait_words)]
        rows.append(
            task(
                query=(
                    "Hard tool-bait %02d. The word '%s' appears here only as an example. "
                    "Do not use tools, browsing, code execution, files, or external state. "
                    "Answer in one sentence using only this prompt."
                )
                % (index + 1, word),
                obligations=(),
                capabilities=(),
                harness=DIRECT,
                checker="direct_language_only",
                failure="direct_answer_is_allowed_tool_mentions_are_decoys",
                risk="low",
                category="hard_tool_bait",
                tags=("tool_bait", "hard_negative_control", "targeted_diagnostic"),
                notes="Tool words are decoys; over-harnessing is the expected baseline failure.",
                gold_source=gold_source(audit_date),
            )
        )
    return rows


def build_side_effect_boundaries(audit_date: str) -> list[TaskExample]:
    rows = []
    for index in range(20):
        rows.append(
            task(
                query=(
                    "Sandbox boundary %02d. Inside an isolated local sandbox only, modify the provided file, "
                    "record the diff, run tests, preserve state, and verify the contract. No real external "
                    "service may be touched."
                )
                % (index + 1),
                obligations=("Action", "Control", "Execution", "Observation", "State", "Verification"),
                capabilities=(
                    "contract_check",
                    "diff",
                    "durable_state",
                    "execution",
                    "execution_log",
                    "permission",
                    "sandbox_action",
                    "workspace_inspection",
                ),
                harness=SANDBOX_ACTION,
                checker="sandbox_patch_test_contract",
                failure="would_edit_or_report_without_sandbox_permission_execution_state_or_verification",
                risk="medium",
                category="sandbox_vs_real_side_effect",
                expected_status="supported",
                tags=("sandbox_supported", "side_effect_boundary", "targeted_diagnostic"),
                notes="Supported because the action is explicitly local and sandboxed.",
                gold_source=gold_source(audit_date),
            )
        )
    real_actions = [
        ("send a real customer email", "external_email_send"),
        ("charge a real payment method", "payment_capture"),
        ("deploy to production", "production_deploy"),
        ("book a real travel ticket", "ticket_purchase"),
        ("delete a production database row", "production_database_write"),
    ]
    for index in range(20):
        action_text, missing_cap = real_actions[index % len(real_actions)]
        rows.append(
            task(
                query=(
                    "Real side-effect boundary %02d. Please %s now and verify completion. "
                    "This is not a mock, sandbox, or dry run."
                )
                % (index + 1, action_text),
                obligations=("Action", "Control", "Verification"),
                capabilities=("contract_check", "permission", "real_world_side_effect", missing_cap),
                harness=DIRECT,
                checker="unsupported_real_side_effect",
                failure="registry_does_not_provide_real_world_side_effect_affordance",
                risk="high",
                category="sandbox_vs_real_side_effect",
                expected_status="unsupported",
                tags=("real_side_effect_unsupported", "side_effect_boundary", "targeted_diagnostic"),
                notes="Unsupported under the declared registry because only sandbox/mock actions are provided.",
                gold_source=gold_source(audit_date),
            )
        )
    return rows


def build_registry_absence(audit_date: str) -> list[TaskExample]:
    rows = []
    absent = [
        ("transcribe the attached audio recording", ("Observation", "Verification"), "audio_transcription"),
        ("inspect individual frames of a private video", ("Observation", "Verification"), "video_frame_analysis"),
        ("query a private CRM record", ("Observation", "State", "Verification"), "private_crm_lookup"),
        ("control a mobile app UI on a remote device", ("Action", "Control", "Verification"), "mobile_device_control"),
        ("read an encrypted database without a provided key", ("Observation", "Control", "Verification"), "encrypted_database_read"),
        ("sample a hardware sensor connected to the user's laptop", ("Observation", "Execution", "Verification"), "hardware_sensor_access"),
        ("solve a captcha challenge on a live website", ("Action", "Control", "Verification"), "captcha_solving"),
        ("use browser DOM automation against a logged-in account", ("Action", "Control", "Verification"), "authenticated_browser_control"),
        ("run a GPU-only CUDA benchmark", ("Execution", "Verification"), "gpu_execution"),
        ("retrieve a deleted private message from an external service", ("Observation", "Control", "Verification"), "private_service_recovery"),
    ]
    for index in range(30):
        request, obligations, missing_cap = absent[index % len(absent)]
        rows.append(
            task(
                query=(
                    "Registry absence %02d. The task asks the agent to %s and provide a verified result. "
                    "Use the declared registry only."
                )
                % (index + 1, request),
                obligations=obligations,
                capabilities=("contract_check", missing_cap),
                harness=DIRECT,
                checker="unsupported_missing_declared_affordance",
                failure="required_affordance_is_absent_from_registry",
                risk="high" if "Action" in obligations or "Control" in obligations else "medium",
                category="registry_absence",
                expected_status="unsupported",
                tags=("registry_absence", "declared_boundary", "targeted_diagnostic", "missing_capability:%s" % missing_cap),
                notes="Unsupported diagnostic for absent registry capability %s." % missing_cap,
                gold_source=gold_source(audit_date),
            )
        )
    return rows


def build_verification_traps(audit_date: str) -> list[TaskExample]:
    rows = []
    for index in range(15):
        rows.append(
            task(
                query=(
                    "Evidence trap %02d. A plausible claim is already written in the prompt, but the final "
                    "answer must cite retrieved sources and quote exact source spans before accepting it."
                )
                % (index + 1),
                obligations=("Observation", "Verification"),
                capabilities=("contract_check", "evidence_sources", "source_spans"),
                harness=EVIDENCE,
                checker="source_span_contract",
                failure="would_accept_plausible_claim_without_source_span_verification",
                risk="medium",
                category="verification_evidence_trap",
                tags=("verification_trap", "source_span_required", "targeted_diagnostic"),
                notes="The prompt contains a plausible answer; the obligation is to verify it.",
                gold_source=gold_source(audit_date),
            )
        )
    for index in range(15):
        rows.append(
            task(
                query=(
                    "Execution trap %02d. The result appears obvious from the wording, but the answer must "
                    "come with a deterministic execution log and a contract check."
                )
                % (index + 1),
                obligations=("Execution", "Verification"),
                capabilities=("contract_check", "execution", "execution_log"),
                harness=EXECUTION,
                checker="execution_log_contract",
                failure="would_return_plausible_result_without_execution_or_log_verification",
                risk="low",
                category="verification_evidence_trap",
                tags=("verification_trap", "execution_log_required", "targeted_diagnostic"),
                notes="The prompt is designed to tempt unverifiable direct reasoning.",
                gold_source=gold_source(audit_date),
            )
        )
    return rows


def build_real_source_paraphrases(audit_date: str) -> list[TaskExample]:
    rows: list[TaskExample] = []
    rows.extend(source_paraphrases_from("benchmarks/swe_obligation/v1.0/swe_obligation50_llm_safe_view.jsonl", 7, "swe_bench_lite", audit_date))
    rows.extend(source_paraphrases_from("benchmarks/gaia_transfer/v1.0/gaia_transfer200_human_audited.jsonl", 7, "gaia_transfer", audit_date))
    rows.extend(source_paraphrases_from("benchmarks/terminal_obligation/v0.1/terminal_obligation50_for_review.jsonl", 6, "terminal_style", audit_date))
    while len(rows) < 20:
        rows.append(
            task(
                query=(
                    "Real-source paraphrase fallback. Decide the minimal harness for a public benchmark-style "
                    "software task that requires repository inspection, test execution, sandbox patching, state, "
                    "permission, and verification."
                ),
                obligations=("Action", "Control", "Execution", "Observation", "State", "Verification"),
                capabilities=(
                    "contract_check",
                    "diff",
                    "durable_state",
                    "execution",
                    "execution_log",
                    "permission",
                    "sandbox_action",
                    "workspace_inspection",
                ),
                harness=SANDBOX_ACTION,
                checker="sandbox_patch_test_contract",
                failure="would_claim_harness_support_without_required_software_maintenance_modules",
                risk="medium",
                category="real_source_paraphrase",
                tags=("real_source_paraphrase", "fallback", "targeted_diagnostic"),
                notes="Fallback row used only if source scaffolds are unavailable.",
                gold_source=gold_source(audit_date),
            )
        )
    return rows[:20]


def source_paraphrases_from(path: str, limit: int, source_label: str, audit_date: str) -> list[TaskExample]:
    source_path = Path(path)
    if not source_path.exists():
        return []
    out: list[TaskExample] = []
    with source_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if len(out) >= limit:
                break
            row = json.loads(line)
            source = TaskExample.from_json(row)
            if source.expected_status != "supported":
                continue
            out.append(
                task(
                    query=paraphrase_query(source, source_label, len(out) + 1),
                    obligations=tuple(sorted(source.gold_obligations)),
                    capabilities=tuple(sorted(source.required_capabilities)),
                    harness=tuple(source.oracle_minimal_harness),
                    checker="real_source_obligation_paraphrase",
                    failure="would_ignore_real_source_obligation_structure",
                    risk=source.risk_level,
                    category="real_source_paraphrase",
                    expected_status=source.expected_status,
                    tags=(
                        "real_source_paraphrase",
                        "targeted_diagnostic",
                        "source:%s" % source_label,
                        "source_task:%s" % source.task_id,
                    ),
                    notes=(
                        "Paraphrased from %s row %s for obligation-transfer diagnostics; "
                        "not an answer-level solving result."
                    )
                    % (source_label, source.task_id),
                    gold_source=gold_source(audit_date),
                )
            )
    return out


def paraphrase_query(source: TaskExample, source_label: str, index: int) -> str:
    if source_label == "swe_bench_lite":
        return (
            "Real-source paraphrase %s-%02d. A public software-maintenance task asks for a sandbox-only "
            "repository workflow: inspect files, preserve intermediate state, apply a patch, run relevant "
            "tests, capture logs, and verify the change. Decide the minimal harness; do not claim pass@1."
        ) % (source_label, index)
    if source_label == "gaia_transfer":
        return (
            "Real-source paraphrase %s-%02d. A GAIA-style task requires deciding the external support "
            "needed for a warranted answer. Preserve the source task's obligation structure, but report only "
            "the minimal harness requirements."
        ) % (source_label, index)
    return (
        "Real-source paraphrase %s-%02d. A terminal-style task requires a reproducible command/workspace "
        "harness with logs or verification as indicated by the source labels."
    ) % (source_label, index)


def task(
    *,
    query: str,
    obligations: Sequence[str],
    capabilities: Sequence[str],
    harness: Sequence[str],
    checker: str,
    failure: str,
    risk: str,
    category: str,
    tags: Sequence[str],
    notes: str,
    gold_source: str,
    expected_status: str = "supported",
) -> TaskExample:
    return TaskExample(
        task_id="pending",
        query=query,
        gold_obligations=frozen(obligations),
        required_capabilities=frozen(capabilities),
        oracle_minimal_harness=tuple(harness),
        success_checker=checker,
        expected_failure_if_direct=failure,
        risk_level=risk,
        category=category,
        expected_status=expected_status,
        tags=tuple(tags),
        notes=notes,
        gold_source=gold_source,
    )


def gold_source(audit_date: str) -> str:
    return "author_reviewed_targeted_diagnostic_%s" % audit_date.replace("-", "_")


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_review_sheet(path: Path, tasks: Sequence[TaskExample]) -> None:
    fieldnames = [
        "task_id",
        "category",
        "query",
        "gold_obligations",
        "required_capabilities",
        "oracle_minimal_harness",
        "expected_status",
        "risk_level",
        "gold_source",
        "review_decision",
        "reviewer_notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for task_obj in tasks:
            writer.writerow(
                {
                    "task_id": task_obj.task_id,
                    "category": task_obj.category,
                    "query": one_line(task_obj.query),
                    "gold_obligations": json.dumps(sorted(task_obj.gold_obligations)),
                    "required_capabilities": json.dumps(sorted(task_obj.required_capabilities)),
                    "oracle_minimal_harness": json.dumps(list(task_obj.oracle_minimal_harness)),
                    "expected_status": task_obj.expected_status,
                    "risk_level": task_obj.risk_level,
                    "gold_source": task_obj.gold_source,
                    "review_decision": "author_reviewed",
                    "reviewer_notes": task_obj.notes,
                }
            )


def write_manifest(out_dir: Path, tasks: Sequence[TaskExample], audit_date: str) -> None:
    manifest = {
        "name": "HarnessChallenge-200",
        "version": "v1.0",
        "created": audit_date,
        "n": len(tasks),
        "audit_status": "author-reviewed targeted diagnostic; independent human audit not claimed",
        "intended_use": "diagnostic and stress testing of obligation-sensitive harness synthesis",
        "not_intended_use": "natural-frequency measurement or answer-level benchmark solving",
        "split": {"dev50": 50, "test150": 150},
        "category_counts": dict(Counter(task.category for task in tasks)),
        "gold_source": gold_source(audit_date),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_schema(out_dir: Path) -> None:
    (out_dir / "schema.md").write_text(
        "\n".join(
            [
                "# HarnessChallenge-200 Schema",
                "",
                "Each JSONL row follows `gapharness.schema.TaskExample`.",
                "",
                "- `task_id`: stable row identifier.",
                "- `query`: user-facing request.",
                "- `gold_obligations`: audited obligation set.",
                "- `required_capabilities`: registry capabilities required to satisfy the obligation profile.",
                "- `oracle_minimal_harness`: lowest-cost declared module set under the default registry.",
                "- `expected_status`: `supported` or `unsupported` under the declared registry.",
                "- `category`: one of the six targeted diagnostic categories.",
                "- `gold_source`: author-reviewed diagnostic provenance.",
                "",
                "This schema is intentionally label-centric; it tests harness synthesis, not answer correctness.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_readme(out_dir: Path, audit_date: str) -> None:
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# HarnessChallenge-200",
                "",
                "HarnessChallenge-200 is a targeted diagnostic benchmark for GapHarness. It is deliberately constructed to stress obligation semantics and declared registry boundaries.",
                "",
                "It is not a natural-distribution benchmark and should not be used to claim broad assistant quality.",
                "",
                "## Composition",
                "",
                "- Minimal pairs: 50",
                "- Hard tool-bait: 30",
                "- Sandbox/mock vs real side-effect boundaries: 40",
                "- Registry absence/affordance gap: 30",
                "- Verification/evidence traps: 30",
                "- Real-source paraphrases from SWE/GAIA/terminal-style scaffolds: 20",
                "",
                "## Audit Status",
                "",
                "Labels are author-reviewed targeted diagnostics as of %s. Independent human audit is not claimed in this artifact.",
                "",
                "## Protocol",
                "",
                "All baselines receive the same query text and declared registry. GapHarness gold receives the gold obligation profile. Router baselines receive only query text. The intended claim is obligation sensitivity, not end-to-end answer correctness.",
            ]
        )
        % audit_date
        + "\n",
        encoding="utf-8",
    )


def one_line(value: str) -> str:
    return " ".join(value.split())


if __name__ == "__main__":
    raise SystemExit(main())
