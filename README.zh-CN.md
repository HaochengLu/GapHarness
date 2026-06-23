# GapHarness 中文说明

GapHarness 是一个面向论文和可复现实验的研究系统，用于 **API-only LLM agent 的 certificate-carrying runtime harness compilation**。它关注的不是最终答案是否正确，而是：面对一个用户请求，agent 需要哪些外部运行时支持，这些支持是否覆盖任务义务，是否最小，是否可审计，是否在 registry 边界内真实存在。

论文 PDF：

[paper/submission/arxiv_package/gapharness_arxiv.pdf](paper/submission/arxiv_package/gapharness_arxiv.pdf)

英文主 README：

[README.md](README.md)

## 核心问题

很多 agent 系统把两个问题混在一起：

1. 用户请求到底带来了哪些义务？
2. 应该调用哪些工具或 runtime module 才足够、安全、可验证？

GapHarness 把它们拆开：先得到 obligation profile，再在 declared registry 上编译出最低 declared-cost 的 harness。如果 registry 缺少能力，系统应该显式给出 `unsupported`、`under-covered` 或 verifier failure，而不是假装可以完成。

## 六类 Obligations

- Observation：需要外部信息、来源、检索、引用。
- Execution：需要代码运行、命令执行、测试。
- State：需要 durable task state、workspace state、intermediate artifacts。
- Action：需要 sandbox action、文件 patch、受控修改。
- Control：需要权限、预算、风险、不可逆操作边界。
- Verification：需要 contract check、source span check、trace check、test result check。

## 仓库内容

```text
gapharness/                         核心库
scripts/                            构建 benchmark、跑实验、生成报告
tests/                              单元测试
benchmarks/                         冻结 benchmark 和 manifest
outputs/final/                      最终结果、trace、checksum
paper/submission/arxiv_package/     PDF、论文源码、表格、图、附录报告
docs/                               claim 边界、最终结果说明、中文状态文档
```

## 包含的主要证据

- GapBench-1000 controlled benchmark。
- GAIA Transfer-200 project-owner-audited diagnostic set。
- Natural-200 project-owner-audited naturalized prompts。
- HarnessChallenge-200 targeted boundary diagnostic。
- SWE-HarnessExec-50 provided-patch sandbox pytest traces。
- Strong baselines：Direct、Tool Router、LLM Tool Router、Always-full、Workflow Generator、ReAct-style Selector、Verifier-Repair Router、GapHarness-Repair。
- Stress tests：registry perturbation、gold label permutation、tool-bait / pure-language negative controls。
- Certificate utility、feedback-level replay、compiler scaling、status confusion、profiler error taxonomy。

## 论文主张边界

这个仓库不声称：

- 解决 open-world answer correctness；
- 达到 SWE-bench pass@1；
- 自动生成真实 patch；
- 比任意 LangGraph / AutoGen / agent framework 本身更强；
- 在真实不可逆 API、部署、邮件、生产系统上执行 action。

它声称的是：

> 在 runtime affordances 已由有限 registry 声明的前提下，obligation-first compilation 可以把 profile inference 和 support selection 分离，并生成可审计、可验证、registry-relative minimal 的 harness selection 证据。

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

小规模 seed benchmark：

```bash
python -m scripts.build_seed_benchmark --out benchmarks/gapbench_factorial_seed.jsonl
python -m gapharness.cli run-benchmark \
  --benchmark benchmarks/gapbench_factorial_seed.jsonl \
  --system all \
  --profiler gold \
  --out outputs/results_seed_gold.jsonl
python -m gapharness.cli make-report \
  --results outputs/results_seed_gold.jsonl \
  --out outputs/summary_seed_gold.md
```

校验最终 artifact：

```bash
pytest
python -m py_compile gapharness/*.py scripts/*.py
shasum -a 256 -c --status --strict outputs/final/checksums.sha256
shasum -a 256 -c --status --strict paper/submission/arxiv_package/checksums.sha256
```

LLM profiler 相关实验需要通过环境变量配置 OpenAI-compatible API。仓库中不包含任何 API key 或私有 provider endpoint。

## Artifact 完整性

最终发布前已做以下检查：

- 单元测试通过；
- Python 文件可编译；
- root/package checksum 可验证；
- PDF 可渲染；
- 未包含私有 API endpoint、API key 或 dummy `sk-...` token pattern。

