"""Build larger GAIA transfer review packages.

The output labels are auto-profiled and intentionally stamped for review, not
as human-audited gold.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List

from gapharness.compiler import compile_minimal_harness
from gapharness.llm_profiler import canonicalize_profile
from gapharness.profiler import profile_heuristic
from gapharness.registry import default_registry
from gapharness.schema import ProfilerOutput, TaskExample


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--out-dir", default="gaia_transfer_review_package")
    parser.add_argument("--splits", nargs="+", default=["validation", "test"], choices=["validation", "test"])
    args = parser.parse_args(argv)

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise SystemExit("Missing HF_TOKEN or HUGGINGFACE_TOKEN.")

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install datasets before running this script.") from exc

    ds = load_dataset("gaia-benchmark/GAIA", "2023_all", token=token)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_on": "2026-06-22",
        "source": "gaia-benchmark/GAIA",
        "config": "2023_all",
        "audit_status": "for_review",
        "gold_source": "gaia_metadata_auto_profile_for_review_2026_06_22",
        "splits": {},
    }

    for split in args.splits:
        rows = build_rows(ds[split], split, args.limit)
        jsonl_path = out_dir / ("gaia_%s_%d_for_review.jsonl" % (split, len(rows)))
        csv_path = out_dir / ("gaia_%s_%d_review_sheet.csv" % (split, len(rows)))
        write_jsonl(jsonl_path, rows)
        write_csv(csv_path, rows)
        manifest["splits"][split] = {
            "count": len(rows),
            "jsonl": jsonl_path.name,
            "csv": csv_path.name,
        }
        print("wrote", split, len(rows), jsonl_path, csv_path)

    (out_dir / "gaia_transfer_review_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("wrote manifest", out_dir / "gaia_transfer_review_manifest.json")
    return 0


def build_rows(dataset, split: str, limit: int) -> List[TaskExample]:
    selected = stratified_take(list(dataset), limit)
    registry = default_registry()
    rows: List[TaskExample] = []
    for index, row in enumerate(selected, start=1):
        query = str(row.get("Question") or "")
        file_name = row.get("file_name") or ""
        file_path = row.get("file_path") or ""
        profile = profile_heuristic(query)
        if file_name or file_path:
            profile = canonicalize_profile(profile, query + " attached file workspace artifact")
        profile = ProfilerOutput(
            direct_llm_sufficient=profile.direct_llm_sufficient,
            obligations=profile.obligations,
            required_capabilities=profile.required_capabilities,
            output_contract=profile.output_contract,
            forbidden_paths=profile.forbidden_paths,
            risk_level=profile.risk_level,
            unsupported_possibility=(),
            rationale=profile.rationale + " [gaia_supported_task]",
        )
        oracle = compile_minimal_harness(profile, registry).modules
        level = str(row.get("Level") or "")
        source_task_id = str(row.get("task_id") or "")
        rows.append(
            TaskExample(
                task_id="gaia-%s-review-%03d" % (split, index),
                query=query,
                gold_obligations=profile.obligations,
                required_capabilities=profile.required_capabilities,
                oracle_minimal_harness=oracle,
                success_checker="gaia_obligation_transfer_only",
                expected_failure_if_direct="missing_external_obligations",
                risk_level=profile.risk_level,
                category="gaia_transfer_level_%s" % level,
                expected_status="supported",
                tags=("gaia", split, "for_review", "source_task_id:%s" % source_task_id),
                notes=(
                    "Auto-profiled GAIA transfer label for review; source_task_id=%s; "
                    "file_name=%s"
                )
                % (source_task_id, file_name),
                gold_source="gaia_metadata_auto_profile_for_review_2026_06_22",
            )
        )
    return rows


def stratified_take(rows: List[Dict[str, object]], limit: int) -> List[Dict[str, object]]:
    buckets: Dict[tuple, List[Dict[str, object]]] = {}
    for row in rows:
        key = (str(row.get("Level") or ""), bool(row.get("file_name") or row.get("file_path")))
        buckets.setdefault(key, []).append(row)

    selected: List[Dict[str, object]] = []
    keys = sorted(buckets)
    while len(selected) < limit and keys:
        progressed = False
        for key in keys:
            bucket = buckets[key]
            if bucket:
                selected.append(bucket.pop(0))
                progressed = True
                if len(selected) >= limit:
                    break
        if not progressed:
            break
    return selected


def write_jsonl(path: Path, rows: Iterable[TaskExample]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_json(), sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[TaskExample]) -> None:
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
        "revised_gold_obligations",
        "revised_required_capabilities",
        "revised_oracle_minimal_harness",
        "revised_expected_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            data = row.to_json()
            writer.writerow(
                {
                    "task_id": data["task_id"],
                    "category": data["category"],
                    "query": one_line(data["query"]),
                    "gold_obligations": json.dumps(data["gold_obligations"]),
                    "required_capabilities": json.dumps(data["required_capabilities"]),
                    "oracle_minimal_harness": json.dumps(data["oracle_minimal_harness"]),
                    "expected_status": data["expected_status"],
                    "risk_level": data["risk_level"],
                    "gold_source": data["gold_source"],
                    "notes": one_line(data["notes"]),
                    "review_decision": "",
                    "reviewer_notes": "",
                    "revised_gold_obligations": "",
                    "revised_required_capabilities": "",
                    "revised_oracle_minimal_harness": "",
                    "revised_expected_status": "",
                }
            )


def one_line(value: object) -> str:
    return " ".join(str(value).split())


if __name__ == "__main__":
    raise SystemExit(main())
