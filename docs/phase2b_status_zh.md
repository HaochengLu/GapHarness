# Phase 2B 状态汇报：LLM Profiler Calibration + Held-out Test Sweep

更新时间：2026-06-22

## 结论

Phase 2B 已经完成第一版：dev200 三个 LLM profiler 策略已经校准，按预注册规则选出 `llm_single`，并且只用这个策略跑了 held-out test800。

这个阶段的结论不是“profiler 已完全解决”，而是：

- LLM profiler 让 GapHarness 显著超过 Direct / Tool Router / Difficulty Router。
- 成本接近 oracle minimal。
- 但 held-out under-harness 仍然略高，说明 profiler calibration 是下一步核心限制。

## 冻结边界

checkpoint：

```text
phase2-deterministic-artifacts-v1
```

Phase 2B 没有修改：

- GapBench v1.0 labels
- GAIA-Transfer v1.0 labels
- compiler rules
- deterministic baselines
- Phase 2 gold results

## Dev200 校准结果

| Profiler | Success | Avg Cost | Regret | Over | Under | Wrong | Obl F1 | Exact Set |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| llm_single | 0.92 | 3.68 | 0.06 | 0.19 | 0.08 | 0.00 | 0.929 | 0.79 |
| llm_recall | 0.96 | 3.94 | 0.32 | 0.20 | 0.04 | 0.00 | 0.930 | 0.80 |
| llm_minimality | 0.98 | 3.82 | 0.20 | 0.14 | 0.02 | 0.00 | 0.949 | 0.86 |

选择规则：

1. under_harness_rate <= 0.08
2. success >= 0.90
3. 满足 1 和 2 的 profiler 里选 minimality regret 最低的
4. 如果都不满足，选 recall-biased 并把 calibration 写成 limitation

按规则选出：

```text
llm_single
```

## Held-out Test800 结果

| System | Success | Avg Cost | Regret | Over | Under | Wrong |
|---|---:|---:|---:|---:|---:|---:|
| direct | 0.20 | 0.00 | -3.69 | 0.00 | 0.74 | 0.00 |
| tool_router | 0.32 | 1.96 | -1.72 | 0.09 | 0.62 | 0.43 |
| difficulty_router | 0.41 | 3.22 | -0.47 | 0.26 | 0.53 | 0.15 |
| always_full | 0.94 | 16.00 | 12.31 | 0.94 | 0.00 | 0.00 |
| gold_oracle_gap_harness | 1.00 | 3.69 | 0.00 | 0.00 | 0.00 | 0.00 |
| selected_llm_gap_harness | 0.89 | 3.59 | -0.09 | 0.14 | 0.09 | 0.01 |

## 主要发现

`selected_llm_gap_harness` 的优势：

- 比 Direct / Tool Router / Difficulty Router 明显更可靠。
- 成本接近 oracle。
- 比 Always-full 便宜很多。

当前不足：

- success 0.89，略低于 dev 阈值 0.90。
- under-harness 0.09，略高于 dev 规则里的 0.08。
- 不能写成“LLM profiler 已解决”；应该写成“near-practical but calibration-limited”。

## 主要错误模式

最大问题不是 obligation 大方向完全错，而是 capability lowering。

典型情况：

- LLM 预测了正确的 Observation / Action / Control。
- 但额外加入 `real_world_side_effect`。
- MVP registry 不覆盖真实不可逆外部动作，因为当前 Action 只做 sandbox/mock。
- compiler 因此返回 unsupported，导致 supported 任务 under-harness。

下一步最值得做：

```text
registry guard / conservative capability lowering
```

规则可以是：

```text
Only keep real_world_side_effect when the query explicitly asks for real irreversible external action.
Sandbox/mock/local file actions should compile to sandbox_action + permission + diff, not real_world_side_effect.
```

注意：这个应该作为新的 calibrated profiler variant，再走新的 dev/test protocol，不能偷偷改进当前 held-out 结果。
