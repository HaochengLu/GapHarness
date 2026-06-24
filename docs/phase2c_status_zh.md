# Phase 2C 状态报告：Registry-Guarded Profiler Calibration

## 目标与边界

Phase 2C 是 Phase 2B 之后的独立校准实验，不覆盖 Phase 2B 结果。核心问题是：`llm_single` 在 Phase 2B 中有系统性错误，会把 sandbox/mock/local action 降格成 `real_world_side_effect`，导致本来可支持的任务被 compiler 判成 `unsupported`。

本阶段实现的新 profiler 是 `llm_registry_guarded`：先复用 `llm_single` 的 profile，再用 deterministic registry guard 修正 sandbox/mock/local 与真实外部副作用的边界。GapBench dev/test 默认复用 Phase 2B 冻结 cache，没有重新调用 API；GAIA-Transfer 因没有 Phase 2B LLM cache，实际调用 API 批处理约 40 次（含一次修正规则后的重跑），低于 1000 次上限。

## 已实现内容

- 新增 `llm_registry_guarded` profiler variant。
- 新增 guard metadata：`guard_applied`、`guard_actions`、`guard_reason`、raw/guarded obligations、raw/guarded capabilities、raw/guarded status。
- 新增 Phase 2C dev200 / test800 / GAIA-Transfer runner。
- 追加 Phase 2B frozen checkpoint 记录，明确 `outputs/phase2b/` 为冻结 artifact。
- 生成 Terminal-Bench-obligation50 scaffold，来源为 public Terminal-Bench task instructions，labels 仍为待人工审核。
- 运行 Terminal-Bench-obligation50 sandbox smoke（20 cases），本地 sandbox-only，无网络、无生产路径、无真实外部副作用。

## Dev200 结果

`llm_registry_guarded` 通过 Phase 2B selection rule：

- success: 0.970
- avg cost: 4.015
- regret: 0.395
- over-harness: 0.200
- under-harness: 0.030
- wrong-harness: 0.000
- unsupported false positives: 4

对比 Phase 2B dev200 `llm_single`：

- `llm_single`: success 0.920, under 0.080, unsupported FP 14
- `llm_registry_guarded`: success 0.970, under 0.030, unsupported FP 4

Guard correction:

- guard applied: 16 / 200
- removed sandbox false `real_world_side_effect`: 10
- converted unsupported to supported: 10
- preserved ambiguous clarification: 6

## Held-out Test800 结果

因为 dev200 通过规则，已运行 held-out test800。该结果是 Phase 2C calibration experiment，不替换 Phase 2B selected-profiler table。

`llm_registry_guarded`:

- success: 0.944
- avg cost: 3.985
- oracle cost: 3.686
- regret: 0.299
- over-harness: 0.153
- under-harness: 0.034
- wrong-harness: 0.005
- unsupported false positives: 12

对比 Phase 2B selected `llm_single`:

- Phase 2B `llm_single`: success 0.889, under 0.089, over 0.145, regret -0.094, unsupported FP 56
- Phase 2C guarded: success 0.944, under 0.034, over 0.153, regret 0.299, unsupported FP 12

结论：registry guard 明显降低 unsupported false positives，并提升 success / 降低 under-harness；代价是平均 cost 和 excess cost (cost delta) 上升，说明它更偏 sufficiency。

## GAIA-Transfer

已运行 `llm_registry_guarded` on GAIA-Transfer v1.0 200 rows。该结果仅是 obligation-transfer stress test，不是 GAIA answer-level solving。

结果：

- success: 0.560
- avg cost: 5.560
- oracle cost: 1.480
- regret: 4.080
- over-harness: 0.890
- under-harness: 0.440
- wrong-harness: 0.420
- guard applied: 0 / 200

解释：GapBench 上的 registry guard 修的是 sandbox/mock action 被误判为 real-world side effect 的问题；GAIA 的主要失败不是这个，而是 multimodal/file/evidence/state obligation mismatch。因此 GAIA-Transfer 不能作为 Phase 2C guard 成功证据，只能作为 transfer limitation 证据。

## Terminal-Bench-obligation50

已生成：

- `benchmarks/terminal_obligation/v0.1/terminal_obligation50_for_review.jsonl`
- `benchmarks/terminal_obligation/v0.1/manifest.json`
- `benchmarks/terminal_obligation/v0.1/schema.md`
- `benchmarks/terminal_obligation/v0.1/review_sheet.csv`

重要边界：

- task text 来源于 public Terminal-Bench GitHub repo：`harbor-framework/terminal-bench/original-tasks/*/task.yaml`
- 每条包含 `source_dataset`、`source_task_id`、`source_path`、`source_url`
- `gold_source` 全部是 `generated_for_human_review_pending_audit`
- 不标记为 human-audited gold
- 这不是 full Terminal-Bench solving

当前分布反映官方 Terminal-Bench task 的真实形态：

- sandbox_action_control_state_verification: 45
- observation_execution: 4
- execution_only: 1

官方 Terminal-Bench 主要是可解的容器任务，不天然包含 ambiguous target / unsupported real production mutation 负例；如果需要这些，应另建 GapHarness negative controls，不能混入 official-derived Terminal-Bench scaffold。

## Terminal-Bench-obligation50 sandbox smoke (20 cases)

已运行本地 sandbox-only smoke：

- cases: 20
- deterministic smoke checks passed: 20 / 20
- network used: no
- production paths modified: no
- traces: `outputs/phase2c/terminal_smoke20_traces.jsonl`
- report: `outputs/phase2c/terminal_smoke20_report.md`

该结果只是 qualitative smoke evidence，不是 Terminal-Bench solve result。

## 测试与安全

最终验证已完成：

- `python3 -m pytest`: 16 passed
- `python3 -m py_compile scripts/run_phase2b_llm_sweep.py gapharness/llm_profiler.py gapharness/profiler.py`: passed
- secret scan: no provided API/HF token patterns found in repo
- Phase 2B checksum comparison: no diff; `outputs/phase2b/` 未被修改

## 当前限制

- `llm_registry_guarded` 提升的是 GapBench sandbox/mock action calibration，不是通用 obligation inference。
- GAIA-Transfer 暴露出明显 transfer gap：当前 profiler 对 GAIA 文件、多模态、证据与状态需求的边界仍不稳定。
- Terminal-Bench-obligation50 labels 尚未人工 audit，不能作为 paper gold result，只能作为下一阶段 review package。
- Terminal-Bench-obligation50 sandbox smoke（20 cases）是 sandbox trace smoke，不代表真实 Terminal-Bench container benchmark 成绩。
