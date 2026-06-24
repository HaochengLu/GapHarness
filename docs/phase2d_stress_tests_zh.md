# Phase 2D 状态报告：Stress Tests + Negative Controls

## 目标

Phase 2D 的目标是补上 reviewer 最容易攻击的三个问题：

1. GapHarness 是否只是“无条件成功”的系统？
2. GapBench gold labels 是否只是装饰？
3. GapHarness 是否只是 keyword/tool-sensitive router？

本阶段新增一个可复现实验脚本：

```bash
python3 -m scripts.run_phase2d_stress_tests all
```

所有输出写入 `outputs/phase2d/`，不覆盖 Phase 2B / Phase 2C。

## Stress Test 1：Registry Perturbation

目的：证明 GapHarness 的成功依赖 declared registry affordances。缺失关键 module 时，系统不会 silent hallucinate support，而是显式 unsupported / under-covered / verifier fail。

扰动设置：

- base registry
- remove `python_executor`
- remove `source_span_checker`
- remove `permission_gate`
- remove `sandbox_file_editor`
- remove `web_retrieval`
- remove `contract_verifier`

每个扰动只在相关 first-N subset 上跑，每组 60 条；这是 affordance-boundary stress test，不声称覆盖所有相关样本：

| Perturbation | Removed Module | Base Success | Perturbed Success | Unsupported | Under-covered | Dominant Missing |
|---|---|---:|---:|---:|---:|---|
| remove_python_executor | python_executor | 1.00 | 0.00 | 1.00 | 1.00 | execution |
| remove_source_span_checker | source_span_checker | 1.00 | 0.00 | 1.00 | 1.00 | source_spans |
| remove_permission_gate | permission_gate | 1.00 | 0.00 | 1.00 | 1.00 | permission |
| remove_sandbox_file_editor | sandbox_file_editor | 1.00 | 0.00 | 1.00 | 1.00 | diff |
| remove_web_retrieval | web_retrieval | 1.00 | 0.00 | 1.00 | 1.00 | evidence_sources |
| remove_contract_verifier | contract_verifier | 1.00 | 0.00 | 1.00 | 1.00 | contract_check |

核心结论：registry 缺失能力时，GapHarness 不会继续声称支持，而是显式失败。该实验支持 paper 中的边界句：

> Registry perturbation verifies that GapHarness does not silently hallucinate support when required affordances are absent; it degrades into unsupported or under-covered status.

## Stress Test 2：Gold Label Permutation

目的：证明 GapBench labels 不是无意义装饰。错误 labels 会导致可测量的 harness failure。

协议：

- 抽取 200 条 supported 且有非空 gold obligations 的 GapBench 样本。
- correct condition：原始 project-owner-reviewed gold labels feed compiler，原始 gold verifier。
- permuted condition：corrupted labels feed compiler，但 verifier 仍检查原始 project-owner-reviewed gold labels。

corruption 包括：

- Observation ↔ Execution
- Action ↔ State
- 删除 Verification
- 添加 Control
- 删除一个 primary obligation

结果：

| Condition | N | Success | Regret | Over | Under | Wrong | Verifier Fail |
|---|---:|---:|---:|---:|---:|---:|---:|
| correct gold | 200 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| permuted labels | 200 | 0.17 | 0.24 | 0.55 | 0.83 | 0.79 | 0.83 |

Permutation integrity: 200 / 200 corrupted profiles changed obligations or required capabilities; no-op corruptions: 0.

核心结论：这是 anti-circularity stress test，不是 realistic corruption model。它说明 compiler/verifier 对 obligation semantics 敏感，不是任意 label 都能通过。

## Stress Test 3：Tool-Bait / Pure-Language Negative Controls

目的：证明 GapHarness 是 obligation-sensitive，而不是 keyword/tool-sensitive。

单独报告两个类别：

- `pure_language_negative`: 100 条
- `tool_bait`: 100 条

对比系统：

- Direct
- Tool Router
- Always-full
- Difficulty Router
- GapHarness gold
- GapHarness LLM
- Registry-guarded GapHarness

关键结果：

| Category | System | N | Success | Avg Cost | Over |
|---|---|---:|---:|---:|---:|
| pure_language_negative | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
| pure_language_negative | Always-full | 100 | 1.00 | 16.00 | 1.00 |
| tool_bait | GapHarness gold | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | GapHarness LLM | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Registry-guarded GapHarness | 100 | 1.00 | 0.00 | 0.00 |
| tool_bait | Tool Router | 100 | 1.00 | 1.26 | 0.51 |
| tool_bait | Difficulty Router | 100 | 1.00 | 1.22 | 0.51 |
| tool_bait | Always-full | 100 | 1.00 | 16.00 | 1.00 |

核心结论：GapHarness 不因为 query 出现 “tool/search/code/file” 等词就过度 harness；Tool Router 和 Difficulty Router 在 tool-bait 上有明显 over-harness，Always-full 必然 over-harness。

## 输出文件

- `outputs/phase2d/registry_perturbation_report.md`
- `outputs/phase2d/registry_perturbation/results_registry_perturbation.jsonl`
- `outputs/phase2d/registry_perturbation/subset_manifest.json`
- `outputs/phase2d/gold_label_permutation_report.md`
- `outputs/phase2d/gold_label_permutation/results_gold_label_permutation.jsonl`
- `outputs/phase2d/gold_label_permutation/permuted_profiles_200.jsonl`
- `outputs/phase2d/negative_control_analysis_report.md`
- `outputs/phase2d/negative_controls/results_negative_controls.jsonl`
- `outputs/phase2d/phase2d_summary.md`

## 证据边界

- Registry perturbation 是 declared affordance boundary test，不是开放世界 agent 能力测试。
- Gold label permutation 是 anti-circularity stress test，不是 realistic benchmark noise model。
- Negative-control analysis 证明 obligation sensitivity，不证明真实用户所有 no-tool 指令都能被完美识别。
- Phase 2D 不替代 Phase 2B/2C 主结果，而是 reviewer-facing robustness evidence。
