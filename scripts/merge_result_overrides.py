"""Merge JSONL result rows, replacing base rows with override rows by task/system."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--override", action="append", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    rows = {}
    order = []
    for row in _load(args.base):
        key = _key(row)
        rows[key] = row
        order.append(key)
    for override_path in args.override:
        for row in _load(override_path):
            key = _key(row)
            rows[key] = row
            if key not in order:
                order.append(key)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for key in order:
            handle.write(json.dumps(rows[key], sort_keys=True) + "\n")
    print("wrote %d merged rows to %s" % (len(order), args.out))
    return 0


def _load(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _key(row):
    return (row.get("task_id"), row.get("system"))


if __name__ == "__main__":
    raise SystemExit(main())
