"""Render combined HarnessChallenge-200 diagnostic tables."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.evaluation import load_results, summarize_results


DEFAULT_INPUTS = (
    ("deterministic_gold", "outputs/final/results_harness_challenge200_author_reviewed_gold.jsonl"),
    ("gapharness_llm", "outputs/final/harness_challenge200_llm/results_dev200_llm_single.jsonl"),
    ("registry_guarded_gapharness", "outputs/final/harness_challenge200_registry_guarded/results_dev200_llm_registry_guarded.jsonl"),
    ("llm_tool_router", "outputs/phase4/llm_tool_router_harness_challenge200/results_llm_tool_router.jsonl"),
)

SYSTEM_ORDER = (
    "direct",
    "tool_router",
    "difficulty_router",
    "always_full",
    "llm_tool_router",
    "gapharness_gold",
    "gapharness_llm",
    "registry_guarded_gapharness",
    "oracle_minimal",
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="outputs/final/harness_challenge200_diagnostic_report.md")
    parser.add_argument("--paper-table", default="paper/tables/table9_harness_challenge200.md")
    args = parser.parse_args(argv)

    rows = load_combined_rows(DEFAULT_INPUTS)
    report = render_report(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    table = Path(args.paper_table)
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(render_compact_table(rows), encoding="utf-8")
    print("wrote HarnessChallenge report to %s and %s" % (out, table))
    return 0


def load_combined_rows(inputs: Sequence[tuple[str, str]]) -> list[dict[str, object]]:
    combined: list[dict[str, object]] = []
    for label, path in inputs:
        for row in load_results(path):
            copied = dict(row)
            if label == "deterministic_gold" and row["system"] == "gapharness":
                copied["system"] = "gapharness_gold"
            elif label != "deterministic_gold":
                copied["system"] = label
            copied["source_result"] = path
            combined.append(copied)
    return combined


def render_report(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# HarnessChallenge-200 Targeted Diagnostic Report",
        "",
        "HarnessChallenge-200 is a targeted diagnostic benchmark. It is not a natural-frequency benchmark and does not measure final answer correctness.",
        "",
        "## Aggregate Results",
        "",
    ]
    lines.extend(render_table_lines(rows))
    lines.extend(
        [
            "",
            "## Category Breakdown: Harness Success",
            "",
            "| Category | Direct | Tool Router | Difficulty | Always-full | LLM Tool Router | GH Gold | GH LLM | Registry-guarded GH |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    categories = sorted({str(row["task"]["category"]) for row in rows})
    wanted = (
        "direct",
        "tool_router",
        "difficulty_router",
        "always_full",
        "llm_tool_router",
        "gapharness_gold",
        "gapharness_llm",
        "registry_guarded_gapharness",
    )
    for category in categories:
        parts = [category]
        for system in wanted:
            bucket = [
                row
                for row in rows
                if row["system"] == system and str(row["task"]["category"]) == category
            ]
            parts.append(fmt(mean(row["metrics"]["success"] for row in bucket)) if bucket else "-")
        lines.append("| %s |" % " | ".join(parts))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- GapHarness gold and oracle minimal reach 1.00 because labels and registry declarations are sufficient and minimal.",
            "- LLM Tool Router sees the same registry and costs but not obligation labels; it under-covers minimal pairs, verification traps, and real-source paraphrases.",
            "- The registry guard was calibrated on GapBench and does not solve this harder targeted diagnostic set; this is reported as a boundary result rather than a positive-only ablation.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_compact_table(rows: Sequence[Mapping[str, object]]) -> str:
    lines = [
        "# Table 9. HarnessChallenge-200 Targeted Diagnostic",
        "",
    ]
    lines.extend(render_table_lines(rows))
    return "\n".join(lines) + "\n"


def render_table_lines(rows: Sequence[Mapping[str, object]]) -> list[str]:
    summary = summarize_results(rows)
    lines = [
        "| System | N | HS | Cost | Delta | Excess | Over | Under | Wrong |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in SYSTEM_ORDER:
        if system not in summary:
            continue
        item = summary[system]
        lines.append(
            "| %s | %.0f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |"
            % (
                display_system(system),
                item["n"],
                item["success_rate"],
                item["avg_cost"],
                item["avg_cost_delta"],
                item["avg_excess_cost"],
                item["over_harness_rate"],
                item["under_harness_rate"],
                item["wrong_harness_rate"],
            )
        )
    return lines


def display_system(system: str) -> str:
    mapping = {
        "direct": "Direct",
        "tool_router": "Tool Router",
        "difficulty_router": "Difficulty Router",
        "always_full": "Always-full",
        "llm_tool_router": "LLM Tool Router",
        "gapharness_gold": "GapHarness gold",
        "gapharness_llm": "GapHarness LLM",
        "registry_guarded_gapharness": "Registry-guarded GH",
        "oracle_minimal": "Oracle minimal",
    }
    return mapping.get(system, system)


def mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / float(len(values_list))


def fmt(value: float) -> str:
    return "%.2f" % value


if __name__ == "__main__":
    raise SystemExit(main())
