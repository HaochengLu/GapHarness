"""Stamp benchmark JSONL/CSV files with human audit status."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", action="append", default=[])
    parser.add_argument("--csv", action="append", default=[])
    parser.add_argument("--gold-source", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--review-decision", default="accept")
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args(argv)

    for path in args.jsonl:
        stamp_jsonl(Path(path), args.gold_source, args.notes, args.out_dir)
    for path in args.csv:
        stamp_csv(Path(path), args.gold_source, args.notes, args.review_decision, args.out_dir)
    return 0


def stamp_jsonl(path: Path, gold_source: str, notes: str, out_dir: str | None) -> None:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["gold_source"] = gold_source
            row["notes"] = notes
            rows.append(row)

    output = _output_path(path, out_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print("stamped jsonl", output, len(rows))


def stamp_csv(path: Path, gold_source: str, notes: str, review_decision: str, out_dir: str | None) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for column in ("gold_source", "notes", "review_decision", "reviewer_notes"):
        if column not in fieldnames:
            fieldnames.append(column)

    for row in rows:
        row["gold_source"] = gold_source
        row["notes"] = notes
        row["review_decision"] = review_decision
        row["reviewer_notes"] = notes

    output = _output_path(path, out_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("stamped csv", output, len(rows))


def _output_path(path: Path, out_dir: str | None) -> Path:
    if out_dir is None:
        return path
    return Path(out_dir) / path.name


if __name__ == "__main__":
    raise SystemExit(main())
