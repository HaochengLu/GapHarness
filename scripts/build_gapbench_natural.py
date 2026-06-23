"""Build GapBench-Natural-200 by naturalizing GapBench v1.0 queries."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from gapharness.llm_client import ChatMessage, OpenAICompatibleClient, parse_json_object


COMPOSITION = [
    ("pure_language_direct", 40),
    ("observation_evidence", 40),
    ("execution_computation", 30),
    ("file_workspace_inspection", 30),
    ("sandbox_action_permission", 20),
    ("ambiguous_unsupported", 20),
    ("mixed_multi_obligation", 20),
]


SYSTEM_PROMPT = """You rewrite controlled benchmark queries into natural user requests.

Return JSON only:
{"query": "..."}

Rules:
- Preserve the task's gold obligations, required capabilities, expected status, and risk semantics.
- Do not mention "obligation", "harness", "module", "benchmark", or labels.
- Make the query sound like a real user wrote it.
- If the source is direct/pure language, keep it explicitly answerable without tools.
- If the source needs current/external evidence, make the need for checking sources natural.
- If it needs execution, include exact computation/testing/parsing language.
- If it needs workspace/file inspection, mention a local file, README, log, CSV, PDF, or attached artifact.
- If it needs sandbox action, explicitly keep the action inside a sandbox.
- If it is unsupported, keep the request clearly outside the allowed sandbox or involving real-world side effects.
- If it is ambiguous, preserve the ambiguity so clarification remains warranted.
- Keep it one concise paragraph, no bullet list.
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="benchmarks/gapbench/v1.0/gapbench_1000_human_audited.jsonl")
    parser.add_argument("--out-dir", default="benchmarks/gapbench_natural/v1.0")
    parser.add_argument("--model", default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--progress-every", type=int, default=10)
    args = parser.parse_args(argv)

    rows = load_jsonl(Path(args.source))
    selected = select_rows(rows, args.limit)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "gapbench_natural_200_for_review.jsonl"
    csv_path = out_dir / "gapbench_natural_200_review_sheet.csv"

    done = existing_rows(jsonl_path)
    client = None if args.no_llm else OpenAICompatibleClient(model=args.model)
    with jsonl_path.open("a", encoding="utf-8") as handle:
        for index, item in enumerate(selected, start=1):
            task_id = "natural-%03d" % index
            if task_id in done:
                continue
            natural_query = rewrite_query(item, client) if client else fallback_rewrite(item)
            output = dict(item)
            output["task_id"] = task_id
            output["query"] = natural_query
            output["gold_source"] = "naturalized_for_human_review_2026_06_22"
            output["notes"] = (
                "Naturalized from %s for GapBench-Natural review; source_gold_source=%s"
                % (item["task_id"], item.get("gold_source", ""))
            )
            output["tags"] = list(item.get("tags", [])) + [
                "gapbench_natural",
                "source_task_id:%s" % item["task_id"],
                "natural_bucket:%s" % item["_natural_bucket"],
            ]
            output.pop("_natural_bucket", None)
            handle.write(json.dumps(output, sort_keys=True) + "\n")
            handle.flush()
            if args.progress_every and index % args.progress_every == 0:
                print("progress naturalized=%d/%d last=%s" % (index, len(selected), task_id), file=sys.stderr)

    final_rows = load_jsonl(jsonl_path)
    write_csv(csv_path, final_rows)
    write_manifest(out_dir, final_rows)
    write_readme(out_dir)
    print("wrote", len(final_rows), "rows to", jsonl_path)
    print("wrote review sheet", csv_path)
    return 0


def select_rows(rows: Sequence[Mapping[str, object]], limit: int) -> List[Dict[str, object]]:
    selected: List[Dict[str, object]] = []
    used = set()
    for bucket, count in COMPOSITION:
        matches = [dict(row) for row in rows if row["task_id"] not in used and matches_bucket(row, bucket)]
        if len(matches) < count:
            raise SystemExit("Not enough rows for %s: need %d, got %d" % (bucket, count, len(matches)))
        for row in matches[:count]:
            row["_natural_bucket"] = bucket
            selected.append(row)
            used.add(row["task_id"])
    if len(selected) != limit:
        raise SystemExit("Expected %d rows, selected %d" % (limit, len(selected)))
    return selected


def matches_bucket(row: Mapping[str, object], bucket: str) -> bool:
    obligations = set(row.get("gold_obligations", []))
    caps = set(row.get("required_capabilities", []))
    category = str(row.get("category", ""))
    status = str(row.get("expected_status", "supported"))
    if bucket == "pure_language_direct":
        return category in {"pure_language_negative", "tool_bait"} and not obligations
    if bucket == "observation_evidence":
        return "Observation" in obligations and "evidence_sources" in caps and status == "supported"
    if bucket == "execution_computation":
        return "Execution" in obligations and status == "supported"
    if bucket == "file_workspace_inspection":
        return "workspace_inspection" in caps and status == "supported"
    if bucket == "sandbox_action_permission":
        return "Action" in obligations and "permission" in caps and status == "supported"
    if bucket == "ambiguous_unsupported":
        return status in {"clarify", "unsupported"}
    if bucket == "mixed_multi_obligation":
        return len(obligations) >= 3 and status == "supported"
    return False


def rewrite_query(row: Mapping[str, object], client: OpenAICompatibleClient) -> str:
    prompt = {
        "source_query": row["query"],
        "category": row["category"],
        "expected_status": row["expected_status"],
        "gold_obligations": row["gold_obligations"],
        "required_capabilities": row["required_capabilities"],
        "risk_level": row["risk_level"],
        "natural_bucket": row["_natural_bucket"],
    }
    response = client.chat_json(
        [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=json.dumps(prompt, sort_keys=True)),
        ],
        temperature=0.2,
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    payload = parse_json_object(response.content)
    query = str(payload.get("query", "")).strip()
    if not query:
        return fallback_rewrite(row)
    return one_line(query)


def fallback_rewrite(row: Mapping[str, object]) -> str:
    return one_line(str(row["query"]).replace("For case", "For this request"))


def existing_rows(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row["task_id"] for row in load_jsonl(path)}


def write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
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
        "notes",
        "review_decision",
        "reviewer_notes",
        "revised_query",
        "revised_gold_obligations",
        "revised_required_capabilities",
        "revised_oracle_minimal_harness",
        "revised_expected_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task_id": row["task_id"],
                    "category": row["category"],
                    "query": one_line(row["query"]),
                    "gold_obligations": json.dumps(row["gold_obligations"]),
                    "required_capabilities": json.dumps(row["required_capabilities"]),
                    "oracle_minimal_harness": json.dumps(row["oracle_minimal_harness"]),
                    "expected_status": row["expected_status"],
                    "risk_level": row["risk_level"],
                    "gold_source": row["gold_source"],
                    "notes": one_line(row["notes"]),
                    "review_decision": "",
                    "reviewer_notes": "",
                    "revised_query": "",
                    "revised_gold_obligations": "",
                    "revised_required_capabilities": "",
                    "revised_oracle_minimal_harness": "",
                    "revised_expected_status": "",
                }
            )


def write_manifest(out_dir: Path, rows: Sequence[Mapping[str, object]]) -> None:
    manifest = {
        "dataset_name": "GapBench-Natural",
        "version": "v1.0-draft",
        "n_total": len(rows),
        "audit_status": "for_review",
        "gold_source": "naturalized_for_human_review_2026_06_22",
        "source_dataset": "GapBench v1.0",
        "composition": dict(COMPOSITION),
        "category_counts": dict(count(row["category"] for row in rows)),
        "intended_use": "naturalized evaluation of obligation inference beyond templated factorial queries",
        "not_intended_use": "final paper claims before human audit",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(
        """# GapBench-Natural v1.0 Draft

This package contains 200 naturalized GapBench examples for human review.

Audit status:

- `gapbench_natural_200_for_review.jsonl` is not yet human-audited.
- The labels are inherited from human-audited GapBench v1.0 source tasks.
- The user-facing queries were naturalized and should be reviewed before final paper claims.

Composition:

- 40 pure/direct language tasks
- 40 observation/evidence tasks
- 30 execution/computation tasks
- 30 file/workspace inspection tasks
- 20 sandbox action/permission tasks
- 20 ambiguous/unsupported tasks
- 20 mixed multi-obligation tasks

Use this dataset to test whether the obligation calculus transfers beyond templated controlled queries.
""",
        encoding="utf-8",
    )


def load_jsonl(path: Path) -> List[Mapping[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def count(values: Iterable[object]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for value in values:
        key = str(value)
        result[key] = result.get(key, 0) + 1
    return result


def one_line(value: object) -> str:
    return " ".join(str(value).split())


if __name__ == "__main__":
    raise SystemExit(main())
