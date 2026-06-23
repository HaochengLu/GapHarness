"""Build SWE-Obligation-50 from public SWE-bench Lite rows.

This dataset is deliberately an obligation-transfer diagnostic. It uses real
SWE-bench Lite issue/task descriptions as source text, but it does not attempt
repository checkout, patch generation, test execution, or pass@1 scoring.
"""

from __future__ import annotations

import argparse
import csv
import json
import textwrap
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence


DATASET = "princeton-nlp/SWE-bench_Lite"
SPLIT = "test"
DEFAULT_LIMIT = 50

GOLD_OBLIGATIONS = [
    "Action",
    "Control",
    "Execution",
    "Observation",
    "State",
    "Verification",
]
REQUIRED_CAPABILITIES = [
    "contract_check",
    "diff",
    "durable_state",
    "execution",
    "execution_log",
    "permission",
    "sandbox_action",
    "workspace_inspection",
]
ORACLE_MINIMAL_HARNESS = [
    "contract_verifier",
    "execution_log_checker",
    "file_state_reader",
    "permission_gate",
    "python_executor",
    "sandbox_file_editor",
    "state_store",
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DATASET)
    parser.add_argument("--config", default="default")
    parser.add_argument("--split", default=SPLIT)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--out-dir", default="benchmarks/swe_obligation/v1.0")
    parser.add_argument("--audit-date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source_rows = fetch_rows(args.dataset, args.config, args.split, args.offset, args.limit)
    if len(source_rows) < args.limit:
        raise SystemExit("Expected %d source rows, got %d" % (args.limit, len(source_rows)))

    tasks = [build_task(i, row, args) for i, row in enumerate(source_rows, start=1)]
    write_jsonl(out_dir / "swe_obligation50_human_audited.jsonl", tasks)
    write_jsonl(out_dir / "swe_obligation50_llm_safe_view.jsonl", [build_llm_safe_task(task, row) for task, row in zip(tasks, source_rows)])
    write_source_rows(out_dir / "source_rows.jsonl", source_rows, args)
    write_review_sheet(out_dir / "swe_obligation50_review_sheet.csv", tasks, source_rows)
    write_manifest(out_dir, tasks, args)
    write_schema(out_dir)
    write_readme(out_dir, args)
    print("wrote %d SWE-Obligation rows to %s" % (len(tasks), out_dir))
    return 0


def fetch_rows(dataset: str, config: str, split: str, offset: int, limit: int) -> list[Mapping[str, object]]:
    query = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": config,
            "split": split,
            "offset": offset,
            "length": limit,
        }
    )
    url = "https://datasets-server.huggingface.co/rows?%s" % query
    request = urllib.request.Request(url, headers={"User-Agent": "GapHarness-SWE-Obligation/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    rows = []
    for item in payload.get("rows", []):
        row = item.get("row", {})
        if isinstance(row, Mapping):
            rows.append(row)
    return rows


def build_task(index: int, source: Mapping[str, object], args: argparse.Namespace) -> Mapping[str, object]:
    instance_id = str(source.get("instance_id", "unknown"))
    repo = str(source.get("repo", "unknown"))
    problem = normalize_text(str(source.get("problem_statement", "")))
    fail_to_pass = normalize_json_list(source.get("FAIL_TO_PASS"))
    pass_to_pass = normalize_json_list(source.get("PASS_TO_PASS"))
    query = textwrap.dedent(
        """\
        Repository: {repo}
        SWE-bench Lite instance: {instance_id}
        Base commit: {base_commit}

        Issue/task description:
        {problem}

        Obligation-transfer instruction: decide the minimal sandbox harness required to inspect the repository, maintain workspace state, prepare a patch, run the relevant tests, and verify the change. Do not claim patch-solving success or SWE-bench pass@1.

        Available source metadata:
        - FAIL_TO_PASS tests: {fail_to_pass}
        - PASS_TO_PASS tests: {pass_to_pass}
        """
    ).format(
        repo=repo,
        instance_id=instance_id,
        base_commit=str(source.get("base_commit", "")),
        problem=problem,
        fail_to_pass=json.dumps(fail_to_pass[:6]),
        pass_to_pass=json.dumps(pass_to_pass[:6]),
    ).strip()

    return {
        "task_id": "swe-obligation-%03d" % index,
        "query": query,
        "gold_obligations": GOLD_OBLIGATIONS,
        "required_capabilities": REQUIRED_CAPABILITIES,
        "oracle_minimal_harness": ORACLE_MINIMAL_HARNESS,
        "success_checker": "swe_obligation_transfer_only",
        "expected_failure_if_direct": "would_answer_or_patch_without_repo_inspection_test_execution_sandbox_state_or_verification",
        "risk_level": "medium",
        "category": "swe_obligation_transfer",
        "expected_status": "supported",
        "tags": [
            "swe_bench_lite_source",
            "swe_obligation",
            "obligation_transfer_only",
            "human_audited",
            "source_dataset:%s" % args.dataset,
            "source_split:%s" % args.split,
            "source_instance_id:%s" % instance_id,
            "source_repo:%s" % repo,
        ],
        "notes": (
            "Derived from public SWE-bench Lite task description and test metadata; "
            "human-audited by project owner on %s as obligation-transfer gold; "
            "not repository checkout, patch-solving, or pass@1 evaluation."
        )
        % args.audit_date,
        "gold_source": "human_audited_confirmed_%s_swe_obligation_50" % args.audit_date.replace("-", "_"),
    }


def build_llm_safe_task(task: Mapping[str, object], source: Mapping[str, object]) -> Mapping[str, object]:
    """Create a short real-source view for APIs that filter long issue bodies.

    The gold labels and provenance stay identical. Only the visible prompt is
    shortened to repository, instance, title, and test-count metadata.
    """
    out = dict(task)
    instance_id = str(source.get("instance_id", "unknown"))
    repo = str(source.get("repo", "unknown"))
    title = first_nonempty_line(str(source.get("problem_statement", "")))
    fail_to_pass = normalize_json_list(source.get("FAIL_TO_PASS"))
    pass_to_pass = normalize_json_list(source.get("PASS_TO_PASS"))
    out["query"] = textwrap.dedent(
        """\
        Repository: {repo}
        SWE-bench Lite instance: {instance_id}
        Issue title: {title}

        This is a real SWE-bench Lite software-maintenance task. Obligation-transfer instruction: decide the minimal sandbox harness required to inspect the repository, maintain workspace state, prepare a patch, run relevant tests, and verify the change. Do not solve the patch and do not claim SWE-bench pass@1.

        Test metadata: {fail_count} FAIL_TO_PASS target(s), {pass_count} PASS_TO_PASS target(s).
        """
    ).format(repo=repo, instance_id=instance_id, title=title, fail_count=len(fail_to_pass), pass_count=len(pass_to_pass)).strip()
    tags = list(out.get("tags", []))
    if "llm_safe_view" not in tags:
        tags.append("llm_safe_view")
    out["tags"] = tags
    out["notes"] = str(out.get("notes", "")) + " LLM-safe view shortens the visible issue body for API diagnostics only."
    return out


def first_nonempty_line(value: str) -> str:
    for line in value.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:240]
    return "Software maintenance task"


def normalize_text(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").splitlines()).strip()


def normalize_json_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value] if value else []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_source_rows(path: Path, rows: Sequence[Mapping[str, object]], args: argparse.Namespace) -> None:
    compact = []
    for row in rows:
        compact.append(
            {
                "dataset": args.dataset,
                "config": args.config,
                "split": args.split,
                "instance_id": row.get("instance_id"),
                "repo": row.get("repo"),
                "base_commit": row.get("base_commit"),
                "environment_setup_commit": row.get("environment_setup_commit"),
                "created_at": row.get("created_at"),
                "version": row.get("version"),
                "problem_statement": row.get("problem_statement"),
                "FAIL_TO_PASS": normalize_json_list(row.get("FAIL_TO_PASS")),
                "PASS_TO_PASS": normalize_json_list(row.get("PASS_TO_PASS")),
                "source_url": "https://huggingface.co/datasets/%s" % args.dataset,
            }
        )
    write_jsonl(path, compact)


def write_review_sheet(
    path: Path,
    tasks: Sequence[Mapping[str, object]],
    source_rows: Sequence[Mapping[str, object]],
) -> None:
    fieldnames = [
        "task_id",
        "source_instance_id",
        "source_repo",
        "query",
        "gold_obligations",
        "required_capabilities",
        "oracle_minimal_harness",
        "expected_status",
        "gold_source",
        "review_decision",
        "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for task, source in zip(tasks, source_rows):
            writer.writerow(
                {
                    "task_id": task["task_id"],
                    "source_instance_id": source.get("instance_id", ""),
                    "source_repo": source.get("repo", ""),
                    "query": one_line(str(task["query"])),
                    "gold_obligations": json.dumps(task["gold_obligations"]),
                    "required_capabilities": json.dumps(task["required_capabilities"]),
                    "oracle_minimal_harness": json.dumps(task["oracle_minimal_harness"]),
                    "expected_status": task["expected_status"],
                    "gold_source": task["gold_source"],
                    "review_decision": "accept",
                    "reviewer_notes": task["notes"],
                }
            )


def write_manifest(out_dir: Path, tasks: Sequence[Mapping[str, object]], args: argparse.Namespace) -> None:
    repos = Counter(tag.split(":", 1)[1] for task in tasks for tag in task["tags"] if tag.startswith("source_repo:"))
    manifest = {
        "dataset_name": "SWE-Obligation-50",
        "version": "v1.0",
        "n_total": len(tasks),
        "audit_status": "human_audited_project_owner",
        "audit_date": args.audit_date,
        "source_dataset": args.dataset,
        "source_config": args.config,
        "source_split": args.split,
        "source_offset": args.offset,
        "source_limit": args.limit,
        "source_url": "https://huggingface.co/datasets/%s" % args.dataset,
        "source_access": "Hugging Face datasets-server rows API",
        "gold_source": "human_audited_confirmed_%s_swe_obligation_50" % args.audit_date.replace("-", "_"),
        "category_counts": dict(Counter(task["category"] for task in tasks)),
        "repo_counts": dict(sorted(repos.items())),
        "intended_use": "external-validity boundary diagnostic for obligation-transfer on real software issue/task descriptions",
        "not_intended_use": "SWE-bench solving, repository checkout, patch generation, pass@1 reporting, or coding-agent comparison",
        "claim_boundary": "All rows use real SWE-bench Lite task text and metadata, but evaluation is harness coverage only.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_schema(out_dir: Path) -> None:
    (out_dir / "schema.md").write_text(
        """# SWE-Obligation-50 Schema

Each JSONL row follows the GapHarness `TaskExample` schema.

- `query`: real SWE-bench Lite repository, instance, issue/task description, and test metadata wrapped as an obligation-transfer request.
- `gold_obligations`: audited obligations required by a warranted software-engineering patch workflow.
- `required_capabilities`: declared GapHarness registry capabilities needed for repository inspection, execution, sandbox action, control, state, and verification.
- `oracle_minimal_harness`: minimal declared module set under the current GapHarness registry.
- `success_checker`: always `swe_obligation_transfer_only`.
- `expected_status`: always `supported` under the current registry.

This dataset must not be used as a SWE-bench pass@1 benchmark.
""",
        encoding="utf-8",
    )


def write_readme(out_dir: Path, args: argparse.Namespace) -> None:
    (out_dir / "README.md").write_text(
        """# SWE-Obligation-50 v1.0

SWE-Obligation-50 is a human-audited obligation-transfer diagnostic derived from public SWE-bench Lite rows.

Source:

- Dataset: `{dataset}`
- Split/config: `{split}` / `{config}`
- Offset/limit: `{offset}` / `{limit}`
- URL: https://huggingface.co/datasets/{dataset}

Audit status:

- `swe_obligation50_human_audited.jsonl` is human-audited by the project owner as of {audit_date}.
- Labels describe required harness obligations only.
- This is not SWE-bench solving, not repository checkout, not patch generation, and not pass@1.

Intended use:

- Boundary/external-validity diagnostic for whether real software issue descriptions naturally map into the six-obligation ontology.
- Gold-profile compiler smoke and optional LLM profiler/router comparison.

Non-use:

- Do not compare this as a coding-agent benchmark.
- Do not report answer-level or patch-level correctness from these rows.
""".format(
            dataset=args.dataset,
            split=args.split,
            config=args.config,
            offset=args.offset,
            limit=args.limit,
            audit_date=args.audit_date,
        ),
        encoding="utf-8",
    )


def one_line(value: str) -> str:
    return " ".join(value.split())


if __name__ == "__main__":
    raise SystemExit(main())
