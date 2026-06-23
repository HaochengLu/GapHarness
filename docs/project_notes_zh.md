# GapHarness 项目说明

目标不是做一个好看的 agent demo，而是尽快做出能跑、能复现实验、能支撑 technical report / workshop paper 的最小可信系统。

第一版锁定：

- 系统名：GapHarness
- 论文概念名：Obligation-First Minimal Harness Synthesis
- 核心义务：Observation / Execution / State / Action / Control / Verification
- Action 只做 sandbox/mock，不做真实不可逆操作
- Benchmark 先做 100 条 synthetic seed，后续逐条人工复核
- Baseline：Direct / Tool Router / Always-full / Difficulty Router / Oracle Minimal
- 第一优先 transfer：GAIA subset

当前实现优先保证：

- exact minimal compiler 可解释
- verifier 可复现
- trace 可审计
- benchmark 和结果报告可一键重跑
