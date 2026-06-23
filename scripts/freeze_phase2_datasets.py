"""Freeze Phase 2 benchmark assets into versioned directories."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping


OBLIGATIONS = ["Observation", "Execution", "State", "Action", "Control", "Verification"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gapbench-1000", default="benchmarks/gapbench_1000_human_audited.jsonl")
    parser.add_argument("--gapbench-500", default="benchmarks/gapbench_500_human_audited.jsonl")
    parser.add_argument("--gaia-validation100", default="benchmarks/gaia_validation_100_human_audited.jsonl")
    parser.add_argument("--gaia-test100", default="benchmarks/gaia_test_100_human_audited.jsonl")
    parser.add_argument("--gaia-transfer200", default="benchmarks/gaia_transfer_200_human_audited.jsonl")
    args = parser.parse_args(argv)

    freeze_gapbench(Path(args.gapbench_1000), Path(args.gapbench_500))
    freeze_gaia(
        Path(args.gaia_validation100),
        Path(args.gaia_test100),
        Path(args.gaia_transfer200),
    )
    return 0


def freeze_gapbench(path1000: Path, path500: Path) -> None:
    rows1000 = load_jsonl(path1000)
    rows500 = load_jsonl(path500)
    base = Path("benchmarks/gapbench/v1.0")
    split_dir = base / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(base / "gapbench_1000_human_audited.jsonl", rows1000)
    write_jsonl(base / "gapbench_500_human_audited.jsonl", rows500)

    dev, test = stratified_split(rows1000, dev_size=200)
    write_jsonl(split_dir / "dev200.jsonl", dev)
    write_jsonl(split_dir / "test800.jsonl", test)

    manifest = {
        "dataset_name": "GapBench",
        "version": "v1.0",
        "n_total": len(rows1000),
        "n_subset_500": len(rows500),
        "splits": {"dev200": len(dev), "test800": len(test)},
        "audit_status": "human_audited_confirmed",
        "audit_date": "2026-06-22",
        "gold_source": "human_audited_confirmed_2026_06_22_gapbench_expansion",
        "obligation_set": OBLIGATIONS,
        "success_checker": "gold_obligation_capability_coverage",
        "category_counts": dict(Counter(row["category"] for row in rows1000)),
        "intended_use": "controlled factorial evaluation of obligation coverage and minimal harness compilation",
        "not_intended_use": "claiming full real-world answer-level accuracy or open-world task completion",
        "notes": "Controlled and factorial by design; use dev split for profiler calibration and test split for final reporting.",
    }
    write_json(base / "manifest.json", manifest)
    write_schema(base / "schema.md", rows1000[0])
    (base / "audit_log.md").write_text(
        """# GapBench v1.0 Audit Log

- 2026-06-22: Project owner confirmed all 1000 labels as gold truth.
- 2026-06-22: Dataset frozen as `benchmarks/gapbench/v1.0`.
- 2026-06-22: Split policy frozen: stratified dev200/test800 by category.

## Positioning

GapBench-1000 is controlled and factorial by design. Its purpose is not to measure open-world assistant performance, but to isolate over-harnessing, under-harnessing, wrong-harnessing, and minimality regret under known obligation labels.
""",
        encoding="utf-8",
    )
    print("froze GapBench v1.0", len(rows1000), "rows")


def freeze_gaia(validation_path: Path, test_path: Path, transfer_path: Path) -> None:
    validation = load_jsonl(validation_path)
    test = load_jsonl(test_path)
    transfer = load_jsonl(transfer_path)
    base = Path("benchmarks/gaia_transfer/v1.0")
    base.mkdir(parents=True, exist_ok=True)

    write_jsonl(base / "gaia_validation100_human_audited.jsonl", validation)
    write_jsonl(base / "gaia_test100_human_audited.jsonl", test)
    write_jsonl(base / "gaia_transfer200_human_audited.jsonl", transfer)

    manifest = {
        "dataset_name": "GAIA-Transfer",
        "version": "v1.0",
        "source_dataset": "gaia-benchmark/GAIA",
        "source_config": "2023_all",
        "n_total": len(transfer),
        "splits": {"validation100": len(validation), "test100": len(test)},
        "audit_status": "project_owner_audited_confirmed",
        "audit_date": "2026-06-22",
        "gold_source": "project_owner_audited_confirmed_2026_06_22_gaia_transfer_200",
        "audit_note": "Project owner confirmed the validation100 plus test100 obligation-transfer labels as gold truth on 2026-06-22. This is obligation-transfer gold, not GAIA answer-level correctness.",
        "obligation_set": OBLIGATIONS,
        "success_checker": "gaia_obligation_transfer_only",
        "category_counts": dict(Counter(row["category"] for row in transfer)),
        "intended_use": "obligation-transfer evaluation on real assistant benchmark queries",
        "not_intended_use": "claiming full GAIA answer-level accuracy without executing answer attempts",
    }
    write_json(base / "manifest.json", manifest)
    write_schema(base / "schema.md", transfer[0])
    (base / "audit_log.md").write_text(
        """# GAIA-Transfer v1.0 Audit Log

- 2026-06-22: `load_dataset("gaia-benchmark/GAIA", "2023_all")` succeeded locally.
- 2026-06-22: Project owner confirmed validation100/test100 transfer labels as gold truth.
- 2026-06-22: Dataset frozen as `benchmarks/gaia_transfer/v1.0`.

## Positioning

GAIA-Transfer v1.0 tests whether the obligation ontology and minimal harness compiler transfer to real assistant benchmark queries. It is not a full answer-level GAIA score.
""",
        encoding="utf-8",
    )
    print("froze GAIA-Transfer v1.0", len(transfer), "rows")


def stratified_split(rows: List[Mapping[str, object]], dev_size: int) -> tuple[List[Mapping[str, object]], List[Mapping[str, object]]]:
    by_category: Dict[str, List[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        by_category[str(row["category"])].append(row)

    total = len(rows)
    dev: List[Mapping[str, object]] = []
    for category, category_rows in sorted(by_category.items()):
        quota = round(len(category_rows) * dev_size / total)
        dev.extend(category_rows[:quota])
    while len(dev) < dev_size:
        for category_rows in by_category.values():
            for row in category_rows:
                if row not in dev:
                    dev.append(row)
                    break
            if len(dev) >= dev_size:
                break
    dev_ids = {row["task_id"] for row in dev[:dev_size]}
    test = [row for row in rows if row["task_id"] not in dev_ids]
    return list(dev[:dev_size]), test


def write_schema(path: Path, sample: Mapping[str, object]) -> None:
    lines = [
        "# Schema",
        "",
        "| Field | Type / Description |",
        "|---|---|",
    ]
    descriptions = {
        "task_id": "Stable task identifier.",
        "query": "User-facing task query.",
        "gold_obligations": "Human-audited external obligations.",
        "required_capabilities": "Capabilities required from selected modules.",
        "oracle_minimal_harness": "Human-audited or compiled oracle minimal module set under the declared registry.",
        "success_checker": "Verifier contract used for this task.",
        "expected_failure_if_direct": "Expected failure mode for direct LLM response.",
        "risk_level": "low / medium / high.",
        "category": "Dataset category.",
        "expected_status": "supported / unsupported / clarify.",
        "tags": "Auxiliary tags.",
        "notes": "Audit and provenance notes.",
        "gold_source": "Gold label provenance.",
    }
    for key in sample:
        lines.append("| `%s` | %s |" % (key, descriptions.get(key, "Dataset field.")))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> List[Mapping[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
