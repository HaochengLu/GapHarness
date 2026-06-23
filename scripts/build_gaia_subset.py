"""Build a GAIA obligation-transfer subset from metadata.

This script requires that the provided Hugging Face token has accepted access to
the gated `gaia-benchmark/GAIA` dataset. It intentionally downloads metadata
only; task attachments are not fetched in the MVP.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from gapharness.compiler import compile_minimal_harness
from gapharness.llm_profiler import canonicalize_profile
from gapharness.profiler import profile_heuristic
from gapharness.registry import default_registry
from gapharness.schema import ProfilerOutput, TaskExample, frozen


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="validation", choices=["validation", "test"])
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--out", default="benchmarks/gaia_obligation_subset.jsonl")
    args = parser.parse_args(argv)

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise SystemExit("Missing HF_TOKEN or HUGGINGFACE_TOKEN.")

    try:
        from huggingface_hub import HfApi
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Install datasets and huggingface_hub before running this script.") from exc

    try:
        token_info = HfApi().whoami(token=token)
        access_token = token_info.get("auth", {}).get("accessToken", {})
        if access_token.get("fineGrained", {}).get("canReadGatedRepos") is False:
            raise SystemExit(
                "HF token is valid but canReadGatedRepos=False. Enable read access to public gated repositories "
                "for this fine-grained token before loading GAIA."
            )
    except SystemExit:
        raise
    except Exception:
        pass

    try:
        ds = load_dataset("gaia-benchmark/GAIA", "2023_all", token=token)
    except Exception as exc:
        raise SystemExit(
            "Could not load GAIA via datasets.load_dataset('gaia-benchmark/GAIA', '2023_all'). "
            "Original error: %s" % str(exc)[:1000]
        ) from exc

    dataset = ds[args.split]
    rows = []
    registry = default_registry()
    for row in list(dataset)[: args.limit]:
        task_id = str(row.get("task_id") or row.get("id") or len(rows))
        query = str(row.get("Question") or row.get("question") or row.get("query") or "")
        level = str(row.get("Level") or row.get("level") or "")
        file_name = row.get("file_name") or row.get("file") or None
        profile = profile_heuristic(query)
        if file_name and str(file_name) != "nan":
            profile = canonicalize_profile(
                profile,
                query + " attached file workspace artifact",
            )
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
        rows.append(
            TaskExample(
                task_id="gaia-%s-%03d" % (args.split, len(rows) + 1),
                query=query,
                gold_obligations=profile.obligations,
                required_capabilities=profile.required_capabilities,
                oracle_minimal_harness=oracle,
                success_checker="gaia_obligation_transfer_only",
                expected_failure_if_direct="missing_external_obligations",
                risk_level=profile.risk_level,
                category="gaia_transfer_level_%s" % level,
                expected_status="supported",
                tags=("gaia", args.split),
                notes="Auto-profiled GAIA transfer seed; requires human audit.",
                gold_source="gaia_metadata_auto_profile_needs_human_review",
            )
        )

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for task in rows:
            handle.write(json.dumps(task.to_json(), sort_keys=True) + "\n")
    print("wrote %d GAIA transfer rows to %s" % (len(rows), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
