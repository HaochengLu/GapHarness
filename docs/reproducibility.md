# Reproducibility and Model Pin

This document pins the LLM configuration used for the GapHarness profiler
experiments so that the numbers in the manuscript and tables are traceable to a
specific provider relay, model, and environment-variable contract. Environment
setup, unit tests, and artifact regeneration are covered by the top-level
`README.md` and `scripts/check_repro.sh`.

## Environment and benchmark inputs

The core code path is standard-library only and runs on **Python 3.9** (the pinned
interpreter; see `.python-version` and the `requires-python = ">=3.9"` floor in
`pyproject.toml`). The naturalized-transfer profiler sweep reads the committed
input `benchmarks/gapbench_natural/v1.0/gapbench_natural_200_human_audited.jsonl`
(the earlier `*_for_review` filename was a naming convention and is no longer a
live path).

## Provider Relay and Model Pin

All LLM profiler experiments use an OpenAI-compatible chat endpoint accessed
through a provider relay, not a first-party OpenAI deployment:

- **Provider relay base URL:** `https://api.xgapi.top`
- **Pinned profiler model (default cheap profiler):** `gpt-5.4-mini`
- **Strong fallback model (failed/guarded reruns only):** `gpt-5.5`
- **Decoding:** `temperature = 0.0` (deterministic-as-possible greedy decoding)

The cheap profiler `gpt-5.4-mini` is the pinned model for every primary profiler
sweep (Phase 2B/2C). The `gpt-5.5` model is used only as a strong fallback on the
small set of rows that fail the cheap-profiler cascade or the exact-arithmetic
guard. The independent multi-model IAA study additionally uses
`claude-opus-4-1-20250805` and `gemini-2.5-pro` as separate annotator families;
those are documented in `docs/annotation_codebook.md` and are not the profiler
pin.

Note on the client default: the bare string `gpt-5.5` that appears as the
hard-coded fallback in `gapharness/llm_client.py` (`OpenAICompatibleClient`) is a
last-resort default only. It is **not** the pinned profiler model. The pinned
profiler model is `gpt-5.4-mini`, selected explicitly via the `GAPHARNESS_MODEL`
environment variable (or the `model=` constructor argument) for every reported
profiler run. Read any reference to a `gpt-5.5` "default" as the client-level
fallback, not the experiment configuration.

## Environment Variables

Credentials and endpoint configuration are read from environment variables only.
No API key is ever written to repository files, paper artifacts, or shared command
history.

| Variable | Purpose | Value used for experiments |
|---|---|---|
| `GAPHARNESS_API_KEY` | Bearer token for the relay | (secret — set in the shell only; never committed) |
| `GAPHARNESS_BASE_URL` | OpenAI-compatible base URL | `https://api.xgapi.top` |
| `GAPHARNESS_MODEL` | Pinned profiler model | `gpt-5.4-mini` |

The client also honors the legacy `OPENAI_API_KEY` / `OPENAI_BASE_URL` fallbacks,
but the pinned configuration above uses the `GAPHARNESS_*` names.

Example shell setup (the key is supplied interactively and never stored in a
tracked file):

```bash
export GAPHARNESS_API_KEY=...            # supplied at runtime only; never committed
export GAPHARNESS_BASE_URL=https://api.xgapi.top
export GAPHARNESS_MODEL=gpt-5.4-mini     # pinned profiler model
```

## Raw-Response Caching (No-Network Replay)

`gapharness/llm_client.py` supports an optional raw-response cache so that LLM
calls can be replayed deterministically with no network access. The cache is
additive and disabled by default; enabling it does not change the public
`ChatResponse` or `chat_json` signatures.

- Enable it by passing `cache_dir=...` to `OpenAICompatibleClient(...)`, or by
  setting the `GAPHARNESS_CACHE_DIR` environment variable.
- When enabled, the full raw JSON response is persisted under `cache_dir`, keyed by
  a SHA-256 hash of `(model, messages, temperature, max_tokens, response_format)`.
- On a cache hit, the response is returned from disk and no network request is made,
  so a populated cache reproduces the exact recorded responses without an API key.

```bash
export GAPHARNESS_CACHE_DIR=outputs/llm_cache   # persists/replays raw responses
```

This mechanism is intended for byte-stable replay of the profiler sweeps. The
frozen LLM outputs under `outputs/final/phase2b/` and `outputs/final/phase2c/`
remain the canonical record; the cache is a convenience for re-deriving them
without re-billing the relay.
