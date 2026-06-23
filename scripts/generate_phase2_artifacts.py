"""Generate Phase 2 tables and lightweight SVG figures."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

from gapharness.evaluation import load_results, summarize_results


SYSTEM_ORDER = ["direct", "tool_router", "difficulty_router", "always_full", "gapharness", "oracle_minimal"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-results", default="outputs/results_gapbench1000_all_gold.jsonl")
    parser.add_argument("--gaia-results", default="outputs/results_gaia_transfer200_human_audited_gold.jsonl")
    parser.add_argument("--natural-results", default="outputs/results_gapbench_natural200_review_gold.jsonl")
    parser.add_argument("--out-dir", default="outputs/phase2")
    parser.add_argument("--fig-dir", default="figures/phase2")
    args = parser.parse_args(argv)

    rows = load_results(args.main_results)
    out_dir = Path(args.out_dir)
    fig_dir = Path(args.fig_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    summary = summarize_results(rows)
    (out_dir / "table1_gapbench1000_gold.md").write_text(render_summary_table(summary), encoding="utf-8")
    (out_dir / "table2_transfer_and_review_smokes.md").write_text(
        render_transfer_smoke_table(
            [
                ("GAIA-Transfer v1.0", Path(args.gaia_results), "human-audited gold"),
                ("GapBench-Natural v1.0 draft", Path(args.natural_results), "for human review"),
            ]
        ),
        encoding="utf-8",
    )
    (out_dir / "table3_category_breakdown.md").write_text(render_category_breakdown(rows), encoding="utf-8")
    (out_dir / "failure_mode_summary.md").write_text(render_failure_mode_summary(summary), encoding="utf-8")

    write_pipeline_svg(fig_dir / "pipeline.svg")
    write_cost_success_svg(fig_dir / "cost_success_frontier.svg", summary)
    write_failure_svg(fig_dir / "over_under_wrong_bars.svg", summary)
    write_regret_svg(fig_dir / "regret_distribution.svg", summary)
    write_drop_one_svg(fig_dir / "drop_one_necessity.svg", rows)

    print("wrote phase2 artifacts to", out_dir, "and", fig_dir)
    return 0


def render_summary_table(summary: Mapping[str, Mapping[str, float]]) -> str:
    lines = [
        "# Table 1. Controlled GapBench-1000 Results Under Gold Obligation Labels",
        "",
        "| System | N | Success | Avg Cost | Oracle Cost | Regret | Over | Under | Wrong | Redundancy |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in SYSTEM_ORDER:
        if system not in summary:
            continue
        item = summary[system]
        lines.append(
            "| %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |"
            % (
                system,
                item["n"],
                item["success_rate"],
                item["avg_cost"],
                item["avg_oracle_cost"],
                item["avg_minimality_regret"],
                item["over_harness_rate"],
                item["under_harness_rate"],
                item["wrong_harness_rate"],
                item["avg_redundancy"],
            )
        )
    return "\n".join(lines) + "\n"


def render_category_breakdown(rows: Sequence[Mapping[str, object]]) -> str:
    buckets: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        category = str(row["task"]["category"])
        system = str(row["system"])
        buckets[category][system].append(float(row["metrics"]["success"]))

    lines = [
        "# Table 3. Category Breakdown: Success Rate",
        "",
        "| Category | Direct | Tool Router | Difficulty | Always-full | GapHarness | Oracle |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for category in sorted(buckets):
        lines.append(
            "| %s | %s | %s | %s | %s | %s | %s |"
            % (
                category,
                fmt_mean(buckets[category].get("direct", [])),
                fmt_mean(buckets[category].get("tool_router", [])),
                fmt_mean(buckets[category].get("difficulty_router", [])),
                fmt_mean(buckets[category].get("always_full", [])),
                fmt_mean(buckets[category].get("gapharness", [])),
                fmt_mean(buckets[category].get("oracle_minimal", [])),
            )
        )
    return "\n".join(lines) + "\n"


def render_transfer_smoke_table(items: Sequence[tuple[str, Path, str]]) -> str:
    lines = [
        "# Table 2. Transfer and Naturalization Gold-Compiler Smokes",
        "",
        "| Dataset | Audit status | System | N | Success | Avg Cost | Oracle Cost | Regret |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for label, path, audit_status in items:
        if not path.exists():
            lines.append("| %s | %s | missing | 0 | - | - | - | - |" % (label, audit_status))
            continue
        summary = summarize_results(load_results(str(path)))
        for system in sorted(summary):
            item = summary[system]
            lines.append(
                "| %s | %s | %s | %.0f | %.2f | %.2f | %.2f | %.2f |"
                % (
                    label,
                    audit_status,
                    system,
                    item["n"],
                    item["success_rate"],
                    item["avg_cost"],
                    item["avg_oracle_cost"],
                    item["avg_minimality_regret"],
                )
            )
    return "\n".join(lines) + "\n"


def render_failure_mode_summary(summary: Mapping[str, Mapping[str, float]]) -> str:
    lines = [
        "# Failure Mode Summary",
        "",
        "| System | Over-harness | Under-harness | Wrong-harness |",
        "|---|---:|---:|---:|",
    ]
    for system in SYSTEM_ORDER:
        if system in summary:
            item = summary[system]
            lines.append(
                "| %s | %.2f | %.2f | %.2f |"
                % (system, item["over_harness_rate"], item["under_harness_rate"], item["wrong_harness_rate"])
            )
    return "\n".join(lines) + "\n"


def write_pipeline_svg(path: Path) -> None:
    labels = [
        "User Query",
        "Obligation Profiler",
        "Obligation Vector",
        "Module Registry",
        "Exact Compiler",
        "Executor + Trace",
        "Verifiers",
        "Minimality Report",
    ]
    width = 1180
    height = 160
    box_w = 130
    gap = 16
    parts = [svg_header(width, height)]
    x = 20
    for idx, label in enumerate(labels):
        parts.append(rect(x, 55, box_w, 48, "#eef2ff", "#334155"))
        parts.append(text(x + box_w / 2, 84, label, 12))
        if idx < len(labels) - 1:
            parts.append(line(x + box_w, 79, x + box_w + gap, 79))
        x += box_w + gap
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_cost_success_svg(path: Path, summary: Mapping[str, Mapping[str, float]]) -> None:
    points = []
    for system in SYSTEM_ORDER:
        if system in summary:
            item = summary[system]
            points.append((system, item["avg_cost"], item["success_rate"]))
    width, height = 640, 420
    margin = 55
    max_cost = max(cost for _, cost, _ in points) or 1.0
    parts = [svg_header(width, height), axes(width, height, margin, "Avg cost", "Success")]
    for system, cost, success in points:
        x = margin + cost / max_cost * (width - 2 * margin)
        y = height - margin - success * (height - 2 * margin)
        parts.append(circle(x, y, 5, color_for(system)))
        parts.append(text(x + 8, y - 6, system, 11, anchor="start"))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_failure_svg(path: Path, summary: Mapping[str, Mapping[str, float]]) -> None:
    systems = [system for system in SYSTEM_ORDER if system in summary]
    series = ["over_harness_rate", "under_harness_rate", "wrong_harness_rate"]
    colors = ["#ef4444", "#f59e0b", "#3b82f6"]
    width, height = 760, 420
    margin = 55
    bar_w = 55
    parts = [svg_header(width, height), axes(width, height, margin, "System", "Rate")]
    step = (width - 2 * margin) / len(systems)
    for i, system in enumerate(systems):
        x = margin + i * step + step / 2 - bar_w / 2
        y_base = height - margin
        current = 0.0
        for key, color in zip(series, colors):
            value = float(summary[system][key])
            h = value * (height - 2 * margin)
            parts.append(rect(x, y_base - current - h, bar_w, h, color, color))
            current += h
        parts.append(text(x + bar_w / 2, height - 28, system, 10))
    parts.append(legend(width - 190, 30, [("Over", colors[0]), ("Under", colors[1]), ("Wrong", colors[2])]))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_regret_svg(path: Path, summary: Mapping[str, Mapping[str, float]]) -> None:
    systems = [system for system in SYSTEM_ORDER if system in summary]
    values = [float(summary[system]["avg_minimality_regret"]) for system in systems]
    width, height = 760, 420
    margin = 60
    min_v = min(values + [0.0])
    max_v = max(values + [0.0])
    scale = max(max_v - min_v, 1.0)
    zero_y = height - margin - (0.0 - min_v) / scale * (height - 2 * margin)
    parts = [svg_header(width, height), axes(width, height, margin, "System", "Avg regret")]
    parts.append(line(margin, zero_y, width - margin, zero_y, "#64748b"))
    step = (width - 2 * margin) / len(systems)
    for i, system in enumerate(systems):
        value = float(summary[system]["avg_minimality_regret"])
        x = margin + i * step + step / 2 - 24
        y = height - margin - (value - min_v) / scale * (height - 2 * margin)
        h = abs(y - zero_y)
        parts.append(rect(x, min(y, zero_y), 48, h, color_for(system), color_for(system)))
        parts.append(text(x + 24, height - 28, system, 10))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def write_drop_one_svg(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    values: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        system = str(row["system"])
        redundancy = float(row["metrics"].get("redundancy", 0.0))
        values[system].append(1.0 - redundancy)
    summary = {system: sum(items) / len(items) for system, items in values.items() if items}
    systems = [system for system in SYSTEM_ORDER if system in summary]
    width, height = 760, 420
    margin = 55
    parts = [svg_header(width, height), axes(width, height, margin, "System", "Necessity rate")]
    step = (width - 2 * margin) / len(systems)
    for i, system in enumerate(systems):
        value = summary[system]
        x = margin + i * step + step / 2 - 24
        h = value * (height - 2 * margin)
        parts.append(rect(x, height - margin - h, 48, h, color_for(system), color_for(system)))
        parts.append(text(x + 24, height - 28, system, 10))
    parts.append("</svg>\n")
    path.write_text("".join(parts), encoding="utf-8")


def fmt_mean(values: Sequence[float]) -> str:
    if not values:
        return "-"
    return "%.2f" % (sum(values) / len(values))


def color_for(system: str) -> str:
    return {
        "direct": "#64748b",
        "tool_router": "#3b82f6",
        "difficulty_router": "#8b5cf6",
        "always_full": "#ef4444",
        "gapharness": "#16a34a",
        "oracle_minimal": "#0f766e",
    }.get(system, "#334155")


def svg_header(width: int, height: int) -> str:
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n<rect width="100%%" height="100%%" fill="white"/>\n' % (width, height, width, height)


def axes(width: int, height: int, margin: int, x_label: str, y_label: str) -> str:
    return (
        line(margin, height - margin, width - margin, height - margin)
        + line(margin, margin, margin, height - margin)
        + text(width / 2, height - 8, x_label, 12)
        + text(18, height / 2, y_label, 12, rotate=-90)
    )


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str) -> str:
    return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="4" fill="%s" stroke="%s"/>\n' % (x, y, w, max(h, 0), fill, stroke)


def line(x1: float, y1: float, x2: float, y2: float, color: str = "#334155") -> str:
    return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="1.5"/>\n' % (x1, y1, x2, y2, color)


def circle(x: float, y: float, r: float, fill: str) -> str:
    return '<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/>\n' % (x, y, r, fill)


def text(x: float, y: float, value: str, size: int, anchor: str = "middle", rotate: int | None = None) -> str:
    transform = ' transform="rotate(%d %.2f %.2f)"' % (rotate, x, y) if rotate is not None else ""
    return '<text x="%.2f" y="%.2f" font-family="Arial, sans-serif" font-size="%d" text-anchor="%s"%s>%s</text>\n' % (
        x,
        y,
        size,
        anchor,
        transform,
        escape(value),
    )


def legend(x: float, y: float, items: Sequence[tuple[str, str]]) -> str:
    parts = []
    for idx, (label, color) in enumerate(items):
        yy = y + idx * 22
        parts.append(rect(x, yy - 10, 12, 12, color, color))
        parts.append(text(x + 20, yy, label, 12, anchor="start"))
    return "".join(parts)


def escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    raise SystemExit(main())
