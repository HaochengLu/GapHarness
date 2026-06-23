"""Write the synthetic GapBench-Factorial seed benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gapharness.seed_data import build_seed_tasks


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="benchmarks/gapbench_factorial_seed.jsonl")
    args = parser.parse_args(argv)

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for task in build_seed_tasks():
            handle.write(json.dumps(task.to_json(), sort_keys=True) + "\n")
    print("wrote 100 tasks to %s" % output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
