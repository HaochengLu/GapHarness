# Paper Claims and Boundaries (v3)

This file tracks the evidence-backed claim set for manuscript v3
(`paper/drafts/gapharness_manuscript_v3.md`). The contribution is the
**certificate-as-contract** framing plus an **honest, measured reliability study**
of the obligation instrument. We make no algorithmic claim and no raw-coverage
dominance claim.

## Strong Claims Supported by Current Evidence

1. **Decidable pre-execution typing + certificate.** GapHarness separates "which
   obligations a request imposes" from "which declared affordances satisfy them,"
   compiling the lowest declared-cost valid registry subset or a certificate-carrying
   refusal that names the missing affordance. The output is a witness a third party can
   verify in linear time without trusting the compiler or the LLM.
2. **Compiler correctness is by construction, not by a self-generated oracle.**
   Registry-relative minimality holds by construction (Prop 1). It is corroborated by
   an independently implemented exact min-cost solver (`gapharness/independent_oracle.py`)
   that imports no compiler internals and agrees on 1,390/1,390 supported rows (cost and
   module set), zero mismatches, across 6 benchmark files.
3. **Honest equivalence replay.** Across the 4,020 rows where the compiler was genuinely
   re-invoked, the optimized branch-and-bound + dominance-pruned compiler produces zero
   status/module/cost changes; a separate dominance track removes 24 dominated modules with
   zero brute-force mismatches. (The previously inflated 14,320 count — 10,100
   reconstructed-baseline + 200 router-skipped rows — is excluded.)
4. **Fail-closed safety boundary that does not invert.** A scope-aware side-effect
   classifier replaces a guard that wrongly mapped "deploy to production from the repo and
   send a real email to customers" to supported; that canonical case now returns
   unsupported, the 32-row (16-pair) adversarial minimal-pair set all classifies correctly,
   bare repo/workspace/file tokens no longer downgrade a real action, and the sandbox twin
   stays supported.
5. **Reliability finding (headline): the status decision and coarse obligations reproduce
   across independent model families; the fine obligations do not on adversarial inputs.**
   Using three independent model families (gpt-5.5, claude-opus-4-1-20250805, gemini-2.5-pro)
   annotating from a shared neutral codebook (549 cached annotations):
   - Status (supported/unsupported/clarify): Krippendorff alpha 0.913 on the controlled
     GapBench-120 subset and 0.787 on the adversarial disguised-refusal-63 set.
   - Coarse obligations (Observation, Action, Control) reproduce on both controlled and
     adversarial inputs (Observation alpha 0.866 controlled, 1.000 adversarial; Action/Control
     unanimous on the adversarial set).
   - Fine obligations (Execution, State, Verification) reproduce on controlled inputs
     (alpha 0.747/0.796/0.833) but NOT on adversarial inputs (alpha 0.270 / -0.015 / -0.107).
   - Model-model Obl-Exact: 0.647 controlled, 0.317 adversarial (vs prior single-LLM 0.65).
   The disagreement structure is a first-class finding. This is MULTI-MODEL agreement (a
   proxy for and precursor to human IAA), not a human IAA study; the human pass (protocol,
   codebook, and `outputs/iaa/human_review_sheet.csv`) is scaffolded and is the decisive
   next step.
6. **Certificate is the differentiator, not coverage.** With the rigged certificate-utility
   proxy removed, under MEDIUM non-leaky feedback iterative-repair baselines reach equal
   coverage without a certificate (GapBench 0.93 vs 0.91; HarnessChallenge 0.79 vs 0.79).
   Baselines reach ~1.00 only under weak feedback by over-provisioning (excess 2.18 GapBench /
   3.08 HarnessChallenge) or under strong feedback by consulting privileged gold status/
   capabilities (oracle-status accesses 0.20/0.35 per task = an oracle-leakage upper bound).
   GapHarness-Repair attains the same coverage while emitting a checkable witness and without
   consuming privileged resources; on the hard split it pays more excess (0.98 vs 0.04) for
   that parity.
7. **Registry perturbation and label permutation are anti-circularity checks.** Removing a key
   module degrades to a refusal naming the missing affordance (relevant-subset HS 1.00 -> 0.00);
   permuting gold labels collapses verifier success (1.00 -> 0.17), confirming obligation labels
   are semantically consequential, not decorative.
8. **Negative controls hold.** GapHarness variants and the LLM Tool Router avoid tool-bait
   over-harnessing; heuristic routers over-harness tool-bait at 0.51.

## Secondary Claims (reported, not headline)

1. **Held-out coverage.** On test800, GapHarness LLM reaches 0.89 harness success vs 0.80 for
   the LLM Tool Router. These coverage numbers are secondary to the reliability finding.
2. **The post-hoc scope-classifier 0.94 is de-emphasized.** It was shaped on the same
   distribution and the dev/test split is template-leaky; it is reported as a post-hoc,
   template-leaky figure, not a clean held-out result.
3. **Executable traces.** GapHarness gold/oracle reach 1.00 coverage and trace success on
   SWE-HarnessExec-20/50 at declared cost 12.00; on these homogeneous fixtures, routers and
   agentic strategies also reach 1.00, so they are a boundary result, not a differentiator.
4. **Over-harness over-rate is 0.14/0.15** (raw 0.145/0.152) for GapHarness LLM / scope-classifier
   GH, corrected from the earlier 0.16/0.17.

## Claims Not Supported

1. GapHarness solves full GAIA, Terminal-Bench, or SWE-bench (no pass@1, no patch generation).
2. GapHarness handles arbitrary real API side effects (executor is sandbox/mock only).
3. **The obligation taxonomy is independently human-audited gold.** It is NOT. GapBench labels
   are single-annotator (system designer). Reproducibility is partial and measured: the fine
   obligations (Execution/State/Verification) are not reproducible across independent annotators
   on adversarial scope-confusion inputs (this moved from "Strong Claims" to "Not Supported").
4. **GapHarness wins on raw coverage.** It does not. Coverage is at parity under non-leaky
   feedback; the certificate is the differentiator.
5. **The optimizer is novel.** It is textbook weighted set cover + monotone dependency closure;
   no algorithmic claim is made.
6. **The system is free of lexical aids / "is not keyword routing."** The LLM profile is passed
   through a deterministic `canonicalize_profile` normalizer with explicit lexical triggers; the
   no-lexical ablation is future work, so coverage reflects a model-plus-normalizer pipeline.
7. The LLM profiler is fully calibrated; GapBench is a complete real-world benchmark; GapHarness
   is categorically better than LangGraph/AutoGen/any agent framework as a substrate.

## Required Boundary Statements

- Minimality is relative to a declared obligation ontology, module registry (9 modules — a toy
  scale), dependency model, and cost function.
- Harness success is obligation/capability coverage, not answer-level correctness.
- Cost delta can be negative; excess cost is the per-task positive excess, not max of aggregate
  mean delta.
- Krippendorff's alpha is implemented from the coincidence matrix and unit-tested against the
  canonical 0.743 example; IAA confidence intervals are cluster-bootstrap by template (8-9
  clusters), high-variance and indicative of between-template spread, not tight standard errors.
- An alpha of "n/a" with prevalence near 1.00 means unanimous inclusion (no variation to
  disagree about), not missing data.
- The IAA study is multi-model agreement, a proxy for human IAA; the human pass is scaffolded but
  not yet run.
- The independent-oracle cross-check is an implementation unit test, not an empirical performance
  result; correctness is by construction (Prop 1).
- The fail-closed scope-classifier minimal-pair set is small (16 pairs) and partly author-shaped;
  the IAA status alpha (0.79 on the disguised set) is the independent check that the direction of
  these judgments reproduces.
- "Strong feedback" in the feedback-cost analysis leaks gold status/capabilities and is reported
  as an oracle-leakage upper bound, not a fair operating point; "medium" non-leaky feedback is the
  fair operating point.
- The executor is a deterministic sandbox/mock runtime; SWE-HarnessExec uses provided patches and
  generated fixtures, not real-repository checkout or model-generated repair.
- GAIA-Transfer, GapBench-Natural, SWE-Obligation-50, and Terminal-Bench-obligation50 are
  external-validity / boundary diagnostics only; they make no solving or pass@1 claim.
- Honest venue ceiling: a strong workshop or borderline benchmark-track artifact, contingent on
  the human reliability pass and (optionally) a live side-effect-logging executor experiment.
