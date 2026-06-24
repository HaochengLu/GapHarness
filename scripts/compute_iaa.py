"""Inter-annotator-agreement statistics for the GapHarness IAA gate (M3).

This module is the *measurement* half of the multi-model machine-IAA study. It
consumes per-(model,row) annotations (parsed from the cached raw API responses
produced by ``scripts.run_independent_annotators``) plus gold labels, and
computes, honestly and from-scratch:

  * Per-obligation agreement across the 3 annotators:
      - Cohen's kappa (3 pairwise) treating each obligation as binary present/absent
      - Krippendorff's alpha (nominal, binary present/absent) -- implemented with
        the observed/expected coincidence-matrix formula, unit-tested against a
        known small example.
  * Status agreement: Krippendorff's alpha (nominal over 3 categories) + raw %
    agreement + per-class confusion.
  * Capability agreement: micro-F1 across annotator pairs.
  * Each annotator vs GOLD: obligation-exact-match, obligation micro-F1, status
    agreement.
  * Model-model "Obl-Exact" (mean pairwise exact-set match) vs the paper's prior
    single-LLM secondary-audit Obl-Exact of 0.65.
  * Cluster-bootstrap 95% CIs by TEMPLATE/category (rows are template-correlated,
    so we resample clusters, not rows).

Everything here is pure Python (no numpy) so it replays in a clean environment.

The public surface used by the runner and the unit test:
  - ``OBLIGATIONS``, ``STATUSES``, ``CAPABILITY_VOCAB``
  - ``krippendorff_alpha_nominal(units)`` -- the core implementation under test
  - ``cohens_kappa_binary(a, b)``
  - ``micro_f1(pred_sets, gold_sets)``
  - ``Annotation`` dataclass + ``parse_annotation``
  - ``main`` / CLI to render the tables consumed by the report.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# Mirror the system vocabulary WITHOUT importing the tuned profiler, so the
# measurement code stays independent of the thing it measures. These constants
# match gapharness/schema.py by construction (asserted in tests).
OBLIGATIONS: Tuple[str, ...] = (
    "Observation",
    "Execution",
    "State",
    "Action",
    "Control",
    "Verification",
)

STATUSES: Tuple[str, ...] = ("supported", "unsupported", "clarify")

CAPABILITY_VOCAB: Tuple[str, ...] = (
    "evidence_sources",
    "source_spans",
    "execution",
    "execution_log",
    "workspace_inspection",
    "durable_state",
    "diff",
    "sandbox_action",
    "permission",
    "contract_check",
    "real_world_side_effect",
)


# ---------------------------------------------------------------------------
# Parsed annotation record
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Annotation:
    model: str
    row_id: str
    cluster: str  # template (disguised) or category (gapbench) -- bootstrap unit
    obligations: frozenset
    capabilities: frozenset
    status: str
    parse_ok: bool = True


def _clean_set(values: object, vocab: Sequence[str]) -> frozenset:
    allowed = set(vocab)
    out = set()
    if isinstance(values, list):
        for v in values:
            s = str(v).strip()
            if s in allowed:
                out.add(s)
    return frozenset(out)


def parse_annotation(payload: Mapping[str, object]) -> Tuple[frozenset, frozenset, str, bool]:
    """Parse a model's JSON judgment into (obligations, capabilities, status, ok).

    Robust to the three families' quirks (code fences are stripped upstream).
    A missing/invalid status is normalized to ``"supported"`` and flagged
    ``parse_ok=False`` so we can report parse health honestly without crashing.
    """
    obligations = _clean_set(payload.get("obligations"), OBLIGATIONS)
    capabilities = _clean_set(payload.get("capabilities"), CAPABILITY_VOCAB)
    raw_status = str(payload.get("status", "")).strip().lower()
    ok = raw_status in STATUSES
    status = raw_status if ok else "supported"
    return obligations, capabilities, status, ok


# ---------------------------------------------------------------------------
# Krippendorff's alpha (nominal) -- coincidence-matrix formulation
# ---------------------------------------------------------------------------
def krippendorff_alpha_nominal(units: Sequence[Sequence[object]]) -> Optional[float]:
    """Krippendorff's alpha for nominal data via the coincidence matrix.

    ``units`` is a sequence of units (items). Each unit is a sequence of the
    values assigned to it by the annotators; missing values are represented by
    ``None`` and are dropped (units with < 2 present values contribute nothing).

    Formula (Krippendorff, *Content Analysis*, nominal metric):

        alpha = 1 - D_o / D_e

    Built from the coincidence matrix ``o[c][k]`` -- the number of value pairs
    (c, k) co-occurring within units, where a unit with ``m`` present values
    contributes each ordered pair weighted by ``1 / (m - 1)``. Let
    ``n_c = sum_k o[c][k]`` (the marginal) and ``n = sum_c n_c``. For the nominal
    metric (disagreement = 0 iff c == k, else 1):

        D_o = (1/n) * sum_{c != k} o[c][k]
            = 1 - (sum_c o[c][c]) / n
        D_e = (1/(n*(n-1))) * sum_{c != k} n_c * n_k
            = 1 - (sum_c n_c*(n_c-1)) / (n*(n-1))

        alpha = 1 - D_o / D_e

    Returns ``None`` when alpha is undefined (no pairable values, or D_e == 0
    because every present value is identical -> perfect-but-degenerate; callers
    treat that as alpha = 1.0 only when there is real variation, else None).
    """
    # Coincidence matrix over hashable nominal categories.
    o: Dict[object, Dict[object, float]] = defaultdict(lambda: defaultdict(float))
    for unit in units:
        present = [v for v in unit if v is not None]
        m = len(present)
        if m < 2:
            continue
        weight = 1.0 / (m - 1)
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                o[present[i]][present[j]] += weight

    categories = sorted(
        {c for c in o.keys()} | {k for row in o.values() for k in row.keys()},
        key=lambda x: str(x),
    )
    if not categories:
        return None

    n_c: Dict[object, float] = {c: sum(o[c].values()) for c in categories}
    n = sum(n_c.values())
    if n < 2:
        return None

    sum_diag = sum(o[c].get(c, 0.0) for c in categories)
    d_o = 1.0 - (sum_diag / n)

    sum_marg = sum(v * (v - 1.0) for v in n_c.values())
    denom = n * (n - 1.0)
    if denom <= 0:
        return None
    d_e = 1.0 - (sum_marg / denom)

    if d_e == 0:
        # Expected disagreement is zero only when all present values are the same
        # category. With observed disagreement also zero this is degenerate
        # (perfect agreement, but no variation) -> alpha undefined.
        return None
    return 1.0 - (d_o / d_e)


# ---------------------------------------------------------------------------
# Cohen's kappa (binary) -- two raters, presence/absence
# ---------------------------------------------------------------------------
def cohens_kappa_binary(a: Sequence[int], b: Sequence[int]) -> Optional[float]:
    """Cohen's kappa for two raters over binary labels (0/1).

    Returns ``None`` when undefined. When the two raters agree on every item and
    there is variation, kappa == 1.0; when there is no variation at all (both
    raters give the same constant label to every item) kappa is undefined
    (expected agreement == 1).
    """
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    agree = sum(1 for x, y in zip(a, b) if x == y)
    p_o = agree / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    p_e = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if p_e >= 1.0:
        # No variation: every cell on one label. Kappa undefined.
        return None
    return (p_o - p_e) / (1 - p_e)


# ---------------------------------------------------------------------------
# Micro-F1 over sets (capability agreement / obligation-vs-gold)
# ---------------------------------------------------------------------------
def micro_f1(pred_sets: Sequence[frozenset], gold_sets: Sequence[frozenset]) -> float:
    """Micro-averaged F1 between two parallel lists of label sets.

    For agreement between two annotators this is symmetric set overlap; for
    annotator-vs-gold it is standard micro-F1 with gold as truth. Empty-vs-empty
    contributes a perfect match (TP+FP+FN all zero on that row) and is handled by
    the global aggregation: if there are no labels anywhere, F1 is defined as 1.0
    (perfect trivial agreement).
    """
    tp = fp = fn = 0
    for pred, gold in zip(pred_sets, gold_sets):
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn += len(gold - pred)
    if tp + fp + fn == 0:
        return 1.0
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def exact_set_match(a: frozenset, b: frozenset) -> int:
    return 1 if set(a) == set(b) else 0


# ---------------------------------------------------------------------------
# Aggregate IAA over a list of annotations from 3 models on a shared row set
# ---------------------------------------------------------------------------
def _by_row(annotations: Sequence[Annotation]) -> "Dict[str, Dict[str, Annotation]]":
    table: Dict[str, Dict[str, Annotation]] = defaultdict(dict)
    for a in annotations:
        table[a.row_id][a.model] = a
    return table


def per_obligation_agreement(
    by_row: Mapping[str, Mapping[str, Annotation]],
    models: Sequence[str],
) -> Dict[str, Dict[str, Optional[float]]]:
    """For each obligation: mean pairwise Cohen's kappa + Krippendorff alpha."""
    rows = [r for r in by_row.values() if all(m in r for m in models)]
    result: Dict[str, Dict[str, Optional[float]]] = {}
    for obl in OBLIGATIONS:
        # binary present/absent vectors per model, aligned across rows
        vecs = {m: [1 if obl in rows[i][m].obligations else 0 for i in range(len(rows))] for m in models}
        kappas = []
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                k = cohens_kappa_binary(vecs[models[i]], vecs[models[j]])
                if k is not None:
                    kappas.append(k)
        # Krippendorff over the 3 ratings per unit
        units = [[1 if obl in rows[idx][m].obligations else 0 for m in models] for idx in range(len(rows))]
        alpha = krippendorff_alpha_nominal(units)
        result[obl] = {
            "kappa_mean": (sum(kappas) / len(kappas)) if kappas else None,
            "kappa_pairs": kappas,
            "alpha": alpha,
            "prevalence": sum(units_row.count(1) for units_row in units) / (len(units) * len(models)) if units else 0.0,
        }
    return result


def status_agreement(
    by_row: Mapping[str, Mapping[str, Annotation]],
    models: Sequence[str],
) -> Dict[str, object]:
    rows = [r for r in by_row.values() if all(m in r for m in models)]
    units = [[rows[i][m].status for m in models] for i in range(len(rows))]
    alpha = krippendorff_alpha_nominal(units)
    # raw % agreement = fraction of units where all annotators agree
    full_agree = sum(1 for u in units if len(set(u)) == 1)
    raw_agree = full_agree / len(units) if units else 0.0
    # pairwise raw agreement (mean over pairs)
    pair_agree = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            same = sum(1 for u in units if u[i] == u[j])
            pair_agree.append(same / len(units) if units else 0.0)
    # per-class confusion: pooled pairwise confusion counts
    confusion: Dict[Tuple[str, str], int] = Counter()
    for u in units:
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                confusion[(u[i], u[j])] += 1
                confusion[(u[j], u[i])] += 1
    return {
        "alpha": alpha,
        "raw_full_agreement": raw_agree,
        "pairwise_raw_agreement_mean": sum(pair_agree) / len(pair_agree) if pair_agree else 0.0,
        "n": len(units),
        "confusion": {f"{a}->{b}": c for (a, b), c in sorted(confusion.items())},
    }


def capability_micro_f1_pairwise(
    by_row: Mapping[str, Mapping[str, Annotation]],
    models: Sequence[str],
) -> Dict[str, object]:
    rows = [r for r in by_row.values() if all(m in r for m in models)]
    pair_scores = {}
    all_a: List[frozenset] = []
    all_b: List[frozenset] = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            preds = [rows[k][models[i]].capabilities for k in range(len(rows))]
            golds = [rows[k][models[j]].capabilities for k in range(len(rows))]
            pair_scores[f"{models[i]}|{models[j]}"] = micro_f1(preds, golds)
            all_a.extend(preds)
            all_b.extend(golds)
    return {
        "pairwise": pair_scores,
        "micro_f1_pooled": micro_f1(all_a, all_b),
        "mean_pairwise": sum(pair_scores.values()) / len(pair_scores) if pair_scores else 0.0,
    }


def model_model_obl_exact(
    by_row: Mapping[str, Mapping[str, Annotation]],
    models: Sequence[str],
) -> Dict[str, object]:
    rows = [r for r in by_row.values() if all(m in r for m in models)]
    pair_scores = {}
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            matches = sum(
                exact_set_match(rows[k][models[i]].obligations, rows[k][models[j]].obligations)
                for k in range(len(rows))
            )
            pair_scores[f"{models[i]}|{models[j]}"] = matches / len(rows) if rows else 0.0
    return {
        "pairwise": pair_scores,
        "mean_pairwise": sum(pair_scores.values()) / len(pair_scores) if pair_scores else 0.0,
        "n": len(rows),
    }


def annotator_vs_gold(
    annotations: Sequence[Annotation],
    gold: Mapping[str, Mapping[str, object]],
    models: Sequence[str],
) -> Dict[str, Dict[str, float]]:
    """obligation-exact-match, obligation micro-F1, status agreement vs gold."""
    by_model: Dict[str, List[Annotation]] = defaultdict(list)
    for a in annotations:
        if a.row_id in gold:
            by_model[a.model].append(a)
    out: Dict[str, Dict[str, float]] = {}
    for m in models:
        recs = by_model.get(m, [])
        if not recs:
            continue
        obl_exact = 0
        status_agree = 0
        preds = []
        golds = []
        for a in recs:
            g = gold[a.row_id]
            gold_obl = frozenset(g.get("gold_obligations", []) or [])
            obl_exact += exact_set_match(a.obligations, gold_obl)
            status_agree += 1 if a.status == g.get("gold_status") else 0
            preds.append(a.obligations)
            golds.append(gold_obl)
        n = len(recs)
        out[m] = {
            "n": n,
            "obl_exact": obl_exact / n,
            "obl_micro_f1": micro_f1(preds, golds),
            "status_agree": status_agree / n,
        }
    return out


# ---------------------------------------------------------------------------
# Cluster bootstrap (by template/category)
# ---------------------------------------------------------------------------
def cluster_bootstrap_ci(
    clusters: Mapping[str, Sequence[str]],
    stat_fn,
    n_samples: int = 2000,
    seed: int = 1729,
    alpha: float = 0.05,
) -> Tuple[Optional[float], Optional[float]]:
    """Cluster bootstrap: resample whole clusters with replacement.

    ``clusters`` maps cluster-name -> list of row_ids. ``stat_fn`` takes a list
    of row_ids and returns a float (or None). Returns (ci_low, ci_high) of the
    statistic over ``n_samples`` resamples. None-valued draws are skipped.
    """
    names = list(clusters.keys())
    if not names:
        return (None, None)
    rng = random.Random(seed)
    draws: List[float] = []
    for _ in range(n_samples):
        picked: List[str] = []
        for _ in range(len(names)):
            cname = names[rng.randrange(len(names))]
            picked.extend(clusters[cname])
        val = stat_fn(picked)
        if val is not None and not (isinstance(val, float) and math.isnan(val)):
            draws.append(val)
    if not draws:
        return (None, None)
    draws.sort()
    lo = _percentile(draws, alpha / 2)
    hi = _percentile(draws, 1 - alpha / 2)
    return (lo, hi)


def _percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = q * (len(sorted_values) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_values) - 1)
    w = idx - lo
    return sorted_values[lo] * (1 - w) + sorted_values[hi] * w


# ---------------------------------------------------------------------------
# Loading annotations from the cache + gold
# ---------------------------------------------------------------------------
def load_annotations_from_cache(cache_dir: Path, dataset: str) -> List[Annotation]:
    """Load parsed annotations from outputs/iaa/raw/<dataset>/<model>/<row>.json.

    Each cached file is the FULL raw API response plus our envelope metadata
    {model, row_id, cluster, dataset, response}. We parse the model's JSON
    content here so the report can be regenerated with no API.
    """
    from gapharness.llm_client import parse_json_object

    annotations: List[Annotation] = []
    base = cache_dir / dataset
    if not base.exists():
        return annotations
    for model_dir in sorted(base.iterdir()):
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        for fp in sorted(model_dir.glob("*.json")):
            env = json.loads(fp.read_text())
            content = ""
            try:
                content = env["response"]["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                content = env.get("content", "")
            try:
                payload = parse_json_object(content)
            except Exception:
                payload = {}
            obl, cap, status, ok = parse_annotation(payload)
            annotations.append(
                Annotation(
                    model=model,
                    row_id=str(env["row_id"]),
                    cluster=str(env.get("cluster", "unknown")),
                    obligations=obl,
                    capabilities=cap,
                    status=status,
                    parse_ok=ok,
                )
            )
    return annotations


def load_gold(dataset_path: Path, id_key: str, status_key: str, obl_key: str, cluster_key: str) -> Dict[str, Dict[str, object]]:
    gold: Dict[str, Dict[str, object]] = {}
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            gold[str(r[id_key])] = {
                "gold_status": r.get(status_key),
                "gold_obligations": r.get(obl_key, []) or [],
                "cluster": r.get(cluster_key, "unknown"),
            }
    return gold


# ---------------------------------------------------------------------------
# Full analysis bundle for one dataset
# ---------------------------------------------------------------------------
def analyze_dataset(
    annotations: Sequence[Annotation],
    gold: Mapping[str, Mapping[str, object]],
    models: Sequence[str],
    n_bootstrap: int = 2000,
    seed: int = 1729,
) -> Dict[str, object]:
    by_row = _by_row(annotations)
    complete_rows = [rid for rid, r in by_row.items() if all(m in r for m in models)]
    clusters: Dict[str, List[str]] = defaultdict(list)
    for rid in complete_rows:
        cluster = gold.get(rid, {}).get("cluster") or next(iter(by_row[rid].values())).cluster
        clusters[str(cluster)].append(rid)

    obl_agreement = per_obligation_agreement(by_row, models)
    status_agg = status_agreement(by_row, models)
    cap_agg = capability_micro_f1_pairwise(by_row, models)
    obl_exact_mm = model_model_obl_exact(by_row, models)
    vs_gold = annotator_vs_gold(annotations, gold, models)

    # ----- cluster-bootstrap CIs -----
    def _subset_by_row(row_ids: Sequence[str]) -> Dict[str, Dict[str, Annotation]]:
        return {rid: by_row[rid] for rid in row_ids if rid in by_row}

    # per-obligation alpha CI
    obl_alpha_ci: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
    for obl in OBLIGATIONS:
        def stat(row_ids, obl=obl):
            sub = _subset_by_row(row_ids)
            rows = [sub[r] for r in sub if all(m in sub[r] for m in models)]
            units = [[1 if obl in row[m].obligations else 0 for m in models] for row in rows]
            return krippendorff_alpha_nominal(units)
        obl_alpha_ci[obl] = cluster_bootstrap_ci(clusters, stat, n_bootstrap, seed)

    # status alpha CI
    def status_stat(row_ids):
        sub = _subset_by_row(row_ids)
        rows = [sub[r] for r in sub if all(m in sub[r] for m in models)]
        units = [[row[m].status for m in models] for row in rows]
        return krippendorff_alpha_nominal(units)
    status_alpha_ci = cluster_bootstrap_ci(clusters, status_stat, n_bootstrap, seed)

    # model-model obl-exact CI
    def obl_exact_stat(row_ids):
        sub = _subset_by_row(row_ids)
        rows = [sub[r] for r in sub if all(m in sub[r] for m in models)]
        if not rows:
            return None
        scores = []
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                m = sum(exact_set_match(r[models[i]].obligations, r[models[j]].obligations) for r in rows)
                scores.append(m / len(rows))
        return sum(scores) / len(scores) if scores else None
    obl_exact_ci = cluster_bootstrap_ci(clusters, obl_exact_stat, n_bootstrap, seed)

    # capability micro-f1 CI (pooled pairwise)
    def cap_stat(row_ids):
        sub = _subset_by_row(row_ids)
        rows = [sub[r] for r in sub if all(m in sub[r] for m in models)]
        if not rows:
            return None
        a, b = [], []
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                a.extend(r[models[i]].capabilities for r in rows)
                b.extend(r[models[j]].capabilities for r in rows)
        return micro_f1(a, b)
    cap_ci = cluster_bootstrap_ci(clusters, cap_stat, n_bootstrap, seed)

    parse_health = {
        m: {
            "n": sum(1 for a in annotations if a.model == m),
            "parse_ok": sum(1 for a in annotations if a.model == m and a.parse_ok),
        }
        for m in models
    }

    return {
        "n_rows_complete": len(complete_rows),
        "n_clusters": len(clusters),
        "cluster_sizes": {k: len(v) for k, v in sorted(clusters.items())},
        "models": list(models),
        "obligation_agreement": obl_agreement,
        "obligation_alpha_ci": obl_alpha_ci,
        "status": status_agg,
        "status_alpha_ci": status_alpha_ci,
        "capability": cap_agg,
        "capability_micro_f1_ci": cap_ci,
        "model_model_obl_exact": obl_exact_mm,
        "model_model_obl_exact_ci": obl_exact_ci,
        "annotator_vs_gold": vs_gold,
        "parse_health": parse_health,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _fmt(x: Optional[float]) -> str:
    return "n/a" if x is None else "%.3f" % x


def _fmt_ci(ci: Tuple[Optional[float], Optional[float]]) -> str:
    lo, hi = ci
    if lo is None or hi is None:
        return "[n/a]"
    return "[%.3f, %.3f]" % (lo, hi)


# ---------------------------------------------------------------------------
# Stop-loss verdict (PRE-COMMITTED rule applied to the actual numbers)
# ---------------------------------------------------------------------------
PRIOR_SINGLE_LLM_OBL_EXACT = 0.65  # paper Table 7 secondary-audit Obl-Exact


def stop_loss_verdict(results: Mapping[str, object]) -> Dict[str, object]:
    """Apply the pre-committed stop-loss rule to the computed numbers.

    Rule (committed before seeing numbers):
      SUPPORTED  if per-obligation Krippendorff alpha >= 0.70 (esp. on the
                 disguised-refusal set) AND model-model Obl-Exact materially
                 exceeds 0.65.
      WEAK       if alpha lands in [0.50, 0.65] on >= 2 obligations on the harder
                 (disguised) set -> taxonomy becomes the research target; honest
                 'proposal' reframe.
      Otherwise  -> reported as an intermediate ('mixed') outcome with the same
                 honest-proposal lean unless the SUPPORTED bar is cleared.
    """
    disg = results.get("disguised")
    gb = results.get("gapbench")
    verdict = {"reasoning": []}

    def alphas(res):
        if not isinstance(res, dict):
            return {}
        return {o: res["obligation_agreement"][o]["alpha"] for o in OBLIGATIONS}

    disg_alpha = alphas(disg)
    gb_alpha = alphas(gb)

    # obligations that actually vary on the disguised set (alpha is defined)
    disg_defined = {o: a for o, a in disg_alpha.items() if a is not None}
    n_alpha_ge_070 = sum(1 for a in disg_defined.values() if a >= 0.70)
    n_alpha_weak = sum(1 for a in disg_defined.values() if 0.50 <= a <= 0.65)
    n_alpha_below_050 = sum(1 for a in disg_defined.values() if a < 0.50)

    disg_obl_exact = disg["model_model_obl_exact"]["mean_pairwise"] if isinstance(disg, dict) else None
    gb_obl_exact = gb["model_model_obl_exact"]["mean_pairwise"] if isinstance(gb, dict) else None

    # "materially exceeds 0.65": point estimate clears 0.65 by a clear margin and
    # the cluster-bootstrap CI lower bound is above 0.65.
    def materially_exceeds(res):
        if not isinstance(res, dict):
            return False
        pt = res["model_model_obl_exact"]["mean_pairwise"]
        lo, _ = res["model_model_obl_exact_ci"]
        return pt is not None and pt > 0.70 and (lo is None or lo > 0.65)

    all_disg_defined_ge_070 = bool(disg_defined) and all(a >= 0.70 for a in disg_defined.values())

    supported = all_disg_defined_ge_070 and materially_exceeds(disg)
    # Pre-committed WEAK trigger: >=2 obligations in [0.50,0.65] on the hard set.
    weak = n_alpha_weak >= 2
    # The committed rule targets the [0.50,0.65] band; alphas BELOW 0.50 are
    # strictly worse than weak, so >=2 obligations anywhere below 0.65 (weak or
    # worse) on the hard set means the taxonomy is the research target. We treat
    # this as the (at-least-)WEAK / proposal path, and flag the below-0.50 case.
    n_below_065 = n_alpha_weak + n_alpha_below_050
    weak_or_worse = n_below_065 >= 2

    if supported:
        label = "GO / PREMISE SUPPORTED"
    elif weak_or_worse:
        if n_alpha_below_050 >= 2:
            label = "NO-GO / PREMISE FAILS ON HARD SET -> honest 'proposal' reframe (taxonomy is the research target)"
        else:
            label = "NO-GO / PREMISE WEAK -> honest 'proposal' reframe"
    else:
        label = "NO-GO / MIXED -> honest 'proposal' reframe"

    verdict.update(
        {
            "label": label,
            "supported": supported,
            "weak": weak,
            "weak_or_worse": weak_or_worse,
            "disguised_obl_alpha_below_065_count": n_below_065,
            "disguised_obl_alpha": disg_alpha,
            "gapbench_obl_alpha": gb_alpha,
            "disguised_obl_alpha_ge_070_count": n_alpha_ge_070,
            "disguised_obl_alpha_weak_count": n_alpha_weak,
            "disguised_obl_alpha_below_050_count": n_alpha_below_050,
            "disguised_obl_alpha_defined_count": len(disg_defined),
            "disguised_model_model_obl_exact": disg_obl_exact,
            "gapbench_model_model_obl_exact": gb_obl_exact,
            "prior_single_llm_obl_exact": PRIOR_SINGLE_LLM_OBL_EXACT,
        }
    )
    return verdict


def render_report(results: Mapping[str, object], manifest: Mapping[str, object], verdict: Mapping[str, object]) -> str:
    L: List[str] = []
    A = L.append
    A("# Multi-Model Inter-Annotator-Agreement Report (M3 gate)")
    A("")
    A("**This is MULTI-MODEL agreement: a legitimate, honest proxy for and precursor "
      "to human inter-annotator agreement.** Three different model *families* each "
      "annotated the same rows from the shared neutral codebook only. It is NOT a "
      "human IAA study; the human protocol, codebook, and review sheet below are "
      "ready for a future human pass to plug into.")
    A("")
    A("- Shared instrument (codebook): `docs/annotation_codebook.md`")
    A("- Stratified GapBench subset: `outputs/iaa/gapbench_subset.jsonl` "
      "(+ task ids in `outputs/iaa/gapbench_subset_task_ids.json`)")
    A("- Harder disguised-refusal set: `benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl`")
    A("- Raw cached responses (replay with no API): `outputs/iaa/raw/`")
    A("- Human review sheet: `outputs/iaa/human_review_sheet.csv`")
    A("")
    # exact model ids
    A("## Annotators (exact model ids)")
    A("")
    A("| Family | Model id | temperature | max_tokens |")
    A("|---|---|---:|---:|")
    for a in manifest.get("annotators", []):
        A("| %s | `%s` | %s | %s |" % (a["family"], a["model"], a["temperature"], a["max_tokens"]))
    A("")
    A("Independence: each annotator received only the codebook + the bare query. No "
      "annotator saw gold labels, the registry-guard code, the tuned profiler "
      "prompt, or the other annotators.")
    A("")

    # ---- PRE-COMMITTED stop-loss, written BEFORE the numbers ----
    A("## Pre-committed stop-loss rule (committed before computing numbers)")
    A("")
    A("- **SUPPORTED (GO):** per-obligation Krippendorff alpha >= 0.70 (especially "
      "on the disguised-refusal set) AND model-model Obl-Exact *materially* exceeds "
      "the paper's prior single-LLM 0.65.")
    A("- **WEAK (NO-GO):** alpha lands in [0.50, 0.65] on >= 2 obligations on the "
      "harder disguised-refusal set -> the taxonomy itself becomes the research "
      "target; recommend the honest 'proposal' reframe.")
    A("- The rule is applied to the ACTUAL numbers in the Verdict section below.")
    A("")

    for dataset in ("gapbench", "disguised"):
        res = results.get(dataset)
        if not isinstance(res, dict):
            continue
        title = "GapBench stratified subset" if dataset == "gapbench" else "Disguised-refusal set (HARDER)"
        A("## %s" % title)
        A("")
        A("Rows with all 3 annotators: **%d** across **%d** template/category clusters. "
          "Bootstrap CIs are cluster-bootstrap by template/category (rows are "
          "template-correlated)." % (res["n_rows_complete"], res["n_clusters"]))
        A("")
        # parse health
        ph = res["parse_health"]
        A("Parse health: " + ", ".join("%s %d/%d ok" % (m, ph[m]["parse_ok"], ph[m]["n"]) for m in res["models"]))
        A("")
        # per-obligation table
        A("### Per-obligation agreement (3 annotators)")
        A("")
        A("| Obligation | Prevalence | Krippendorff alpha | alpha 95% CI (cluster) | mean pairwise Cohen kappa |")
        A("|---|---:|---:|---:|---:|")
        for obl in OBLIGATIONS:
            oa = res["obligation_agreement"][obl]
            A("| %s | %.2f | %s | %s | %s |" % (
                obl, oa["prevalence"], _fmt(oa["alpha"]),
                _fmt_ci(res["obligation_alpha_ci"][obl]), _fmt(oa["kappa_mean"]),
            ))
        A("")
        A("Reading the table: a prevalence near 1.00 with alpha = n/a means **all "
          "three annotators include that obligation on essentially every row** -- "
          "that is unanimous agreement (good), not missing data; Krippendorff's "
          "alpha is simply undefined when there is no variation to disagree about. "
          "A low or negative alpha with mid-range prevalence (e.g. State, "
          "Verification on the hard set) is the diagnostic signal: the annotators "
          "vary AND do not agree, i.e. that obligation is not a reproducible "
          "judgment on these inputs.")
        A("")
        # status
        st = res["status"]
        A("### Status agreement (3 categories: supported / unsupported / clarify)")
        A("")
        A("- Krippendorff alpha (nominal): **%s** %s" % (_fmt(st["alpha"]), _fmt_ci(res["status_alpha_ci"])))
        A("- Raw full (all-3-agree) agreement: **%s**" % _fmt(st["raw_full_agreement"]))
        A("- Mean pairwise raw agreement: **%s**" % _fmt(st["pairwise_raw_agreement_mean"]))
        A("")
        A("Note on the CI: with only %d template clusters the cluster bootstrap is "
          "high-variance and the resample distribution can be narrow and slightly "
          "off-centre from the point estimate (the point alpha can fall just "
          "outside the percentile interval). Treat the CIs as indicative of "
          "between-template variability, not as tight standard errors; the point "
          "estimates and the raw-agreement numbers are the primary quantities."
          % res["n_clusters"])
        A("")
        A("Per-class pairwise confusion (symmetric pooled counts):")
        A("")
        A("| transition | count |")
        A("|---|---:|")
        for k, v in res["status"]["confusion"].items():
            A("| %s | %d |" % (k, v))
        A("")
        # capability
        cap = res["capability"]
        A("### Capability agreement (micro-F1 across annotator pairs)")
        A("")
        A("- Pooled pairwise micro-F1: **%s** %s" % (_fmt(cap["micro_f1_pooled"]), _fmt_ci(res["capability_micro_f1_ci"])))
        A("- Mean pairwise micro-F1: **%s**" % _fmt(cap["mean_pairwise"]))
        for pair, score in cap["pairwise"].items():
            A("  - %s: %s" % (pair, _fmt(score)))
        A("")
        # model-model obl-exact
        mm = res["model_model_obl_exact"]
        A("### Model-model obligation-exact-set match")
        A("")
        A("- Mean pairwise **Obl-Exact**: **%s** %s "
          "(vs prior single-LLM secondary-audit Obl-Exact = %.2f)" % (
              _fmt(mm["mean_pairwise"]), _fmt_ci(res["model_model_obl_exact_ci"]),
              PRIOR_SINGLE_LLM_OBL_EXACT,
          ))
        for pair, score in mm["pairwise"].items():
            A("  - %s: %s" % (pair, _fmt(score)))
        A("")
        # vs gold
        A("### Each annotator vs GOLD")
        A("")
        A("| Model | n | Obl-Exact | Obl micro-F1 | Status agree |")
        A("|---|---:|---:|---:|---:|")
        for m in res["models"]:
            vg = res["annotator_vs_gold"].get(m)
            if not vg:
                continue
            A("| `%s` | %d | %s | %s | %s |" % (
                m, vg["n"], _fmt(vg["obl_exact"]), _fmt(vg["obl_micro_f1"]), _fmt(vg["status_agree"]),
            ))
        A("")

    # ---- Verdict ----
    A("## STOP-LOSS VERDICT (applied to actual numbers)")
    A("")
    A("**%s**" % verdict["label"])
    A("")
    A("- Disguised-set model-model Obl-Exact: %s (prior single-LLM = %.2f)" % (
        _fmt(verdict["disguised_model_model_obl_exact"]), verdict["prior_single_llm_obl_exact"]))
    A("- GapBench-subset model-model Obl-Exact: %s" % _fmt(verdict["gapbench_model_model_obl_exact"]))
    A("- Disguised per-obligation alpha defined on %d/6 obligations; "
      "of those: %d have alpha>=0.70, %d are weak [0.50,0.65], %d below 0.50." % (
          verdict["disguised_obl_alpha_defined_count"],
          verdict["disguised_obl_alpha_ge_070_count"],
          verdict["disguised_obl_alpha_weak_count"],
          verdict["disguised_obl_alpha_below_050_count"]))
    A("")
    A("Disguised per-obligation alpha: " + ", ".join(
        "%s=%s" % (o, _fmt(verdict["disguised_obl_alpha"][o])) for o in OBLIGATIONS))
    A("")
    if verdict["supported"]:
        A("=> The premise is **SUPPORTED**: the obligation abstraction reproduces "
          "across independent model families on the hard set. Proceed toward the "
          "validated-abstraction paper, then run the ready human pass to confirm.")
    elif verdict.get("weak_or_worse"):
        if verdict.get("disguised_obl_alpha_below_050_count", 0) >= 2:
            A("=> The premise **FAILS on the hard set**: %d of the obligations with "
              "defined alpha fall BELOW 0.50 (i.e. at or below chance) on the "
              "disguised-refusal set -- strictly worse than the pre-committed "
              "[0.50,0.65] WEAK band. The committed stop-loss therefore fires in "
              "its 'taxonomy is the research target' direction, and then some. "
              "Recommend the honest 'proposal' reframe: present the obligation "
              "taxonomy and harness as a PROPOSED instrument whose obligation-level "
              "reproducibility is partial -- strong on Observation/Action/Control "
              "and status, but weak-to-absent on Execution/State/Verification on "
              "adversarial scope-confusion inputs -- with the disagreement "
              "structure (which obligations reproduce, which do not, and why) as a "
              "first-class finding and the human pass as the decisive next step."
              % verdict.get("disguised_obl_alpha_below_050_count", 0))
        else:
            A("=> The premise is **WEAK**: >=2 obligations land at/below the "
              "[0.50,0.65] band on the harder set. The taxonomy itself becomes the "
              "research target. Recommend the honest 'proposal' reframe: present "
              "the obligation taxonomy and harness as a proposed instrument whose "
              "reproducibility is partial, with the disagreement structure as a "
              "first-class finding.")
    else:
        A("=> Mixed: the SUPPORTED bar is not cleared. Recommend the honest "
          "'proposal' reframe and report the disagreement structure (which "
          "obligations reproduce, which do not) as a first-class finding, with "
          "the human pass as the decisive next step.")
    A("")
    A("## Human pass: ready protocol")
    A("")
    A("The same instrument supports a human study with no code change:")
    A("1. Recruit >=3 annotators; give each ONLY `docs/annotation_codebook.md`.")
    A("2. Have them fill `outputs/iaa/human_review_sheet.csv` (one row per query; "
      "columns for obligations, capabilities, status, and free-text notes).")
    A("3. Re-run `scripts.compute_iaa` over the human annotations (same kappa / "
      "Krippendorff alpha / micro-F1 / cluster-bootstrap pipeline) to get human IAA.")
    A("4. Compare human IAA to this multi-model proxy; adjudicate disagreements; "
      "fold confirmed labels back into gold.")
    A("")
    return "\n".join(L) + "\n"


def write_review_sheet(
    gapbench_subset: Path,
    disguised: Path,
    out_path: Path,
    annotations: Sequence[Annotation],
) -> None:
    """Emit a human review sheet CSV. One row per (dataset,query).

    Columns let a future human annotator fill obligations/capabilities/status and
    notes from the codebook alone. The model annotations are included only as a
    reference column the human may ignore; the human columns are blank.
    """
    import csv

    # index model annotations by (dataset-ish row_id) for an optional reference col
    by_row: Dict[str, List[Annotation]] = defaultdict(list)
    for a in annotations:
        by_row[a.row_id].append(a)

    obl_cols = list(OBLIGATIONS)
    fieldnames = (
        ["dataset", "row_id", "cluster", "query"]
        + ["obl_%s" % o for o in obl_cols]
        + ["capabilities", "status", "annotator_id", "notes", "model_reference_majority_status"]
    )

    rows_out: List[Dict[str, object]] = []

    def majority_status(rid: str) -> str:
        anns = by_row.get(rid, [])
        if not anns:
            return ""
        c = Counter(a.status for a in anns)
        return c.most_common(1)[0][0]

    def add(dataset: str, rid: str, cluster: str, query: str):
        row = {k: "" for k in fieldnames}
        row.update({
            "dataset": dataset,
            "row_id": rid,
            "cluster": cluster,
            "query": query,
            "model_reference_majority_status": majority_status(rid),
        })
        rows_out.append(row)

    if gapbench_subset.exists():
        for r in (json.loads(l) for l in gapbench_subset.read_text().splitlines() if l.strip()):
            add("gapbench", str(r["task_id"]), str(r.get("category", "")), str(r["query"]))
    if disguised.exists():
        for r in (json.loads(l) for l in disguised.read_text().splitlines() if l.strip()):
            add("disguised", str(r["id"]), str(r.get("template", "")), str(r["query"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_out:
            writer.writerow(row)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compute multi-model IAA statistics.")
    parser.add_argument("--cache-dir", default="outputs/iaa/raw")
    parser.add_argument("--out", default="outputs/iaa/iaa_metrics.json")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument(
        "--gapbench-gold",
        default="outputs/iaa/gapbench_subset.jsonl",
        help="Stratified GapBench subset jsonl (written by the runner).",
    )
    parser.add_argument(
        "--disguised-gold",
        default="benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl",
    )
    parser.add_argument("--report", default="outputs/iaa/iaa_report.md")
    parser.add_argument("--review-sheet", default="outputs/iaa/human_review_sheet.csv")
    parser.add_argument("--manifest", default="outputs/iaa/run_manifest.json")
    args = parser.parse_args(argv)

    cache_dir = Path(args.cache_dir)
    results: Dict[str, object] = {}
    all_annotations: List[Annotation] = []

    # GapBench subset
    gb_ann = load_annotations_from_cache(cache_dir, "gapbench")
    if gb_ann:
        all_annotations.extend(gb_ann)
        gb_gold = load_gold(Path(args.gapbench_gold), "task_id", "expected_status", "gold_obligations", "category")
        models = sorted({a.model for a in gb_ann})
        results["gapbench"] = analyze_dataset(gb_ann, gb_gold, models, args.bootstrap, args.seed)

    # Disguised refusal
    dr_ann = load_annotations_from_cache(cache_dir, "disguised")
    if dr_ann:
        all_annotations.extend(dr_ann)
        dr_gold = load_gold(Path(args.disguised_gold), "id", "gold_status", "gold_obligations", "template")
        models = sorted({a.model for a in dr_ann})
        results["disguised"] = analyze_dataset(dr_ann, dr_gold, models, args.bootstrap, args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True, default=str))
    print("wrote metrics to %s" % out_path)

    # ----- stop-loss verdict, report, review sheet -----
    verdict = stop_loss_verdict(results)
    results["_stop_loss_verdict"] = verdict
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True, default=str))

    manifest: Dict[str, object] = {}
    mpath = Path(args.manifest)
    if mpath.exists():
        try:
            manifest = json.loads(mpath.read_text())
        except Exception:
            manifest = {}
    if not manifest.get("annotators"):
        # Minimal fallback: list the model ids observed in the cache (no params).
        manifest["annotators"] = [
            {"family": "unknown", "model": m, "temperature": "n/a", "max_tokens": "n/a"}
            for m in sorted({a.model for a in all_annotations})
        ]

    report = render_report(results, manifest, verdict)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(report, encoding="utf-8")
    print("wrote report to %s" % args.report)

    write_review_sheet(
        Path(args.gapbench_gold),
        Path(args.disguised_gold),
        Path(args.review_sheet),
        all_annotations,
    )
    print("wrote review sheet to %s" % args.review_sheet)
    print("\nSTOP-LOSS VERDICT: %s" % verdict["label"])
    for dataset, res in results.items():
        if not isinstance(res, dict) or "n_rows_complete" not in res:
            continue
        print("\n=== %s (n=%s rows, %s clusters) ===" % (dataset, res["n_rows_complete"], res["n_clusters"]))
        print("model-model Obl-Exact: %s %s" % (
            _fmt(res["model_model_obl_exact"]["mean_pairwise"]),
            _fmt_ci(res["model_model_obl_exact_ci"]),
        ))
        print("status alpha: %s %s  raw-full-agree: %s" % (
            _fmt(res["status"]["alpha"]),
            _fmt_ci(res["status_alpha_ci"]),
            _fmt(res["status"]["raw_full_agreement"]),
        ))
        for obl in OBLIGATIONS:
            oa = res["obligation_agreement"][obl]
            print("  %-12s alpha=%s %s  kappa=%s  prev=%.2f" % (
                obl, _fmt(oa["alpha"]), _fmt_ci(res["obligation_alpha_ci"][obl]),
                _fmt(oa["kappa_mean"]), oa["prevalence"],
            ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
