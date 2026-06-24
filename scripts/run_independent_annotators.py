"""Run 3 independent multi-model annotators for the GapHarness IAA gate (M3).

Design for VALIDITY (see the plan's independence requirements):
  * Each annotator is a DIFFERENT model FAMILY.
  * Each annotator sees ONLY the neutral codebook (docs/annotation_codebook.md)
    plus the bare query. It never sees gold labels, the registry-guard code,
    GapHarness's tuned profiler prompt, or the other annotators' answers.
  * The annotator system prompt is the codebook verbatim plus a short, neutral
    "output JSON only" instruction. We do NOT inject any of the tuned profiler's
    heuristics.

CACHE: the FULL raw API response per (model, row) is written under
``outputs/iaa/raw/<dataset>/<model_slug>/<row_id>.json`` so the whole study
replays with NO API. Re-runs resume from cache (a present, non-empty,
parseable cache file is skipped unless --no-resume).

DATASETS:
  * ``gapbench``  -- a stratified, deterministic ~120-row subset of
    benchmarks/gapbench_1000_human_audited.jsonl, written to
    outputs/iaa/gapbench_subset.jsonl with the sampled task_ids.
  * ``disguised`` -- benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl.

This script writes ONLY to its owned paths (outputs/iaa/**).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from gapharness.llm_client import (
    ChatMessage,
    LLMClientError,
    OpenAICompatibleClient,
    parse_json_object,
)

# ---------------------------------------------------------------------------
# Annotator model families (recorded EXACT ids).
# gemini-2.5-pro consumes reasoning tokens, so it needs a larger max_tokens
# budget; gpt-5.5 and opus are fine at 600. temperature is 0 for all (the
# endpoint accepts temperature=0 for all three families in the smoke test).
# ---------------------------------------------------------------------------
ANNOTATORS: Tuple[Dict[str, object], ...] = (
    {"family": "openai", "model": "gpt-5.5", "max_tokens": 700, "temperature": 0.0},
    {"family": "anthropic", "model": "claude-opus-4-1-20250805", "max_tokens": 700, "temperature": 0.0},
    {"family": "google", "model": "gemini-2.5-pro", "max_tokens": 4096, "temperature": 0.0},
)

CODEBOOK_PATH = Path("docs/annotation_codebook.md")

ANNOTATOR_TASK_INSTRUCTION = """
You are an independent annotator applying the codebook above. You will be given
ONE user request. Apply the codebook and return your judgment.

Return ONE JSON object only, with exactly these keys and nothing else:
{
  "obligations": [ ... subset of Observation/Execution/State/Action/Control/Verification ... ],
  "capabilities": [ ... subset of the codebook capability vocabulary ... ],
  "status": "supported" | "unsupported" | "clarify"
}

Do not add explanations or any text outside the JSON object.
"""


def model_slug(model: str) -> str:
    return model.replace("/", "_").replace(":", "_")


def load_codebook() -> str:
    if not CODEBOOK_PATH.exists():
        raise SystemExit("Missing codebook at %s" % CODEBOOK_PATH)
    return CODEBOOK_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Stratified deterministic GapBench subset
# ---------------------------------------------------------------------------
def load_jsonl(path: Path) -> List[Mapping[str, object]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def stratified_gapbench_subset(
    source: Path,
    target_n: int = 120,
    seed: int = 1729,
) -> List[Mapping[str, object]]:
    """Deterministic stratified sample of ~target_n rows.

    Strata are (category, status, obligation-multiplicity) so the subset covers
    supported/unsupported/clarify AND single/multi-obligation. We allocate per
    stratum proportional to its size, guaranteeing >=1 from every non-empty
    stratum (so the 30 unsupported and 30 clarify rows are represented), then
    sample within each stratum with a fixed RNG seed.
    """
    rows = load_jsonl(source)

    def mult(r: Mapping[str, object]) -> str:
        n = len(r.get("gold_obligations", []) or [])
        return "0" if n == 0 else ("1" if n == 1 else "2plus")

    strata: Dict[Tuple[str, str, str], List[Mapping[str, object]]] = defaultdict(list)
    for r in rows:
        key = (str(r.get("category")), str(r.get("expected_status")), mult(r))
        strata[key].append(r)

    total = len(rows)
    rng = random.Random(seed)
    selected: List[Mapping[str, object]] = []
    seen_ids = set()

    # Deterministic stratum order.
    ordered_keys = sorted(strata.keys())
    # First pass: proportional allocation with a floor of 1 per non-empty stratum.
    alloc: Dict[Tuple[str, str, str], int] = {}
    for key in ordered_keys:
        bucket = strata[key]
        share = target_n * len(bucket) / total
        alloc[key] = max(1, int(round(share)))
        alloc[key] = min(alloc[key], len(bucket))

    # Adjust total to land near target_n: trim/grow from the largest strata.
    def current_total() -> int:
        return sum(alloc.values())

    # Trim overshoot (largest strata first, never below 1).
    while current_total() > target_n:
        candidates = [k for k in ordered_keys if alloc[k] > 1]
        if not candidates:
            break
        k = max(candidates, key=lambda x: (alloc[x], str(x)))
        alloc[k] -= 1
    # Grow undershoot (largest strata with headroom first).
    while current_total() < target_n:
        candidates = [k for k in ordered_keys if alloc[k] < len(strata[k])]
        if not candidates:
            break
        k = max(candidates, key=lambda x: (len(strata[x]) - alloc[x], str(x)))
        alloc[k] += 1

    for key in ordered_keys:
        bucket = sorted(strata[key], key=lambda r: str(r["task_id"]))
        pick = rng.sample(bucket, alloc[key]) if alloc[key] < len(bucket) else list(bucket)
        for r in pick:
            if r["task_id"] not in seen_ids:
                selected.append(r)
                seen_ids.add(r["task_id"])

    selected.sort(key=lambda r: str(r["task_id"]))
    return selected


def write_gapbench_subset(rows: Sequence[Mapping[str, object]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    ids_path = out_path.with_name("gapbench_subset_task_ids.json")
    ids_path.write_text(json.dumps([r["task_id"] for r in rows], indent=2))


# ---------------------------------------------------------------------------
# Dataset row adapters: (row_id, query, cluster)
# ---------------------------------------------------------------------------
def gapbench_items(rows: Sequence[Mapping[str, object]]):
    for r in rows:
        yield str(r["task_id"]), str(r["query"]), str(r.get("category", "unknown"))


def disguised_items(rows: Sequence[Mapping[str, object]]):
    for r in rows:
        yield str(r["id"]), str(r["query"]), str(r.get("template", "unknown"))


# ---------------------------------------------------------------------------
# Caching + running one annotator over one dataset
# ---------------------------------------------------------------------------
def cache_path(cache_dir: Path, dataset: str, model: str, row_id: str) -> Path:
    return cache_dir / dataset / model_slug(model) / ("%s.json" % row_id)


def is_cached(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        env = json.loads(path.read_text())
    except Exception:
        return False
    # A usable cache entry has a parseable model content payload.
    try:
        content = env["response"]["choices"][0]["message"]["content"]
        parse_json_object(content)
        return True
    except Exception:
        return False


def run_annotator(
    client: OpenAICompatibleClient,
    annotator: Mapping[str, object],
    dataset: str,
    items: Sequence[Tuple[str, str, str]],
    codebook: str,
    cache_dir: Path,
    resume: bool = True,
    sleep: float = 0.0,
    limit: Optional[int] = None,
) -> Dict[str, int]:
    model = str(annotator["model"])
    system_prompt = codebook + "\n\n" + ANNOTATOR_TASK_INSTRUCTION
    stats = {"cached": 0, "called": 0, "errors": 0, "parse_fail": 0}
    count = 0
    for row_id, query, cluster in items:
        if limit is not None and count >= limit:
            break
        count += 1
        path = cache_path(cache_dir, dataset, model, row_id)
        if resume and is_cached(path):
            stats["cached"] += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        user = "User request to annotate:\n\n" + query
        try:
            resp = client.chat_json(
                [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=user),
                ],
                temperature=float(annotator["temperature"]),
                max_tokens=int(annotator["max_tokens"]),
            )
        except LLMClientError as exc:
            stats["errors"] += 1
            sys.stderr.write("[%s/%s] ERROR %s: %s\n" % (dataset, model, row_id, str(exc)[:160]))
            if sleep:
                time.sleep(sleep)
            continue
        envelope = {
            "dataset": dataset,
            "model": model,
            "family": annotator["family"],
            "row_id": row_id,
            "cluster": cluster,
            "query": query,
            "request": {
                "temperature": annotator["temperature"],
                "max_tokens": annotator["max_tokens"],
            },
            "response": resp.raw,
        }
        path.write_text(json.dumps(envelope, indent=2))
        stats["called"] += 1
        # parse health check (does not affect caching)
        try:
            parse_json_object(resp.content)
        except Exception:
            stats["parse_fail"] += 1
        if sleep:
            time.sleep(sleep)
    return stats


def make_client(model: str, timeout_seconds: int = 60, max_retries: int = 2) -> OpenAICompatibleClient:
    # api_key/base_url come from env (GAPHARNESS_API_KEY / GAPHARNESS_BASE_URL).
    # A shorter timeout fails fast on a hung relay connection so one stuck row
    # cannot stall the whole batch; the runner catches the error, leaves that row
    # uncached, and continues. Re-running resumes and retries only the gaps.
    return OpenAICompatibleClient(model=model, timeout_seconds=timeout_seconds, max_retries=max_retries)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run multi-model independent annotators (IAA gate).")
    parser.add_argument("--gapbench-source", default="benchmarks/gapbench_1000_human_audited.jsonl")
    parser.add_argument("--disguised-source", default="benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl")
    parser.add_argument("--subset-n", type=int, default=120)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--cache-dir", default="outputs/iaa/raw")
    parser.add_argument("--subset-out", default="outputs/iaa/gapbench_subset.jsonl")
    parser.add_argument("--datasets", default="gapbench,disguised")
    parser.add_argument("--models", default=None, help="Comma-separated model ids to run (default: all 3 families).")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=60, help="Per-request socket timeout (s). Fail fast on hung relay calls.")
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--build-subset-only", action="store_true", help="Only build the stratified subset, no API calls.")
    args = parser.parse_args(argv)

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    datasets = [d.strip() for d in args.datasets.split(",") if d.strip()]

    # Build (or rebuild) the deterministic stratified GapBench subset.
    subset_rows: List[Mapping[str, object]] = []
    if "gapbench" in datasets:
        subset_rows = stratified_gapbench_subset(Path(args.gapbench_source), args.subset_n, args.seed)
        write_gapbench_subset(subset_rows, Path(args.subset_out))
        print("stratified GapBench subset: %d rows -> %s" % (len(subset_rows), args.subset_out))

    if args.build_subset_only:
        return 0

    disguised_rows: List[Mapping[str, object]] = []
    if "disguised" in datasets:
        disguised_rows = load_jsonl(Path(args.disguised_source))
        print("disguised-refusal set: %d rows" % len(disguised_rows))

    annotators = ANNOTATORS
    if args.models:
        wanted = {m.strip() for m in args.models.split(",")}
        annotators = tuple(a for a in ANNOTATORS if a["model"] in wanted)

    dataset_items = {}
    if "gapbench" in datasets:
        dataset_items["gapbench"] = list(gapbench_items(subset_rows))
    if "disguised" in datasets:
        dataset_items["disguised"] = list(disguised_items(disguised_rows))

    summary: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(dict)
    for annotator in annotators:
        model = str(annotator["model"])
        client = make_client(model, timeout_seconds=args.timeout, max_retries=args.retries)
        for dataset in datasets:
            items = dataset_items.get(dataset, [])
            stats = run_annotator(
                client,
                annotator,
                dataset,
                items,
                load_codebook(),
                cache_dir,
                resume=not args.no_resume,
                sleep=args.sleep,
                limit=args.limit,
            )
            summary[model][dataset] = stats
            print("[%s | %s] cached=%d called=%d errors=%d parse_fail=%d" % (
                model, dataset, stats["cached"], stats["called"], stats["errors"], stats["parse_fail"],
            ))

    # Record which exact model ids ran (no secrets).
    manifest = {
        "annotators": [{"family": a["family"], "model": a["model"], "max_tokens": a["max_tokens"], "temperature": a["temperature"]} for a in annotators],
        "datasets": datasets,
        "subset_n": len(subset_rows),
        "seed": args.seed,
        "summary": summary,
    }
    manifest_path = cache_dir.parent / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print("wrote run manifest to %s" % manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
