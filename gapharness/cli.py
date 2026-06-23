"""Command-line interface for GapHarness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .compiler import compile_minimal_harness
from .evaluation import (
    load_results,
    profiler_confusion,
    render_markdown_report,
    run_benchmark,
    run_benchmark_streaming,
    write_jsonl,
)
from .profiler import profile_heuristic
from .registry import default_registry


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gapharness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile a harness for one query.")
    compile_parser.add_argument("query")
    compile_parser.add_argument(
        "--profiler",
        default="heuristic",
        choices=["heuristic", "llm", "consensus", "llm_single", "llm_recall", "llm_minimality", "llm_cascade"],
    )

    run_parser = subparsers.add_parser("run-benchmark", help="Run benchmark systems.")
    run_parser.add_argument("--benchmark", required=True)
    run_parser.add_argument("--system", default="all")
    run_parser.add_argument(
        "--profiler",
        default="gold",
        choices=["gold", "heuristic", "llm", "consensus", "llm_single", "llm_recall", "llm_minimality", "llm_cascade"],
    )
    run_parser.add_argument("--out", required=True)
    run_parser.add_argument("--stream", action="store_true", help="Write each row as soon as it completes.")
    run_parser.add_argument("--no-resume", action="store_true", help="Do not skip rows already present in --out.")
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.add_argument("--start", type=int, default=0)
    run_parser.add_argument("--progress-every", type=int, default=5)

    report_parser = subparsers.add_parser("make-report", help="Render a Markdown summary.")
    report_parser.add_argument("--results", required=True)
    report_parser.add_argument("--out", required=True)

    profiler_report_parser = subparsers.add_parser("profiler-report", help="Print profiler precision/recall from result rows.")
    profiler_report_parser.add_argument("--results", required=True)

    args = parser.parse_args(argv)
    if args.command == "compile":
        if args.profiler == "heuristic":
            profile = profile_heuristic(args.query)
        else:
            from .llm_client import OpenAICompatibleClient
            from .llm_profiler import profile_variant

            client = OpenAICompatibleClient()
            profile = profile_variant(args.query, client, args.profiler)
        harness = compile_minimal_harness(profile, default_registry())
        print(json.dumps({"profile": profile.to_json(), "harness": harness.to_json()}, indent=2, sort_keys=True))
        return 0
    if args.command == "run-benchmark":
        if args.stream:
            count = run_benchmark_streaming(
                args.benchmark,
                args.system,
                args.profiler,
                args.out,
                limit=args.limit,
                start=args.start,
                resume=not args.no_resume,
                progress_every=args.progress_every,
            )
            print("wrote %d new rows to %s" % (count, args.out))
            return 0
        rows = run_benchmark(args.benchmark, args.system, args.profiler)
        write_jsonl(args.out, rows)
        print("wrote %d rows to %s" % (len(rows), args.out))
        return 0
    if args.command == "make-report":
        rows = load_results(args.results)
        markdown = render_markdown_report(rows)
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        print("wrote report to %s" % args.out)
        return 0
    if args.command == "profiler-report":
        rows = load_results(args.results)
        print(json.dumps(profiler_confusion(rows), indent=2, sort_keys=True))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
