"""Run SWE-HarnessExec executable trace validation.

This experiment validates that a compiled harness can drive a concrete
sandboxed software-maintenance loop: inspect files, run failing tests, apply a
provided patch, rerun tests, and verify logs/diff. It is not SWE-bench pass@1
and does not claim model patch generation.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from gapharness.baselines import compile_for_system
from gapharness.evaluation import row_metrics, write_jsonl
from gapharness.executor import execute_task
from gapharness.registry import default_registry
from gapharness.schema import TaskExample, frozen


SYSTEMS = ("direct", "tool_router", "difficulty_router", "always_full", "gapharness", "oracle_minimal")
REQUIRED_MODULES = (
    "contract_verifier",
    "execution_log_checker",
    "file_state_reader",
    "permission_gate",
    "python_executor",
    "sandbox_file_editor",
    "state_store",
)
REQUIRED_CAPABILITIES = (
    "contract_check",
    "diff",
    "durable_state",
    "execution",
    "execution_log",
    "permission",
    "sandbox_action",
    "workspace_inspection",
)
REQUIRED_OBLIGATIONS = ("Action", "Control", "Execution", "Observation", "State", "Verification")


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    title: str
    buggy_source: str
    fixed_source: str
    test_source: str
    issue: str


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", default="benchmarks/harness_exec/v1.0")
    parser.add_argument("--out-dir", default="outputs/final/harness_exec20")
    parser.add_argument("--audit-date", default=date.today().isoformat())
    parser.add_argument("--systems", default=",".join(SYSTEMS))
    parser.add_argument("--suite-size", type=int, default=20)
    parser.add_argument("--suite-label", default="")
    args = parser.parse_args(argv)

    benchmark_dir = Path(args.benchmark_dir)
    out_dir = Path(args.out_dir)
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    systems = tuple(item.strip() for item in args.systems.split(",") if item.strip())
    cases = build_cases(args.suite_size)
    suite_label = args.suite_label or suite_label_from_size(len(cases))
    tasks = [case_to_task(case, args.audit_date, suite_label) for case in cases]
    write_benchmark_artifacts(benchmark_dir, tasks, args.audit_date, suite_label)

    registry = default_registry()
    rows = []
    for case, task in zip(cases, tasks):
        for system in systems:
            harness, profiler = compile_for_system(task, system, "gold", registry)
            coverage_result = execute_task(task, system, profiler, harness, registry)
            exec_row = run_case_trace(case, task, system, profiler, harness.to_json(), out_dir)
            row = {
                "case_id": case.case_id,
                "task_id": task.task_id,
                "system": system,
                "profiler": profiler,
                "task": task.to_json(),
                "harness": harness.to_json(),
                "coverage_metrics": row_metrics(task, coverage_result),
                "coverage_verifier_passed": coverage_result.verifier_passed,
                "coverage_verifier_failures": list(coverage_result.verifier_failures),
                "exec_metrics": exec_row["exec_metrics"],
                "trace": exec_row["trace"],
                "sandbox_path": exec_row["sandbox_path"],
            }
            rows.append(row)

    write_jsonl(str(out_dir / "traces.jsonl"), rows)
    (out_dir / "summary.md").write_text(render_report(rows, suite_label), encoding="utf-8")
    (out_dir / "manifest.json").write_text(render_manifest(tasks, rows, args.audit_date, suite_label), encoding="utf-8")
    print("wrote %s traces to %s" % (suite_label, out_dir))
    return 0


def build_cases(suite_size: int = 20) -> list[CaseSpec]:
    all_cases = [
        case(
            "case-001",
            "addition regression",
            "def add(a, b):\n    return a - b\n",
            "def add(a, b):\n    return a + b\n",
            "from solution import add\n\n\ndef test_add_positive_numbers():\n    assert add(2, 5) == 7\n",
            "The add helper subtracts instead of adding.",
        ),
        case(
            "case-002",
            "slug normalization",
            "def slugify(text):\n    return text.strip().replace(' ', '-')\n",
            "def slugify(text):\n    return '-'.join(text.strip().lower().split())\n",
            "from solution import slugify\n\n\ndef test_slugify_lowercases_and_collapses_spaces():\n    assert slugify('  Hello   World  ') == 'hello-world'\n",
            "Slug generation must lowercase and collapse whitespace.",
        ),
        case(
            "case-003",
            "upper clamp",
            "def clamp(value, low, high):\n    if value < low:\n        return low\n    return value\n",
            "def clamp(value, low, high):\n    if value < low:\n        return low\n    if value > high:\n        return high\n    return value\n",
            "from solution import clamp\n\n\ndef test_clamp_upper_bound():\n    assert clamp(12, 0, 10) == 10\n",
            "Clamp handles the lower bound but forgets the upper bound.",
        ),
        case(
            "case-004",
            "boolean parsing",
            "def parse_bool(value):\n    return value == 'true'\n",
            "def parse_bool(value):\n    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}\n",
            "from solution import parse_bool\n\n\ndef test_parse_bool_accepts_yes():\n    assert parse_bool(' YES ')\n",
            "Boolean parsing should accept common truthy strings.",
        ),
        case(
            "case-005",
            "median odd length",
            "def median(values):\n    values = sorted(values)\n    return sum(values) / len(values)\n",
            "def median(values):\n    values = sorted(values)\n    mid = len(values) // 2\n    if len(values) % 2:\n        return values[mid]\n    return (values[mid - 1] + values[mid]) / 2\n",
            "from solution import median\n\n\ndef test_median_odd_length():\n    assert median([1, 2, 9]) == 2\n",
            "Median incorrectly returns the mean.",
        ),
        case(
            "case-006",
            "stable unique",
            "def unique_preserve(values):\n    return sorted(set(values))\n",
            "def unique_preserve(values):\n    seen = set()\n    out = []\n    for value in values:\n        if value not in seen:\n            seen.add(value)\n            out.append(value)\n    return out\n",
            "from solution import unique_preserve\n\n\ndef test_unique_preserves_order():\n    assert unique_preserve(['b', 'a', 'b']) == ['b', 'a']\n",
            "Unique values must preserve first-seen order.",
        ),
        case(
            "case-007",
            "count merging",
            "def merge_counts(left, right):\n    out = dict(left)\n    out.update(right)\n    return out\n",
            "def merge_counts(left, right):\n    out = dict(left)\n    for key, value in right.items():\n        out[key] = out.get(key, 0) + value\n    return out\n",
            "from solution import merge_counts\n\n\ndef test_merge_counts_adds_existing_key():\n    assert merge_counts({'a': 2}, {'a': 3, 'b': 1}) == {'a': 5, 'b': 1}\n",
            "Merging count dictionaries should add overlapping counts.",
        ),
        case(
            "case-008",
            "safe divide",
            "def safe_divide(a, b, default=0):\n    return a / b\n",
            "def safe_divide(a, b, default=0):\n    if b == 0:\n        return default\n    return a / b\n",
            "from solution import safe_divide\n\n\ndef test_safe_divide_zero_uses_default():\n    assert safe_divide(5, 0, default=None) is None\n",
            "Division by zero should return the provided default.",
        ),
        case(
            "case-009",
            "flatten one level",
            "def flatten_once(values):\n    return values\n",
            "def flatten_once(values):\n    out = []\n    for item in values:\n        if isinstance(item, list):\n            out.extend(item)\n        else:\n            out.append(item)\n    return out\n",
            "from solution import flatten_once\n\n\ndef test_flatten_once():\n    assert flatten_once([1, [2, 3], 4]) == [1, 2, 3, 4]\n",
            "The helper should flatten one nested list level.",
        ),
        case(
            "case-010",
            "moving average",
            "def moving_average(values, window):\n    return [sum(values[:window]) / window]\n",
            "def moving_average(values, window):\n    return [sum(values[i:i + window]) / window for i in range(len(values) - window + 1)]\n",
            "from solution import moving_average\n\n\ndef test_moving_average_all_windows():\n    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]\n",
            "Moving average should emit every full window.",
        ),
        case(
            "case-011",
            "CSV trimming",
            "def parse_csv_row(row):\n    return row.split(',')\n",
            "def parse_csv_row(row):\n    return [part.strip() for part in row.split(',')]\n",
            "from solution import parse_csv_row\n\n\ndef test_parse_csv_row_trims_cells():\n    assert parse_csv_row('a, b ,c') == ['a', 'b', 'c']\n",
            "CSV row parsing should trim whitespace around cells.",
        ),
        case(
            "case-012",
            "email validation",
            "def is_valid_email(value):\n    return '.' in value\n",
            "def is_valid_email(value):\n    return '@' in value and '.' in value.split('@')[-1]\n",
            "from solution import is_valid_email\n\n\ndef test_email_requires_at_sign():\n    assert not is_valid_email('example.com')\n",
            "Email validation must require an at sign.",
        ),
        case(
            "case-013",
            "chunking",
            "def chunks(values, size):\n    return [values[i:i + size] for i in range(0, len(values) - size, size)]\n",
            "def chunks(values, size):\n    return [values[i:i + size] for i in range(0, len(values), size)]\n",
            "from solution import chunks\n\n\ndef test_chunks_includes_tail():\n    assert chunks([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]\n",
            "Chunking drops the final partial chunk.",
        ),
        case(
            "case-014",
            "token redaction",
            "def redact_token(value):\n    return value[:4] + '...'\n",
            "def redact_token(value):\n    return value[:4] + '...' + value[-4:]\n",
            "from solution import redact_token\n\n\ndef test_redact_token_keeps_suffix():\n    assert redact_token('token_example_abcdef123456') == 'toke...3456'\n",
            "Token redaction should keep a short prefix and suffix.",
        ),
        case(
            "case-015",
            "config defaults",
            "def apply_defaults(config, defaults):\n    return dict(config)\n",
            "def apply_defaults(config, defaults):\n    out = dict(defaults)\n    out.update(config)\n    return out\n",
            "from solution import apply_defaults\n\n\ndef test_apply_defaults_fills_missing_key():\n    assert apply_defaults({'port': 8080}, {'host': '127.0.0.1', 'port': 80}) == {'host': '127.0.0.1', 'port': 8080}\n",
            "Config defaults should fill missing keys without overriding user values.",
        ),
        case(
            "case-016",
            "record sorting",
            "def sort_records(records):\n    return sorted(records, key=lambda row: row['name'])\n",
            "def sort_records(records):\n    return sorted(records, key=lambda row: (row['score'], row['name']))\n",
            "from solution import sort_records\n\n\ndef test_sort_records_by_score_then_name():\n    rows = [{'name': 'b', 'score': 1}, {'name': 'a', 'score': 1}, {'name': 'c', 'score': 0}]\n    assert sort_records(rows) == [{'name': 'c', 'score': 0}, {'name': 'a', 'score': 1}, {'name': 'b', 'score': 1}]\n",
            "Records must sort by score, then name.",
        ),
        case(
            "case-017",
            "fibonacci base case",
            "def fib(n):\n    if n <= 1:\n        return 1\n    return fib(n - 1) + fib(n - 2)\n",
            "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n - 1) + fib(n - 2)\n",
            "from solution import fib\n\n\ndef test_fib_base_cases():\n    assert fib(0) == 0\n    assert fib(6) == 8\n",
            "Fibonacci uses the wrong zero base case.",
        ),
        case(
            "case-018",
            "path normalization",
            "def normalize_path(value):\n    return value.replace('//', '/')\n",
            "def normalize_path(value):\n    parts = [part for part in value.split('/') if part]\n    return '/' + '/'.join(parts)\n",
            "from solution import normalize_path\n\n\ndef test_normalize_path_collapses_repeated_separators():\n    assert normalize_path('//tmp///repo/') == '/tmp/repo'\n",
            "Path normalization should collapse repeated separators and trim trailing slash.",
        ),
        case(
            "case-019",
            "palindrome normalization",
            "def is_palindrome(value):\n    return value == value[::-1]\n",
            "def is_palindrome(value):\n    cleaned = ''.join(ch.lower() for ch in value if ch.isalnum())\n    return cleaned == cleaned[::-1]\n",
            "from solution import is_palindrome\n\n\ndef test_palindrome_ignores_case_and_spaces():\n    assert is_palindrome('Never odd or even')\n",
            "Palindrome checks should ignore case and spaces.",
        ),
        case(
            "case-020",
            "dedupe records by id",
            "def dedupe_by_id(records):\n    return records\n",
            "def dedupe_by_id(records):\n    seen = set()\n    out = []\n    for row in records:\n        if row['id'] not in seen:\n            seen.add(row['id'])\n            out.append(row)\n    return out\n",
            "from solution import dedupe_by_id\n\n\ndef test_dedupe_by_id_keeps_first_record():\n    rows = [{'id': 1, 'v': 'a'}, {'id': 1, 'v': 'b'}, {'id': 2, 'v': 'c'}]\n    assert dedupe_by_id(rows) == [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'c'}]\n",
            "Duplicate records should be removed by id while keeping the first row.",
        ),
        case(
            "case-021",
            "integer parsing default",
            "def parse_int(value, default=0):\n    return int(value)\n",
            "def parse_int(value, default=0):\n    text = str(value).strip()\n    if text == '':\n        return default\n    return int(text)\n",
            "from solution import parse_int\n\n\ndef test_parse_int_uses_default_for_blank():\n    assert parse_int('  ', default=7) == 7\n    assert parse_int('42') == 42\n",
            "Integer parsing should return the provided default for blank input.",
        ),
        case(
            "case-022",
            "phone normalization",
            "def normalize_phone(value):\n    return value.replace(' ', '')\n",
            "def normalize_phone(value):\n    return ''.join(ch for ch in value if ch.isdigit())\n",
            "from solution import normalize_phone\n\n\ndef test_normalize_phone_keeps_digits_only():\n    assert normalize_phone('(555) 123-0000') == '5551230000'\n",
            "Phone normalization should strip punctuation and keep digits only.",
        ),
        case(
            "case-023",
            "inventory reservation",
            "def reserve(stock, sku, qty):\n    out = dict(stock)\n    out[sku] -= 1\n    return out\n",
            "def reserve(stock, sku, qty):\n    out = dict(stock)\n    out[sku] = out.get(sku, 0) - qty\n    return out\n",
            "from solution import reserve\n\n\ndef test_reserve_subtracts_requested_quantity():\n    assert reserve({'book': 10}, 'book', 3) == {'book': 7}\n",
            "Inventory reservation should subtract the requested quantity.",
        ),
        case(
            "case-024",
            "merge sorted values",
            "def merge_sorted(left, right):\n    return left + right\n",
            "def merge_sorted(left, right):\n    return sorted(left + right)\n",
            "from solution import merge_sorted\n\n\ndef test_merge_sorted_keeps_order():\n    assert merge_sorted([1, 4], [2, 3]) == [1, 2, 3, 4]\n",
            "Merging two sorted lists should return a sorted list.",
        ),
        case(
            "case-025",
            "ISO date parsing",
            "def parse_iso_date(value):\n    month, day, year = value.split('/')\n    return {'year': int(year), 'month': int(month), 'day': int(day)}\n",
            "def parse_iso_date(value):\n    year, month, day = value.split('-')\n    return {'year': int(year), 'month': int(month), 'day': int(day)}\n",
            "from solution import parse_iso_date\n\n\ndef test_parse_iso_date():\n    assert parse_iso_date('2026-06-23') == {'year': 2026, 'month': 6, 'day': 23}\n",
            "Date parsing should accept YYYY-MM-DD ISO dates.",
        ),
        case(
            "case-026",
            "environment boolean false",
            "def env_flag(value):\n    return bool(value)\n",
            "def env_flag(value):\n    return str(value).strip().lower() not in {'', '0', 'false', 'no', 'off'}\n",
            "from solution import env_flag\n\n\ndef test_env_flag_false_string():\n    assert env_flag('false') is False\n    assert env_flag('yes') is True\n",
            "Environment flags should treat common false strings as false.",
        ),
        case(
            "case-027",
            "byte size conversion",
            "def bytes_to_kib(value):\n    return value / 1000\n",
            "def bytes_to_kib(value):\n    return value / 1024\n",
            "from solution import bytes_to_kib\n\n\ndef test_bytes_to_kib_uses_binary_units():\n    assert bytes_to_kib(2048) == 2\n",
            "KiB conversion should use 1024-byte units.",
        ),
        case(
            "case-028",
            "email masking",
            "def mask_email(value):\n    name, domain = value.split('@', 1)\n    return '***@' + domain\n",
            "def mask_email(value):\n    name, domain = value.split('@', 1)\n    return name[:1] + '***@' + domain\n",
            "from solution import mask_email\n\n\ndef test_mask_email_keeps_first_character():\n    assert mask_email('alice@example.com') == 'a***@example.com'\n",
            "Email masking should preserve the first local-part character.",
        ),
        case(
            "case-029",
            "top-k ranking",
            "def top_k(values, k):\n    return sorted(values)[:k]\n",
            "def top_k(values, k):\n    return sorted(values, reverse=True)[:k]\n",
            "from solution import top_k\n\n\ndef test_top_k_returns_largest_values():\n    assert top_k([4, 1, 9, 2], 2) == [9, 4]\n",
            "Top-k ranking should return the largest values first.",
        ),
        case(
            "case-030",
            "z-score zero variance",
            "def zscores(values):\n    mean = sum(values) / len(values)\n    variance = sum((value - mean) ** 2 for value in values) / len(values)\n    stdev = variance ** 0.5\n    return [(value - mean) / stdev for value in values]\n",
            "def zscores(values):\n    mean = sum(values) / len(values)\n    variance = sum((value - mean) ** 2 for value in values) / len(values)\n    stdev = variance ** 0.5\n    if stdev == 0:\n        return [0.0 for _ in values]\n    return [(value - mean) / stdev for value in values]\n",
            "from solution import zscores\n\n\ndef test_zscores_zero_variance():\n    assert zscores([5, 5, 5]) == [0.0, 0.0, 0.0]\n",
            "Z-score normalization should handle zero variance.",
        ),
        case(
            "case-031",
            "nested dictionary lookup",
            "def nested_get(data, keys, default=None):\n    return data[keys[0]]\n",
            "def nested_get(data, keys, default=None):\n    current = data\n    for key in keys:\n        if not isinstance(current, dict) or key not in current:\n            return default\n        current = current[key]\n    return current\n",
            "from solution import nested_get\n\n\ndef test_nested_get_walks_all_keys():\n    assert nested_get({'a': {'b': 3}}, ['a', 'b']) == 3\n    assert nested_get({'a': {}}, ['a', 'b'], default='x') == 'x'\n",
            "Nested lookup should walk all keys and use the default when missing.",
        ),
        case(
            "case-032",
            "percent change zero baseline",
            "def percent_change(old, new):\n    return (new - old) / old\n",
            "def percent_change(old, new):\n    if old == 0:\n        return None\n    return (new - old) / old\n",
            "from solution import percent_change\n\n\ndef test_percent_change_zero_baseline():\n    assert percent_change(0, 5) is None\n",
            "Percent change should not divide by a zero baseline.",
        ),
        case(
            "case-033",
            "port validation",
            "def valid_port(port):\n    return 0 <= port <= 65535\n",
            "def valid_port(port):\n    return 1 <= port <= 65535\n",
            "from solution import valid_port\n\n\ndef test_valid_port_rejects_zero():\n    assert not valid_port(0)\n    assert valid_port(443)\n",
            "Port validation should reject zero and accept valid TCP/UDP ports.",
        ),
        case(
            "case-034",
            "group records by key",
            "def group_by(rows, key):\n    out = {}\n    for row in rows:\n        out[row[key]] = row\n    return out\n",
            "def group_by(rows, key):\n    out = {}\n    for row in rows:\n        out.setdefault(row[key], []).append(row)\n    return out\n",
            "from solution import group_by\n\n\ndef test_group_by_keeps_all_rows():\n    rows = [{'team': 'a', 'id': 1}, {'team': 'a', 'id': 2}]\n    assert group_by(rows, 'team') == {'a': rows}\n",
            "Grouping should keep every row for each group key.",
        ),
        case(
            "case-035",
            "interval overlap",
            "def overlaps(left, right):\n    return left[1] < right[0] or right[1] < left[0]\n",
            "def overlaps(left, right):\n    return max(left[0], right[0]) <= min(left[1], right[1])\n",
            "from solution import overlaps\n\n\ndef test_overlaps_detects_intersection():\n    assert overlaps((1, 5), (5, 9))\n    assert not overlaps((1, 2), (3, 4))\n",
            "Interval overlap should detect inclusive boundary intersection.",
        ),
        case(
            "case-036",
            "word count punctuation",
            "def word_counts(text):\n    out = {}\n    for word in text.lower().split():\n        out[word] = out.get(word, 0) + 1\n    return out\n",
            "def word_counts(text):\n    cleaned = ''.join(ch.lower() if ch.isalnum() else ' ' for ch in text)\n    out = {}\n    for word in cleaned.split():\n        out[word] = out.get(word, 0) + 1\n    return out\n",
            "from solution import word_counts\n\n\ndef test_word_counts_strips_punctuation():\n    assert word_counts('Hi, hi!') == {'hi': 2}\n",
            "Word counts should normalize punctuation before counting.",
        ),
        case(
            "case-037",
            "key-value parsing",
            "def parse_key_values(text):\n    return dict(line.split('=') for line in text.splitlines())\n",
            "def parse_key_values(text):\n    out = {}\n    for line in text.splitlines():\n        if not line.strip():\n            continue\n        key, value = line.split('=', 1)\n        out[key.strip()] = value.strip()\n    return out\n",
            "from solution import parse_key_values\n\n\ndef test_parse_key_values_trims_and_skips_blank_lines():\n    assert parse_key_values('host = localhost\\n\\nport= 8080') == {'host': 'localhost', 'port': '8080'}\n",
            "Key-value parsing should trim whitespace and skip blank lines.",
        ),
        case(
            "case-038",
            "duration parsing",
            "def parse_duration(value):\n    return int(value[:-1])\n",
            "def parse_duration(value):\n    amount = int(value[:-1])\n    unit = value[-1]\n    if unit == 'h':\n        return amount * 3600\n    if unit == 'm':\n        return amount * 60\n    return amount\n",
            "from solution import parse_duration\n\n\ndef test_parse_duration_minutes():\n    assert parse_duration('2m') == 120\n",
            "Duration parsing should convert minute and hour suffixes to seconds.",
        ),
        case(
            "case-039",
            "URL joining",
            "def join_url(base, path):\n    return base + '/' + path\n",
            "def join_url(base, path):\n    return base.rstrip('/') + '/' + path.lstrip('/')\n",
            "from solution import join_url\n\n\ndef test_join_url_avoids_double_slash():\n    assert join_url('https://example.com/', '/docs') == 'https://example.com/docs'\n",
            "URL joining should avoid duplicate slashes at the boundary.",
        ),
        case(
            "case-040",
            "matrix transpose",
            "def transpose(matrix):\n    return matrix\n",
            "def transpose(matrix):\n    return [list(row) for row in zip(*matrix)]\n",
            "from solution import transpose\n\n\ndef test_transpose_matrix():\n    assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]\n",
            "Matrix transpose should swap rows and columns.",
        ),
        case(
            "case-041",
            "basename without extension",
            "def stem(path):\n    return path.split('.')[0]\n",
            "def stem(path):\n    name = path.rstrip('/').split('/')[-1]\n    return name.rsplit('.', 1)[0]\n",
            "from solution import stem\n\n\ndef test_stem_handles_directories_and_multiple_dots():\n    assert stem('/tmp/archive.tar.gz') == 'archive.tar'\n",
            "Path stem extraction should ignore directories and split only the final extension.",
        ),
        case(
            "case-042",
            "moving window sum",
            "def window_sum(values, window):\n    return [sum(values[:window])]\n",
            "def window_sum(values, window):\n    return [sum(values[i:i + window]) for i in range(len(values) - window + 1)]\n",
            "from solution import window_sum\n\n\ndef test_window_sum_all_windows():\n    assert window_sum([1, 2, 3, 4], 3) == [6, 9]\n",
            "Windowed sum should emit every full window.",
        ),
        case(
            "case-043",
            "average empty default",
            "def average(values, default=0):\n    return sum(values) / len(values)\n",
            "def average(values, default=0):\n    if not values:\n        return default\n    return sum(values) / len(values)\n",
            "from solution import average\n\n\ndef test_average_empty_uses_default():\n    assert average([], default=None) is None\n",
            "Average should return the provided default for empty input.",
        ),
        case(
            "case-044",
            "tag parsing",
            "def parse_tags(value):\n    return value.split(',')\n",
            "def parse_tags(value):\n    return [tag.strip().lower() for tag in value.split(',') if tag.strip()]\n",
            "from solution import parse_tags\n\n\ndef test_parse_tags_normalizes_and_drops_empty():\n    assert parse_tags(' AI, Systems, ,Paper ') == ['ai', 'systems', 'paper']\n",
            "Tag parsing should trim, lowercase, and drop empty entries.",
        ),
        case(
            "case-045",
            "anagram normalization",
            "def is_anagram(left, right):\n    return sorted(left) == sorted(right)\n",
            "def is_anagram(left, right):\n    clean_left = sorted(ch.lower() for ch in left if ch.isalnum())\n    clean_right = sorted(ch.lower() for ch in right if ch.isalnum())\n    return clean_left == clean_right\n",
            "from solution import is_anagram\n\n\ndef test_is_anagram_ignores_case_and_spaces():\n    assert is_anagram('Dormitory', 'dirty room')\n",
            "Anagram checks should ignore case and spaces.",
        ),
        case(
            "case-046",
            "one-indexed pagination",
            "def page(items, page_number, size):\n    start = page_number * size\n    return items[start:start + size]\n",
            "def page(items, page_number, size):\n    start = (page_number - 1) * size\n    return items[start:start + size]\n",
            "from solution import page\n\n\ndef test_page_is_one_indexed():\n    assert page(['a', 'b', 'c', 'd'], 2, 2) == ['c', 'd']\n",
            "Pagination should treat page numbers as one-indexed.",
        ),
        case(
            "case-047",
            "TTL boundary",
            "def expired(created_at, now, ttl):\n    return now - created_at > ttl\n",
            "def expired(created_at, now, ttl):\n    return now - created_at >= ttl\n",
            "from solution import expired\n\n\ndef test_expired_at_ttl_boundary():\n    assert expired(5, 10, 5)\n",
            "Expiration should trigger exactly at the TTL boundary.",
        ),
        case(
            "case-048",
            "currency formatting",
            "def format_currency(amount):\n    return '$' + str(amount)\n",
            "def format_currency(amount):\n    return '$%.2f' % amount\n",
            "from solution import format_currency\n\n\ndef test_format_currency_two_decimals():\n    assert format_currency(3) == '$3.00'\n",
            "Currency formatting should always use two decimal places.",
        ),
        case(
            "case-049",
            "prefix idempotence",
            "def ensure_prefix(value, prefix):\n    return prefix + value\n",
            "def ensure_prefix(value, prefix):\n    if value.startswith(prefix):\n        return value\n    return prefix + value\n",
            "from solution import ensure_prefix\n\n\ndef test_ensure_prefix_is_idempotent():\n    assert ensure_prefix('gh-123', 'gh-') == 'gh-123'\n    assert ensure_prefix('123', 'gh-') == 'gh-123'\n",
            "Prefix insertion should not duplicate an existing prefix.",
        ),
        case(
            "case-050",
            "JSON lines parsing",
            "import json\n\n\ndef parse_json_lines(text):\n    return [json.loads(text)]\n",
            "import json\n\n\ndef parse_json_lines(text):\n    return [json.loads(line) for line in text.splitlines() if line.strip()]\n",
            "from solution import parse_json_lines\n\n\ndef test_parse_json_lines_multiple_rows():\n    assert parse_json_lines('{\"a\": 1}\\n{\"b\": 2}') == [{'a': 1}, {'b': 2}]\n",
            "JSON-lines parsing should decode each nonblank line separately.",
        ),
    ]
    if suite_size < 1 or suite_size > len(all_cases):
        raise ValueError("suite_size must be between 1 and %d" % len(all_cases))
    return all_cases[:suite_size]


def case(case_id: str, title: str, buggy_source: str, fixed_source: str, test_source: str, issue: str) -> CaseSpec:
    return CaseSpec(case_id, title, buggy_source, fixed_source, test_source, issue)


def suite_label_from_size(suite_size: int) -> str:
    return "SWE-HarnessExec-%d" % suite_size


def suite_tag(suite_label: str) -> str:
    if suite_label.startswith("SWE-HarnessExec-"):
        return "swe_harness_exec%s" % suite_label.rsplit("-", 1)[-1]
    return suite_label.lower().replace("-", "_")


def suite_artifact_stem(suite_label: str) -> str:
    return suite_tag(suite_label) + "_cases"


def case_to_task(case_spec: CaseSpec, audit_date: str, suite_label: str = "SWE-HarnessExec-20") -> TaskExample:
    return TaskExample(
        task_id="swe-harness-exec-%03d" % int(case_spec.case_id.split("-")[-1]),
        query=(
            "%s task %s: %s. Inspect the local sandbox repository, preserve durable state, "
            "run the failing pytest test, apply the provided patch to solution.py, rerun the test, capture "
            "execution logs, and verify the diff. This is sandbox-only executable trace validation, not "
            "SWE-bench pass@1."
        )
        % (suite_label, case_spec.case_id, case_spec.issue),
        gold_obligations=frozen(REQUIRED_OBLIGATIONS),
        required_capabilities=frozen(REQUIRED_CAPABILITIES),
        oracle_minimal_harness=REQUIRED_MODULES,
        success_checker="swe_harness_exec_patch_tests_pass",
        expected_failure_if_direct="would_skip_repo_inspection_test_execution_patch_state_permission_or_verification",
        risk_level="medium",
        category="swe_harness_exec",
        expected_status="supported",
        tags=(
            suite_tag(suite_label),
            "executable_trace",
            "sandbox_only",
            "pytest",
            "not_swe_bench_pass_at_1",
            "case:%s" % case_spec.case_id,
        ),
        notes="Author-reviewed executable sandbox fixture as of %s." % audit_date,
        gold_source="author_reviewed_executable_trace_%s" % audit_date.replace("-", "_"),
    )


def run_case_trace(
    case_spec: CaseSpec,
    task: TaskExample,
    system: str,
    profiler: str,
    harness: Mapping[str, object],
    out_dir: Path,
) -> Mapping[str, object]:
    workspace = out_dir / "sandboxes" / system / case_spec.case_id
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    write_case_workspace(case_spec, workspace)

    trace: list[dict[str, object]] = [
        {
            "step": 0,
            "module": "compiler",
            "event_type": "compiled_harness",
            "message": "Compiled %s harness for %s." % (system, case_spec.case_id),
            "evidence": {"status": harness["status"], "modules": harness["modules"], "profiler": profiler},
        }
    ]
    selected = set(harness.get("modules", []))
    missing = [module for module in REQUIRED_MODULES if module not in selected]
    if harness.get("status") != "supported" or missing:
        trace.append(
            {
                "step": 1,
                "module": "trace_verifier",
                "event_type": "boundary_failure",
                "message": "Executable trace stopped because required modules are missing.",
                "evidence": {"missing_modules": missing, "status": harness.get("status")},
            }
        )
        return {
            "sandbox_path": str(workspace),
            "trace": trace,
            "exec_metrics": {
                "trace_success": False,
                "pre_test_failed": False,
                "post_test_passed": False,
                "patch_applied": False,
                "missing_required_modules": missing,
            },
        }

    trace.append(
        {
            "step": 1,
            "module": "file_state_reader",
            "event_type": "workspace_snapshot",
            "message": "Captured initial sandbox files.",
            "evidence": {"files": sorted(path.name for path in workspace.iterdir())},
        }
    )
    pre = run_pytest(workspace)
    trace.append(
        {
            "step": 2,
            "module": "python_executor",
            "event_type": "pre_patch_test",
            "message": "Ran pytest before applying the patch.",
            "evidence": test_evidence(pre),
        }
    )
    patch_text = unified_diff(case_spec.buggy_source, case_spec.fixed_source)
    (workspace / "solution.py").write_text(case_spec.fixed_source, encoding="utf-8")
    (workspace / "patch.diff").write_text(patch_text, encoding="utf-8")
    trace.append(
        {
            "step": 3,
            "module": "sandbox_file_editor",
            "event_type": "patch_applied",
            "message": "Applied provided sandbox patch to solution.py.",
            "evidence": {"patch_lines": patch_text.count("\n"), "patch_path": str(workspace / "patch.diff")},
        }
    )
    post = run_pytest(workspace)
    trace.append(
        {
            "step": 4,
            "module": "execution_log_checker",
            "event_type": "post_patch_test",
            "message": "Ran pytest after applying the patch.",
            "evidence": test_evidence(post),
        }
    )
    patch_applied = (workspace / "solution.py").read_text(encoding="utf-8") == case_spec.fixed_source
    trace_success = pre.returncode != 0 and post.returncode == 0 and patch_applied
    trace.append(
        {
            "step": 5,
            "module": "contract_verifier",
            "event_type": "trace_contract",
            "message": "Verified pre-test failure, post-test success, and patch application.",
            "evidence": {
                "pre_test_failed": pre.returncode != 0,
                "post_test_passed": post.returncode == 0,
                "patch_applied": patch_applied,
                "trace_success": trace_success,
            },
        }
    )
    return {
        "sandbox_path": str(workspace),
        "trace": trace,
        "exec_metrics": {
            "trace_success": trace_success,
            "pre_test_failed": pre.returncode != 0,
            "post_test_passed": post.returncode == 0,
            "patch_applied": patch_applied,
            "missing_required_modules": [],
        },
    }


def write_case_workspace(case_spec: CaseSpec, workspace: Path) -> None:
    (workspace / "solution.py").write_text(case_spec.buggy_source, encoding="utf-8")
    (workspace / "test_solution.py").write_text(case_spec.test_source, encoding="utf-8")
    (workspace / "README.md").write_text("# %s\n\n%s\n" % (case_spec.title, case_spec.issue), encoding="utf-8")


def run_pytest(workspace: Path) -> subprocess.CompletedProcess[str]:
    pycache = workspace / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(workspace),
        text=True,
        capture_output=True,
        env={**dict(os_environ()), "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=30,
        check=False,
    )


def os_environ() -> Mapping[str, str]:
    import os

    return os.environ


def test_evidence(result: subprocess.CompletedProcess[str]) -> Mapping[str, object]:
    return {
        "returncode": result.returncode,
        "stdout_tail": tail(result.stdout),
        "stderr_tail": tail(result.stderr),
    }


def tail(value: str, limit: int = 1200) -> str:
    value = value.strip()
    return value[-limit:] if len(value) > limit else value


def unified_diff(before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile="solution.py.before",
            tofile="solution.py.after",
        )
    )


def write_benchmark_artifacts(
    benchmark_dir: Path,
    tasks: Sequence[TaskExample],
    audit_date: str,
    suite_label: str = "SWE-HarnessExec-20",
) -> None:
    write_jsonl(str(benchmark_dir / ("%s.jsonl" % suite_artifact_stem(suite_label))), [task.to_json() for task in tasks])
    with (benchmark_dir / "review_sheet.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "task_id",
            "query",
            "gold_obligations",
            "required_capabilities",
            "oracle_minimal_harness",
            "expected_status",
            "review_decision",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for task in tasks:
            writer.writerow(
                {
                    "task_id": task.task_id,
                    "query": one_line(task.query),
                    "gold_obligations": json.dumps(sorted(task.gold_obligations)),
                    "required_capabilities": json.dumps(sorted(task.required_capabilities)),
                    "oracle_minimal_harness": json.dumps(list(task.oracle_minimal_harness)),
                    "expected_status": task.expected_status,
                    "review_decision": "author_reviewed_executable_fixture",
                }
            )
    (benchmark_dir / "README.md").write_text(
        "\n".join(
            [
                "# %s" % suite_label,
                "",
                "%s is a small executable trace validation over sandboxed software-maintenance fixtures." % suite_label,
                "",
                "Each case creates a local Python repo, runs a failing pytest test, applies a provided patch, reruns pytest, and verifies that the trace contains the required inspection, execution, action, state, control, and verification affordances.",
                "",
                "This is not SWE-bench pass@1, not repository checkout from SWE-bench, and not model patch generation. It is execution-level evidence that the harness loop can drive real files and tests.",
                "",
                "Audit status: author-reviewed executable fixtures as of %s." % audit_date,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (benchmark_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": suite_label,
                "version": "v1.1" if suite_label.endswith("-50") else "v1.0",
                "created": audit_date,
                "n": len(tasks),
                "audit_status": "author-reviewed executable fixtures; independent human audit not claimed",
                "claim_boundary": "sandboxed executable trace validation, not SWE-bench pass@1",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def render_manifest(
    tasks: Sequence[TaskExample],
    rows: Sequence[Mapping[str, object]],
    audit_date: str,
    suite_label: str = "SWE-HarnessExec-20",
) -> str:
    by_system = summarize_exec(rows)
    return (
        json.dumps(
            {
                "name": "%s run" % suite_label,
                "created": audit_date,
                "n_tasks": len(tasks),
                "n_rows": len(rows),
                "systems": by_system,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def render_report(rows: Sequence[Mapping[str, object]], suite_label: str = "SWE-HarnessExec-20") -> str:
    summary = summarize_exec(rows)
    lines = [
        "# %s Executable Trace Validation" % suite_label,
        "",
        "This experiment runs real sandbox files and pytest commands. It validates the harness execution loop with provided patches; it does not claim model patch generation or SWE-bench pass@1.",
        "",
        "| System | N | Coverage HS | Trace Success | Avg Cost | Pre-test Failed | Post-test Passed | Missing Module Rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system in sorted(summary):
        item = summary[system]
        lines.append(
            "| %s | %d | %.2f | %.2f | %.2f | %.2f | %.2f | %.2f |"
            % (
                system,
                item["n"],
                item["coverage_hs"],
                item["trace_success"],
                item["avg_cost"],
                item["pre_test_failed"],
                item["post_test_passed"],
                item["missing_module_rate"],
            )
        )
    lines.extend(
        [
            "",
            "## Failure Interpretation",
            "",
            "Rows that lack `file_state_reader`, `python_executor`, `execution_log_checker`, `sandbox_file_editor`, `permission_gate`, `state_store`, or `contract_verifier` stop before the executable trace. This is intentional: the experiment checks that systems without the declared affordances do not silently perform sandbox patch/test workflows.",
        ]
    )
    return "\n".join(lines) + "\n"


def summarize_exec(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        buckets[str(row["system"])].append(row)
    out: dict[str, dict[str, float]] = {}
    for system, bucket in buckets.items():
        out[system] = {
            "n": len(bucket),
            "coverage_hs": mean(row["coverage_metrics"]["success"] for row in bucket),
            "trace_success": mean(row["exec_metrics"]["trace_success"] for row in bucket),
            "avg_cost": mean(row["coverage_metrics"]["predicted_cost"] for row in bucket),
            "pre_test_failed": mean(row["exec_metrics"]["pre_test_failed"] for row in bucket),
            "post_test_passed": mean(row["exec_metrics"]["post_test_passed"] for row in bucket),
            "missing_module_rate": mean(bool(row["exec_metrics"]["missing_required_modules"]) for row in bucket),
        }
    return out


def mean(values: Iterable[object]) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(float(value) for value in values_list) / float(len(values_list))


def one_line(value: str) -> str:
    return " ".join(value.split())


if __name__ == "__main__":
    raise SystemExit(main())
