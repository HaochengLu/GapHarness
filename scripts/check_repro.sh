#!/usr/bin/env bash
#
# check_repro.sh - static reproducibility self-check.
#
# Verifies, WITHOUT running any experiment or touching committed artifacts:
#   1. Every benchmark input path referenced by run_phase2_gold_experiments.sh
#      actually exists on disk.
#   2. freeze_phase2_datasets.py writes JSON with ensure_ascii=False so a freeze
#      re-run preserves committed UTF-8 bytes (e.g. U+2019) and checksums.
#   3. pyproject.toml declares a [build-system] table, the package name
#      "gapharness", and the gapharness -> gapharness.cli:main console script.
#   4. The Python version is consistent across pyproject.toml (>=3.9),
#      .python-version (3.9) and the running interpreter.
#
# Exit code 0 means all checks passed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

fail=0
note() { printf 'CHECK %-46s %s\n' "$1" "$2"; }
ok()   { note "$1" "OK"; }
bad()  { note "$1" "FAIL: $2"; fail=1; }

GOLD_SCRIPT="scripts/run_phase2_gold_experiments.sh"

# 1. Every --benchmark / --results-source input path in the gold script exists.
#    (We check the explicit benchmark JSONL inputs the script reads.)
missing=0
while IFS= read -r path; do
  [ -z "$path" ] && continue
  if [ -e "$path" ]; then
    ok "gold input exists: $path"
  else
    bad "gold input exists: $path" "path not found"
    missing=1
  fi
done < <(grep -oE 'benchmarks/[^ ]+\.jsonl' "$GOLD_SCRIPT" | sort -u)
[ "$missing" -eq 0 ] && ok "all gold-script benchmark inputs present"

# Guard against the historical broken reference.
if grep -q 'gapbench_natural_200_for_review.jsonl' "$GOLD_SCRIPT"; then
  bad "no stale gapbench_natural_200_for_review.jsonl ref" "stale path still referenced"
else
  ok "no stale gapbench_natural_200_for_review.jsonl ref"
fi

# 2. freeze writers use ensure_ascii=False.
FREEZE="scripts/freeze_phase2_datasets.py"
ascii_writers="$(grep -c 'json.dumps(' "$FREEZE" || true)"
ascii_safe="$(grep -c 'ensure_ascii=False' "$FREEZE" || true)"
if [ "$ascii_writers" -ge 1 ] && [ "$ascii_safe" -ge "$ascii_writers" ]; then
  ok "freeze json.dumps uses ensure_ascii=False ($ascii_safe/$ascii_writers)"
else
  bad "freeze json.dumps uses ensure_ascii=False" "$ascii_safe/$ascii_writers calls guarded"
fi

# 3. pyproject build-system + name + entry point.
grep -q '^\[build-system\]' pyproject.toml \
  && ok "pyproject has [build-system]" \
  || bad "pyproject has [build-system]" "missing"
grep -qE '^name = "gapharness"' pyproject.toml \
  && ok 'pyproject name = "gapharness"' \
  || bad 'pyproject name = "gapharness"' "missing/wrong"
grep -qE '^gapharness = "gapharness.cli:main"' pyproject.toml \
  && ok "console script gapharness -> gapharness.cli:main" \
  || bad "console script gapharness -> gapharness.cli:main" "missing/wrong"

# 4. Python version consistency.
grep -qE 'requires-python = ">=3.9"' pyproject.toml \
  && ok 'pyproject requires-python = ">=3.9"' \
  || bad 'pyproject requires-python = ">=3.9"' "not >=3.9"
if [ -f .python-version ] && grep -qE '^3\.9' .python-version; then
  ok ".python-version pins 3.9"
else
  bad ".python-version pins 3.9" "missing or not 3.9"
fi
running_py="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case "$running_py" in
  3.9|3.1[0-9]) ok "running python3 ($running_py) satisfies >=3.9" ;;
  *)            bad "running python3 ($running_py) satisfies >=3.9" "too old" ;;
esac

if [ "$fail" -eq 0 ]; then
  echo "ALL REPRO CHECKS PASSED"
else
  echo "REPRO CHECKS FAILED"
fi
exit "$fail"
