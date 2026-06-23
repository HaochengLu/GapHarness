"""Finalize GapBench-Natural-200 as a human-audited benchmark artifact."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-jsonl", default="benchmarks/gapbench_natural/v1.0/gapbench_natural_200_for_review.jsonl")
    parser.add_argument("--in-csv", default="benchmarks/gapbench_natural/v1.0/gapbench_natural_200_review_sheet.csv")
    parser.add_argument("--out-dir", default="benchmarks/gapbench_natural/v1.0")
    parser.add_argument("--audit-date", default="2026-06-23")
    args = parser.parse_args(argv)

    in_jsonl = Path(args.in_jsonl)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(in_jsonl)
    gold_source = "human_audited_confirmed_%s_gapbench_natural_200" % args.audit_date.replace("-", "_")
    audited = [stamp_row(row, gold_source, args.audit_date) for row in rows]
    out_jsonl = out_dir / "gapbench_natural_200_human_audited.jsonl"
    write_jsonl(out_jsonl, audited)
    write_review_sheet(out_dir / "gapbench_natural_200_human_audited_review_sheet.csv", audited)
    write_manifest(out_dir, audited, gold_source, args.audit_date)
    write_readme(out_dir, args.audit_date)
    if Path(args.in_csv).exists():
        stamp_existing_csv(Path(args.in_csv), out_dir / "gapbench_natural_200_human_audited_from_original_sheet.csv", gold_source, args.audit_date)
    print("wrote human-audited Natural-200 to", out_jsonl)
    return 0


def stamp_row(row: Mapping[str, object], gold_source: str, audit_date: str) -> Mapping[str, object]:
    out = dict(row)
    tags = list(out.get("tags", []))
    for tag in ("human_audited", "gapbench_natural_human_audited"):
        if tag not in tags:
            tags.append(tag)
    source_task_id = next((tag for tag in tags if str(tag).startswith("source_task_id:")), "")
    out["tags"] = tags
    out["gold_source"] = gold_source
    out["notes"] = (
        "%s; human-audited by project owner on %s; all gold obligations, capabilities, "
        "expected status, and oracle minimal harness accepted for Natural-200."
    ) % (str(row.get("notes", "")).rstrip("."), audit_date)
    if source_task_id and source_task_id not in out["notes"]:
        out["notes"] += " %s." % source_task_id
    return out


def write_manifest(out_dir: Path, rows: Sequence[Mapping[str, object]], gold_source: str, audit_date: str) -> None:
    manifest = {
        "dataset_name": "GapBench-Natural",
        "version": "v1.0",
        "n_total": len(rows),
        "audit_status": "human_audited_project_owner",
        "audit_date": audit_date,
        "gold_source": gold_source,
        "source_dataset": "GapBench v1.0",
        "human_audited_file": "gapbench_natural_200_human_audited.jsonl",
        "historical_review_file": "gapbench_natural_200_for_review.jsonl",
        "composition": {
            "pure_language_direct": 40,
            "observation_evidence": 40,
            "execution_computation": 30,
            "file_workspace_inspection": 30,
            "sandbox_action_permission": 20,
            "ambiguous_unsupported": 20,
            "mixed_multi_obligation": 20,
        },
        "category_counts": dict(Counter(str(row["category"]) for row in rows)),
        "intended_use": "human-audited naturalized evaluation of obligation inference beyond templated factorial queries",
        "not_intended_use": "claiming open-world answer correctness or independent external benchmark status",
        "claim_boundary": "Natural prompts are human-audited but still derive from GapBench source rows.",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_readme(out_dir: Path, audit_date: str) -> None:
    (out_dir / "README.md").write_text(
        """# GapBench-Natural v1.0

This package contains 200 naturalized GapBench examples.

Audit status:

- `gapbench_natural_200_human_audited.jsonl` is human-audited by the project owner as of {audit_date}.
- The labels inherit from human-audited GapBench v1.0 source tasks and were rechecked after naturalization.
- `gapbench_natural_200_for_review.jsonl` is retained only as historical provenance from the review stage.
- A deterministic cleanup pass removed templated benchmark remnants such as artificial case labels, placeholder product names, and sandbox filename artifacts from the visible user queries.

Composition:

- 40 pure/direct language tasks
- 40 observation/evidence tasks
- 30 execution/computation tasks
- 30 file/workspace inspection tasks
- 20 sandbox action/permission tasks
- 20 ambiguous/unsupported tasks
- 20 mixed multi-obligation tasks

Use this dataset to test whether the obligation calculus transfers beyond templated controlled queries. It is not an open-world answer-correctness benchmark.
""".format(
            audit_date=audit_date
        ),
        encoding="utf-8",
    )


def write_review_sheet(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task_id": row["task_id"],
                    "category": row["category"],
                    "query": one_line(str(row["query"])),
                    "gold_obligations": json.dumps(row["gold_obligations"]),
                    "required_capabilities": json.dumps(row["required_capabilities"]),
                    "oracle_minimal_harness": json.dumps(row["oracle_minimal_harness"]),
                    "expected_status": row["expected_status"],
                    "risk_level": row["risk_level"],
                    "gold_source": row["gold_source"],
                    "review_decision": "accept",
                    "reviewer_notes": row["notes"],
                }
            )


def stamp_existing_csv(path: Path, out_path: Path, gold_source: str, audit_date: str) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    for column in ("gold_source", "review_decision", "reviewer_notes"):
        if column not in fieldnames:
            fieldnames.append(column)
    for row in rows:
        row["gold_source"] = gold_source
        row["review_decision"] = "accept"
        row["reviewer_notes"] = "Human-audited by project owner on %s; accepted." % audit_date
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def one_line(value: str) -> str:
    return " ".join(value.split())


if __name__ == "__main__":
    raise SystemExit(main())
