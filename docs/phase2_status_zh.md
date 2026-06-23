# Phase 2 状态汇报：Paper-Ready Experiment + Manuscript Stage

更新时间：2026-06-22

## 结论

Phase 2 的第一段已经完成：现在不只是 demo，而是有冻结数据、可复现实验、baseline 对比、transfer smoke、Natural review package、图表和 technical report 草稿的最小可信 paper artifact。

目前可以进入下一段：LLM profiler dev/test sweep + manuscript tightening。

## 已完成

### 1. GapBench v1.0 冻结

位置：`benchmarks/gapbench/v1.0/`

内容：

- `gapbench_1000_human_audited.jsonl`：1000 条 human-audited gold。
- `gapbench_500_human_audited.jsonl`：500 条子集。
- `splits/dev200.jsonl`：开发集。
- `splits/test800.jsonl`：最终报告测试集。
- `manifest.json`、`schema.md`、`audit_log.md`：公开 artifact 需要的说明文件。

当前主结果：

- GapHarness gold：success 1.00，avg cost 3.67，regret 0.00。
- Direct：success 0.20。
- Tool Router：success 0.34，under-harness 0.60，wrong-harness 0.42。
- Always-full：success 0.94，但 avg cost 16.00，over-harness 0.94。

这已经支撑核心 claim：obligation-first compiler 可以把 insufficiency 和 over-harnessing 清楚分开。

### 2. GAIA-Transfer v1.0 冻结

位置：`benchmarks/gaia_transfer/v1.0/`

内容：

- `gaia_validation100_human_audited.jsonl`
- `gaia_test100_human_audited.jsonl`
- `gaia_transfer200_human_audited.jsonl`
- `manifest.json`、`schema.md`、`audit_log.md`

当前 smoke：

- GapHarness gold：200 条，success 1.00，avg cost 1.48，regret 0.00。

注意边界：这里证明的是 obligation-transfer / harness coverage，不是完整 GAIA answer accuracy。

### 3. GapBench-Natural-200 review package

位置：`benchmarks/gapbench_natural/v1.0/`

内容：

- `gapbench_natural_200_for_review.jsonl`
- `gapbench_natural_200_review_sheet.csv`
- `manifest.json`
- `README.md`

打包文件：

- `gapbench_natural_review_package.zip`

当前状态：

- labels 继承自已 audit 的 GapBench v1.0。
- visible user queries 还需要人工 review 后才能变成 final paper claim。
- 模板残留检查为 0。
- gold-compiler smoke：200 条，success 1.00，avg cost 2.83，regret 0.00。

### 4. Profiler variant infrastructure

已经实现：

- `llm_single`
- `llm_recall`
- `llm_minimality`
- `llm_cascade`

CLI 已支持：

- `gapharness compile --profiler ...`
- `gapharness run-benchmark --profiler ...`

当前状态：代码与测试已经通过；完整 dev/test LLM sweep 尚未跑，建议下一步在 API 调用预算内跑 dev200，然后只把最好的策略跑 test800。

### 5. Phase 2 表格和图

表格：

- `outputs/phase2/table1_gapbench1000_gold.md`
- `outputs/phase2/table2_transfer_and_review_smokes.md`
- `outputs/phase2/table3_category_breakdown.md`
- `outputs/phase2/failure_mode_summary.md`

图：

- `figures/phase2/pipeline.svg`
- `figures/phase2/cost_success_frontier.svg`
- `figures/phase2/over_under_wrong_bars.svg`
- `figures/phase2/regret_distribution.svg`
- `figures/phase2/drop_one_necessity.svg`

复现实验脚本：

- `scripts/run_phase2_gold_experiments.sh`

已验证该脚本能重建当前 deterministic gold artifacts。

## 已验证

命令：

```bash
bash scripts/run_phase2_gold_experiments.sh
python3 -m unittest discover -s tests
python3 -m py_compile scripts/freeze_phase2_datasets.py scripts/build_gapbench_natural.py scripts/clean_gapbench_natural_queries.py scripts/generate_phase2_artifacts.py
```

结果：

- GapBench-1000 all-baseline 输出 6000 行。
- GAIA-Transfer-200 输出 200 行。
- GapBench-Natural-200 输出 200 行。
- 单元测试 12/12 通过。
- secret scan 未发现已提供 API/HF token 写入仓库。

## 当前不能过度 claim 的地方

- 不能说已经达到完整 GAIA answer-level accuracy；现在是 obligation/harness coverage。
- Natural-200 还没有你最终人工确认，不能写成 final gold。
- LLM profiler variants 已实现，但 full dev/test sweep 还没完成。
- Action 仍是 sandbox/mock，不覆盖真实不可逆操作。

## 下一步建议

1. 你 review `gapbench_natural_review_package.zip`，确认 Natural-200 是否可以升为 human-audited gold。
2. 用剩余 API budget 跑 GapBench dev200 的 `llm_single`、`llm_recall`、`llm_minimality`，决定 test800 用哪个策略。
3. 若 dev200 结果足够好，再跑 test800 的最终 LLM profiler 表。
4. 把 `docs/technical_report_draft.md` 扩成正式 workshop/system report 初稿。
5. 再决定是否加 WildToolBench/Terminal-Bench，避免现在扩 benchmark 把论文主线拖散。
