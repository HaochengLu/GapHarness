"""Unit tests for the multi-model IAA statistics (plan milestone M3).

The most important test is ``test_krippendorff_canonical_example``: it pins our
from-scratch nominal Krippendorff's alpha against a published, hand-verifiable
value (Krippendorff's own canonical reliability-data example, nominal metric,
alpha = 0.743). If this drifts, every alpha in the IAA report is suspect.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.compute_iaa import (
    CAPABILITY_VOCAB,
    OBLIGATIONS,
    STATUSES,
    Annotation,
    cohens_kappa_binary,
    cluster_bootstrap_ci,
    exact_set_match,
    krippendorff_alpha_nominal,
    micro_f1,
    model_model_obl_exact,
    parse_annotation,
    per_obligation_agreement,
    status_agreement,
)


class KrippendorffTests(unittest.TestCase):
    def test_krippendorff_canonical_example(self):
        """Canonical nominal example from Krippendorff's textbook -> alpha = 0.743.

        Reliability data (4 coders x 12 units; '.' = missing):
          A: 1 2 3 3 2 1 4 1 2 . . .
          B: 1 2 3 3 2 2 4 1 2 5 . 3
          C: . 3 3 3 2 3 4 2 2 5 1 .
          D: 1 2 3 3 2 4 4 1 2 5 1 .
        The accepted nominal alpha is 0.743 (e.g. the `krippendorff` package and
        Krippendorff 2004, *Content Analysis*). We require 3-decimal agreement.
        """
        A = [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None]
        B = [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3]
        C = [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None]
        D = [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None]
        units = list(zip(A, B, C, D))
        alpha = krippendorff_alpha_nominal(units)
        self.assertIsNotNone(alpha)
        self.assertAlmostEqual(alpha, 0.743, places=3)

    def test_krippendorff_perfect_agreement_with_variation(self):
        units = [[0, 0], [1, 1], [1, 1], [0, 0], [1, 1]]
        self.assertEqual(krippendorff_alpha_nominal(units), 1.0)

    def test_krippendorff_maximal_disagreement_is_negative(self):
        units = [[0, 1], [1, 0], [0, 1], [1, 0]]
        alpha = krippendorff_alpha_nominal(units)
        self.assertIsNotNone(alpha)
        self.assertLess(alpha, 0.0)

    def test_krippendorff_no_variation_is_undefined(self):
        # Every present value identical -> expected disagreement is 0 -> undefined.
        units = [[1, 1], [1, 1], [1, 1]]
        self.assertIsNone(krippendorff_alpha_nominal(units))

    def test_krippendorff_drops_units_with_one_value(self):
        # Units with a single present value contribute nothing; result is driven
        # by the pairable units only.
        units = [[1, None], [0, 0], [1, 1], [0, 0], [1, 1]]
        alpha = krippendorff_alpha_nominal(units)
        self.assertEqual(alpha, 1.0)

    def test_krippendorff_three_category_nominal(self):
        # 3 categories, 3 raters; mostly-agreeing data should be high but < 1.
        units = [
            ["supported", "supported", "supported"],
            ["unsupported", "unsupported", "unsupported"],
            ["clarify", "clarify", "supported"],
            ["supported", "supported", "supported"],
            ["unsupported", "unsupported", "clarify"],
        ]
        alpha = krippendorff_alpha_nominal(units)
        self.assertIsNotNone(alpha)
        self.assertGreater(alpha, 0.5)
        self.assertLess(alpha, 1.0)


class CohenKappaTests(unittest.TestCase):
    def test_perfect_agreement(self):
        self.assertEqual(cohens_kappa_binary([0, 1, 1, 0, 1], [0, 1, 1, 0, 1]), 1.0)

    def test_chance_disagreement(self):
        self.assertEqual(cohens_kappa_binary([0, 1, 0, 1], [1, 0, 1, 0]), -1.0)

    def test_known_value(self):
        # Constructed 2x2: a=[1,1,1,1,0,0,0,0,0,0], b=[1,1,0,0,0,0,0,0,1,1]
        # agree on 6/10 -> p_o=0.6; pa1=0.4, pb1=0.4 -> p_e=0.4*0.4+0.6*0.6=0.52
        # kappa = (0.6-0.52)/(1-0.52) = 0.08/0.48 = 0.1667
        a = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
        b = [1, 1, 0, 0, 0, 0, 0, 0, 1, 1]
        self.assertAlmostEqual(cohens_kappa_binary(a, b), 0.08 / 0.48, places=4)

    def test_no_variation_is_undefined(self):
        self.assertIsNone(cohens_kappa_binary([1, 1, 1], [1, 1, 1]))


class MicroF1Tests(unittest.TestCase):
    def test_identical_sets(self):
        self.assertEqual(micro_f1([frozenset(["a", "b"])], [frozenset(["a", "b"])]), 1.0)

    def test_half_overlap(self):
        # pred={a,b} gold={a,c}: tp=1, fp=1, fn=1 -> P=R=0.5 -> F1=0.5
        self.assertEqual(micro_f1([frozenset(["a", "b"])], [frozenset(["a", "c"])]), 0.5)

    def test_empty_vs_empty_is_one(self):
        self.assertEqual(micro_f1([frozenset()], [frozenset()]), 1.0)

    def test_disjoint_is_zero(self):
        self.assertEqual(micro_f1([frozenset(["a"])], [frozenset(["b"])]), 0.0)

    def test_pooled_across_rows(self):
        # row1 perfect, row2 disjoint -> tp=1, fp=1, fn=1 -> 0.5
        preds = [frozenset(["a"]), frozenset(["b"])]
        golds = [frozenset(["a"]), frozenset(["c"])]
        self.assertEqual(micro_f1(preds, golds), 0.5)


class ClusterBootstrapTests(unittest.TestCase):
    def test_ci_brackets_point_and_is_deterministic(self):
        # 4 clusters, each a constant; statistic = mean over picked rows.
        clusters = {"c1": ["r1", "r2"], "c2": ["r3"], "c3": ["r4", "r5"], "c4": ["r6"]}
        values = {"r1": 1.0, "r2": 1.0, "r3": 0.0, "r4": 1.0, "r5": 0.0, "r6": 0.0}

        def stat(row_ids):
            vals = [values[r] for r in row_ids]
            return sum(vals) / len(vals) if vals else None

        ci1 = cluster_bootstrap_ci(clusters, stat, n_samples=500, seed=7)
        ci2 = cluster_bootstrap_ci(clusters, stat, n_samples=500, seed=7)
        self.assertEqual(ci1, ci2)  # determinism
        lo, hi = ci1
        self.assertIsNotNone(lo)
        self.assertLessEqual(lo, hi)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)

    def test_empty_clusters_return_none(self):
        self.assertEqual(cluster_bootstrap_ci({}, lambda ids: 1.0), (None, None))


class ParseAndAggregateTests(unittest.TestCase):
    def test_parse_filters_to_vocabulary(self):
        obl, cap, status, ok = parse_annotation(
            {
                "obligations": ["Action", "Control", "NotAReal", "Observation"],
                "capabilities": ["permission", "bogus", "real_world_side_effect"],
                "status": "unsupported",
            }
        )
        self.assertEqual(obl, frozenset(["Action", "Control", "Observation"]))
        self.assertEqual(cap, frozenset(["permission", "real_world_side_effect"]))
        self.assertEqual(status, "unsupported")
        self.assertTrue(ok)

    def test_parse_bad_status_flagged(self):
        _, _, status, ok = parse_annotation({"obligations": [], "capabilities": [], "status": "maybe"})
        self.assertFalse(ok)
        self.assertEqual(status, "supported")

    def test_exact_set_match(self):
        self.assertEqual(exact_set_match(frozenset(["A", "B"]), frozenset(["B", "A"])), 1)
        self.assertEqual(exact_set_match(frozenset(["A"]), frozenset(["A", "B"])), 0)

    def test_status_agreement_full_and_alpha(self):
        models = ["m1", "m2", "m3"]
        anns = []
        # 4 rows of full agreement (with variation), 1 row of disagreement
        data = [
            ("r1", ["supported", "supported", "supported"]),
            ("r2", ["unsupported", "unsupported", "unsupported"]),
            ("r3", ["clarify", "clarify", "clarify"]),
            ("r4", ["supported", "supported", "supported"]),
            ("r5", ["unsupported", "clarify", "unsupported"]),
        ]
        for rid, statuses in data:
            for m, s in zip(models, statuses):
                anns.append(Annotation(m, rid, "c", frozenset(), frozenset(), s))
        from scripts.compute_iaa import _by_row

        by_row = _by_row(anns)
        agg = status_agreement(by_row, models)
        self.assertEqual(agg["n"], 5)
        self.assertAlmostEqual(agg["raw_full_agreement"], 4 / 5)
        self.assertIsNotNone(agg["alpha"])

    def test_per_obligation_agreement_perfect(self):
        models = ["m1", "m2", "m3"]
        anns = []
        # Action present on r1,r2; absent on r3,r4 -- all annotators agree.
        present = {"r1": True, "r2": True, "r3": False, "r4": False}
        for rid, has in present.items():
            obl = frozenset(["Action"]) if has else frozenset()
            for m in models:
                anns.append(Annotation(m, rid, "c", obl, frozenset(), "supported"))
        from scripts.compute_iaa import _by_row

        by_row = _by_row(anns)
        res = per_obligation_agreement(by_row, models)
        self.assertEqual(res["Action"]["alpha"], 1.0)
        self.assertEqual(res["Action"]["kappa_mean"], 1.0)

    def test_model_model_obl_exact(self):
        models = ["m1", "m2"]
        anns = [
            Annotation("m1", "r1", "c", frozenset(["Action", "Control"]), frozenset(), "unsupported"),
            Annotation("m2", "r1", "c", frozenset(["Action", "Control"]), frozenset(), "unsupported"),
            Annotation("m1", "r2", "c", frozenset(["Observation"]), frozenset(), "supported"),
            Annotation("m2", "r2", "c", frozenset(["Observation", "Verification"]), frozenset(), "supported"),
        ]
        from scripts.compute_iaa import _by_row

        by_row = _by_row(anns)
        res = model_model_obl_exact(by_row, models)
        self.assertAlmostEqual(res["mean_pairwise"], 0.5)  # r1 matches, r2 does not


class VocabularyConsistencyTests(unittest.TestCase):
    def test_obligations_match_schema(self):
        from gapharness.schema import OBLIGATIONS as SCHEMA_OBL, SUPPORTED_STATUSES

        self.assertEqual(set(OBLIGATIONS), set(SCHEMA_OBL))
        self.assertEqual(set(STATUSES), set(SUPPORTED_STATUSES))

    def test_capability_vocab_nonempty(self):
        self.assertIn("real_world_side_effect", CAPABILITY_VOCAB)
        self.assertEqual(len(set(CAPABILITY_VOCAB)), len(CAPABILITY_VOCAB))


class StopLossVerdictTests(unittest.TestCase):
    """The pre-committed stop-loss rule must apply correctly to numbers."""

    def _mk(self, disg_alphas, disg_obl_exact, disg_ci_low, gb_obl_exact=0.7):
        # Build a minimal results dict shaped like analyze_dataset output.
        def res(alphas, obl_exact, ci_low):
            return {
                "obligation_agreement": {o: {"alpha": alphas.get(o)} for o in OBLIGATIONS},
                "model_model_obl_exact": {"mean_pairwise": obl_exact},
                "model_model_obl_exact_ci": (ci_low, 1.0),
            }
        return {
            "disguised": res(disg_alphas, disg_obl_exact, disg_ci_low),
            "gapbench": res({o: 0.8 for o in OBLIGATIONS}, gb_obl_exact, 0.6),
        }

    def test_supported_when_all_high_and_obl_exact_clears(self):
        from scripts.compute_iaa import stop_loss_verdict

        alphas = {o: 0.85 for o in OBLIGATIONS}
        v = stop_loss_verdict(self._mk(alphas, disg_obl_exact=0.80, disg_ci_low=0.70))
        self.assertTrue(v["supported"])
        self.assertIn("SUPPORTED", v["label"])

    def test_fails_hard_when_two_obligations_below_050(self):
        from scripts.compute_iaa import stop_loss_verdict

        alphas = {"Observation": 1.0, "Execution": 0.27, "State": -0.02,
                  "Verification": -0.1, "Action": None, "Control": None}
        v = stop_loss_verdict(self._mk(alphas, disg_obl_exact=0.32, disg_ci_low=0.27))
        self.assertFalse(v["supported"])
        self.assertTrue(v["weak_or_worse"])
        self.assertGreaterEqual(v["disguised_obl_alpha_below_050_count"], 2)
        self.assertIn("FAILS", v["label"])

    def test_weak_when_two_in_band(self):
        from scripts.compute_iaa import stop_loss_verdict

        alphas = {"Observation": 0.9, "Execution": 0.60, "State": 0.55,
                  "Verification": 0.8, "Action": 0.9, "Control": 0.9}
        v = stop_loss_verdict(self._mk(alphas, disg_obl_exact=0.6, disg_ci_low=0.5))
        self.assertFalse(v["supported"])
        self.assertTrue(v["weak"])
        self.assertIn("WEAK", v["label"])

    def test_not_supported_when_obl_exact_does_not_clear(self):
        from scripts.compute_iaa import stop_loss_verdict

        # all alphas high, but Obl-Exact CI lower bound below 0.65 -> not supported
        alphas = {o: 0.85 for o in OBLIGATIONS}
        v = stop_loss_verdict(self._mk(alphas, disg_obl_exact=0.66, disg_ci_low=0.55))
        self.assertFalse(v["supported"])


class DisguisedRefusalBenchmarkTests(unittest.TestCase):
    """The authored disguised-refusal set must be well-typed and large enough."""

    @classmethod
    def setUpClass(cls):
        path = Path("benchmarks/disguised_refusal/v0.1/disguised_refusal.jsonl")
        cls.rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    def test_at_least_sixty_rows(self):
        self.assertGreaterEqual(len(self.rows), 60)

    def test_ids_unique(self):
        ids = [r["id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fields_and_vocab(self):
        for r in self.rows:
            self.assertIn(r["gold_status"], ("unsupported", "clarify"))
            for o in r["gold_obligations"]:
                self.assertIn(o, OBLIGATIONS)
            self.assertTrue(r["query"].strip())
            self.assertTrue(r["gold_note"].strip())
            self.assertTrue(r["template"].strip())

    def test_has_both_unsupported_and_clarify(self):
        statuses = {r["gold_status"] for r in self.rows}
        self.assertIn("unsupported", statuses)
        self.assertIn("clarify", statuses)

    def test_multiple_templates_for_clustering(self):
        self.assertGreaterEqual(len({r["template"] for r in self.rows}), 5)


if __name__ == "__main__":
    unittest.main()
