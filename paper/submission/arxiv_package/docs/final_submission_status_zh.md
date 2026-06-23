# GapHarness Final Submission Status

更新时间：2026-06-23

## 1. 最终版主文件

- `paper/drafts/gapharness_manuscript_v2.md`：最终英文 technical report。
- `paper/drafts/gapharness_manuscript_v2.tex`：Pandoc 生成的 LaTeX。
- `paper/drafts/gapharness_manuscript_v2.pdf`：本地最终 PDF。
- `paper/submission/arxiv_package/gapharness_arxiv.pdf`：同步后的 submission PDF。
- `paper/submission/arxiv_package/gapharness_package_local.md`：package-local Markdown source，bibliography 和 figures 都使用 package 内相对路径；重新编译仍要求本机已有 Pandoc + TeX/Tectonic bundle。

## 2. 已采纳的 reviewer 修复

- 新增 LLM Tool Router baseline：dev200、test800、negative controls 都已跑完。
- 新增 secondary/adversarial audit：GapBench-100 stratified sample，明确不是 human inter-annotator agreement。
- 指标口径改正：正文和 revised tables 使用 `Harness Success`、`Cost Delta`、`Excess Cost`，不再把负 delta 称为 regret。
- Phase 2C 降级为 post-hoc registry-boundary calibration，不再写成 fresh held-out discovery。
- Figure 3 改为 grouped bars，并标注 over/under/wrong rates are not mutually exclusive。
- Figure 4 改为 paper-style compact chart，统一使用 harness-success 口径。
- 正文新增 formal problem formulation、Proposition 1/2/3 和 proof sketches。
- 标题和主 claim 已改为 certificate-carrying runtime harness compilation，避免把 registry selection 过度写成 code harness synthesis。
- Related Work 新增更强定位比较，补齐 weighted set cover / service composition / feature-model configuration / runtime verification / policy / MAPE-K / assurance cases。
- 新增 diagnostic-feedback upper-bound baselines：Workflow Generator、Verifier-Repair Router、ReAct-style Module Selector；明确比较的是共享 registry/executor/verifier 下的策略，不是 LangGraph/AutoGen 等框架本体。
- 新增 GapHarness-Repair / Verifier-Guided Recompile：把 verifier diagnostics 转成 profile patch 后重新走 exact compiler，因此反馈修复后仍保留 registry-relative certificate。
- 正文 claim 已收缩为 auditability / certifiability / feedback-dependence tradeoff，不再暗示 GapHarness 在 raw coverage 上无条件优于所有 iterative agent policies。
- 新增 mostly non-dominated registry scaling stress，说明当前快速 scaling 是 dominated-redundancy 场景，exact compilation 最坏情况仍是 exponential。
- Natural-200 已从 preliminary/for-review 转为 project-owner-audited。
- 新增 SWE-Obligation-50：从 public SWE-bench Lite 拉取 50 条真实 issue/task descriptions，做 obligation-transfer only，不声称 patch solving/pass@1。
- 新增 SWE-HarnessExec-50：把 provided-patch sandbox pytest trace 从 20 条扩到 50 条，增强 execution-level scale-up 证据；仍不声称真实 repo checkout、model repair 或 SWE-bench pass@1。
- 新增 Phase 6 reviewer evidence：certificate utility proxy、feedback-level replay、cost-scheme sensitivity/status confusion/profiler taxonomy、RealBoundary-100 fresh boundary holdout package。
- 新增 Naturalistic-Holdout v0.1：200 条 public GitHub issue-derived independent candidate review package，不来自 GapBench 模板；review sheet 字段和内容已由项目 owner 确认，但行级 `audit_status` 仍标为 candidate，等待双人独立标注、agreement metrics 和 adjudication 后才能成为 gold。

## 3. 新增实验结果

- LLM Tool Router dev200：N=200，Harness Success=0.79，Cost=3.35，Cost Delta=-0.27，Excess Cost=0.11。
- LLM Tool Router test800：N=800，Harness Success=0.80，Cost=3.51，Cost Delta=-0.18，Excess Cost=0.13。
- LLM Tool Router negative controls：N=200，Harness Success=1.00，Cost=0.00，Over=0.00。
- Secondary adversarial audit：N=100，Obligation micro-F1=0.878，Capability micro-F1=0.814，Status agreement=0.87，Harness exact agreement=0.75。
- GapBench-Natural-200 project-owner-audited：N=200，GapHarness gold Harness Success=1.00，Declared Cost=2.83，Cost Delta=0.00。
- SWE-Obligation-50 original project-owner-audited source view：N=50，GapHarness gold Harness Success=1.00，Declared Cost=12.00，Cost Delta=0.00；Direct/Tool Router 全部 under-covered；Always-full 成功但 over-harness。
- SWE-Obligation-50 LLM-safe diagnostic view：GapHarness LLM Harness Success=1.00，Declared Cost=12.80；LLM Tool Router Harness Success=1.00，Declared Cost=12.00。该视图是供 LLM 系统共享的 shortened diagnostic view，用于避开供应商内容过滤和长 issue 文本；不替代原始 gold source，也不作为独立标注依据。
- Diagnostic-feedback GapBench test800：Workflow Generator HS=0.77；Verifier-Repair Router HS=1.00、Cost=3.85、LLM Calls=1.20、无 certificate；ReAct Module Selector HS=1.00、Cost=3.90、LLM Calls=1.08、无 certificate；GapHarness-Repair HS=1.00、Cost=3.96、LLM Calls=1.00、平均 feedback/recompile steps=0.11、certificate=yes。
- Diagnostic-feedback HarnessChallenge-200：Workflow Generator HS=0.83；Verifier-Repair Router 和 ReAct Module Selector 均 HS=1.00，但依赖失败后的 verifier feedback，仍无 certificate；GapHarness-Repair HS=1.00、Cost=3.69、平均 feedback/recompile steps=0.30、certificate=yes。
- Diagnostic-feedback SWE-HarnessExec-20：Workflow Generator、Verifier-Repair Router、ReAct Module Selector、GapHarness-Repair 均 Coverage HS=1.00、Trace Success=1.00、Cost=12.00，说明同质 execution-heavy fixtures 上强策略也能匹配。
- Feedback-level replay：把 feedback 分成 weak pass/fail、medium missing obligation、strong missing capability/status；strong 是上界，weak 下 router/ReAct 可通过宽 harness 达到高覆盖但 excess cost/over-harness 明显升高。
- Certificate utility proxy：GapBench test800 上 GapHarness LLM debug-work proxy=2.45，GapHarness-Repair=2.40，对比 LLM Tool Router=4.13、Workflow Generator=4.15；这是 deterministic proxy + audit packet，不是已完成 human timing。
- Cost calibration：已加入 declared/uniform/latency_proxy/risk_weighted/token_api_proxy sensitivity，明确 cost 是 proxy 不是真实 provider billing。
- Status confusion / profiler taxonomy：明确 registry guard 在 GapBench 支持项 false unsupported 上有帮助，但在 HarnessChallenge unsupported boundary 上会伤害；主要错误类包括 false unsupported、dependency missed、unsupported false positive、multi-obligation miss、verification/control confusion。
- RealBoundary-100：fresh author-seeded holdout，不用于调 guard；GapHarness author-seeded / Oracle minimal HS=1.00，Direct/Tool/Difficulty/Always-full 暴露边界错误；仍待独立人工 audit。
- Naturalistic-Holdout v0.1：N=200 candidate rows；来源为 public GitHub issues，agent_development=170、developer_tooling=30；当前不跑分、不声称 human-audited gold。
- SWE-HarnessExec-50 deterministic scale-up：N=50；GapHarness gold / Oracle minimal Coverage HS=1.00、Trace Success=1.00、Cost=12.00；Always-full Trace Success=1.00 但 Cost=16.00；Direct / Tool Router / Difficulty Router 均因缺少 required modules 而在 trace 前停止。
- Mostly non-dominated scaling stress：20/30/40 module registries 中 dominated=0；optimized exact search 从 36.70ms 增至 3297.16ms，明确展示 harder registry 下 exact search 边界。

## 4. 主论文证据边界

- GapBench-1000 gold compiler：GapHarness 在 audited gold obligations 下匹配 oracle minimal harness。
- LLM profiler held-out test800：GapHarness LLM 为 0.89 harness success，高于 LLM Tool Router 的 0.80。
- Registry guard：unsupported false positives 从 56 降到 12，harness success 从 0.89 到 0.94，但这是 post-hoc calibration。
- Abstract 和正文已把 registry guard 降级为 post-hoc calibration，不把 0.94 当核心主 claim。
- Stress tests：registry perturbation、gold label permutation、negative controls 均已纳入正文。
- GAIA-Transfer 是 boundary diagnostic，不是 full GAIA answer solving。
- SWE-Obligation-50 是 real-source boundary diagnostic，不是 SWE-bench solving/pass@1。
- SWE-HarnessExec-50 是 provided-patch sandbox trace scale-up，不是真实 SWE-bench repo checkout、open-ended repair 或 pass@1。
- Terminal-Bench-obligation50 是 appendix scaffold，不是 Terminal-Bench solving。
- RealBoundary-100 是 fresh boundary diagnostic，但目前 author-seeded/review-pending，不是最终独立 human-audited external benchmark。
- Naturalistic-Holdout v0.1 是独立 naturalistic candidate package，但还不是 gold benchmark；必须完成 annotator_a / annotator_b、Cohen kappa 或 Krippendorff alpha、disagreement adjudication 后再报告正式结果。
- Certificate utility 表是 deterministic proxy + prepared human audit packet，不是已完成 audit-time human study。
- Feedback-level replay 是 deterministic replay，不是新 LLM 调用结果。
- Diagnostic-feedback baselines 是 harness-selection policy baselines，不是“GapHarness > LangGraph/AutoGen/Agents SDK”的框架级声明。
- Verifier-Repair 和 ReAct-style baselines 在失败后收到 verifier feedback；高覆盖率不能解释为 one-shot minimality certificate。
- GapHarness-Repair 是 feedback-assisted upper-bound variant，不是 one-shot LLM profiler 本身；它的价值是反馈后仍通过 compiler 产出 certificate。

## 5. PDF 状态

- 最终 PDF：20 页，letter 单栏。
- 已使用 bundled Poppler 渲染关键页面；新增 SWE-HarnessExec-50 表页已人工截图检查。
- 已抽查首页、主表页、强 baseline 表页、Phase 6 新表页、SWE trace 表页、appendix/related-work 表页、参考文献页，无明显裁切、重叠或不可读表格。
- LaTeX 编译仅剩 underfull hbox warnings，未发现 overfull table/figure 错误。

## 6. 测试和安全状态

已运行：

```bash
PYTHONPATH=. pytest -q
python3 -m py_compile gapharness/*.py scripts/*.py
pandoc paper/drafts/gapharness_manuscript_v2.md --citeproc -s --pdf-engine=tectonic -o paper/drafts/gapharness_manuscript_v2.pdf
shasum -a 256 -c outputs/final/checksums.sha256
```

结果：`pytest -q` 为 21 passed；`py_compile` 通过；checksum 覆盖 2646 个 artifact 并校验通过；密钥扫描只命中环境变量名/占位符，未发现真实 API key 或 HF token 写入 `paper/`、`outputs/`、`docs/`、`gapharness/`、`scripts/`、`tests/` 或 `README.md`。

## 7. 最终提交前人工动作

1. 决定作者列表、单位、acknowledgement 和匿名/非匿名版本。
2. 若投具体 workshop，再按模板改页边距、双栏、匿名规则和引用样式。
3. 若投 arXiv，确认是否只提交 PDF，或进一步整理 source bundle。
4. 人工通读 v2 PDF，重点看 abstract、claim boundaries、formal section、Table 2、stress tests 和 limitations。
