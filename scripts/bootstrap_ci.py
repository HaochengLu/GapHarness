"""Bootstrap confidence intervals for GapHarness result JSONL files."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


DEFAULT_METRICS = (
    "success",
    "predicted_cost",
    "cost_delta",
    "excess_cost",
    "over_harness",
    "under_harness",
    "wrong_harness",
    "trace_success",
    "pre_test_failed",
    "post_test_passed",
    "missing_required_modules",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result",
        action="append",
        required=True,
        help="Label and path as label:path. May be repeated.",
    )
    parser.add_argument("--out-dir", default="outputs/final/bootstrap_ci")
    parser.add_argument("--samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ci_rows = []
    for spec in args.result:
        label, path = parse_result_spec(spec)
        rows = load_jsonl(path)
        ci_rows.extend(compute_file_ci(label, path, rows, args.samples, rng))

    write_csv(out_dir / "bootstrap_ci.csv", ci_rows)
    write_jsonl(out_dir / "bootstrap_ci.jsonl", ci_rows)
    (out_dir / "bootstrap_ci_report.md").write_text(render_report(ci_rows, args.samples, args.seed), encoding="utf-8")
    print("wrote bootstrap CI report to %s" % out_dir)
    return 0


def parse_result_spec(spec: str) -> tuple[str, Path]:
    if ":" not in spec:
        raise SystemExit("--result must be label:path, got %s" % spec)
    label, path = spec.split(":", 1)
    return label, Path(path)


def load_jsonl(path: Path) -> list[Mapping[str, object]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def compute_file_ci(
    label: str,
    path: Path,
    rows: Sequence[Mapping[str, object]],
    samples: int,
    rng: random.Random,
) -> list[dict[str, object]]:
    by_system: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        by_system[str(row["system"])].append(row)

    out = []
    for system, bucket in sorted(by_system.items()):
        metrics = available_metrics(bucket)
        for metric in metrics:
            point = metric_mean(bucket, metric)
            draws = []
            n = len(bucket)
            for _ in range(samples):
                sample = [bucket[rng.randrange(n)] for _ in range(n)]
                draws.append(metric_mean(sample, metric))
            draws.sort()
            out.append(
                {
                    "dataset": label,
                    "path": str(path),
                    "system": system,
                    "metric": metric,
                    "n": n,
                    "point": point,
                    "ci_low": percentile(draws, 0.025),
                    "ci_high": percentile(draws, 0.975),
                    "samples": samples,
                }
            )
    return out


def available_metrics(rows: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    seen = set()
    for row in rows:
        metrics = row.get("metrics") or row.get("coverage_metrics") or {}
        if isinstance(metrics, Mapping):
            seen.update(metrics.keys())
        exec_metrics = row.get("exec_metrics") or {}
        if isinstance(exec_metrics, Mapping):
            seen.update(exec_metrics.keys())
    return tuple(metric for metric in DEFAULT_METRICS if metric in seen)


def metric_mean(rows: Sequence[Mapping[str, object]], metric: str) -> float:
    values = []
    for row in rows:
        metrics = row.get("metrics") or row.get("coverage_metrics") or {}
        if isinstance(metrics, Mapping) and metric in metrics:
            values.append(float(metrics[metric]))
            continue
        exec_metrics = row.get("exec_metrics") or {}
        if isinstance(exec_metrics, Mapping) and metric in exec_metrics:
            value = exec_metrics[metric]
            if isinstance(value, list):
                values.append(float(bool(value)))
            else:
                values.append(float(value))
    return sum(values) / float(len(values)) if values else 0.0


def percentile(sorted_values: Sequence[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = quantile * (len(sorted_values) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    fieldnames = ["dataset", "path", "system", "metric", "n", "point", "ci_low", "ci_high", "samples"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def render_report(rows: Sequence[Mapping[str, object]], samples: int, seed: int) -> str:
    lines = [
        "# Bootstrap Confidence Intervals",
        "",
        "Nonparametric bootstrap over task rows within each system. Intervals are 95%% percentile intervals with %d resamples and seed %d."
        % (samples, seed),
        "",
        "| Dataset | System | Metric | N | Point | 95% CI |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        if row["metric"] not in set(DEFAULT_METRICS):
            continue
        lines.append(
            "| %s | %s | %s | %d | %.3f | [%.3f, %.3f] |"
            % (
                row["dataset"],
                row["system"],
                row["metric"],
                row["n"],
                row["point"],
                row["ci_low"],
                row["ci_high"],
            )
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
