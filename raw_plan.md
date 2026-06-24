# 技术报告草案：Obligation-First Minimal Harness Synthesis for API-only LLM Agents

## 摘要

本项目提出一个不训练模型、仅依赖 LLM API 与外部工具 API 的 agent harness synthesis 框架。核心思想不是让模型直接选择工具，也不是自动生成完整 workflow，而是将 harness 重新定义为：

> **为无状态 token predictor 补齐任务可靠完成所需外部义务的最小运行时系统。**

给定用户 query、基础模型和可用工具/模块集合，系统首先推导该任务要可靠完成必须满足哪些外部义务，例如外部观察、确定性执行、状态保持、外部行动、权限控制、结果验证；然后根据模块 affordance 合成覆盖这些义务的最小 harness；最后通过 trace-grounded verifier 与 counterfactual ablation 验证该 harness 是否既充分又不过度。

本项目的研究问题是：

> **Can an API-only system infer the external obligations required by a user query and compile the minimal runtime harness that makes an LLM response/action warranted?**

它的目标不是顶会级别地提出一个大模型训练方法，而是形成一个可以写成 workshop paper / system paper / arXiv technical report 的研究型工程项目。它的贡献应集中在问题定义、第一性原理推导、最小 harness 编译、minimal sufficiency evaluation，以及真实 benchmark 上的 transfer 验证。

---

## 1. 背景与定位

当前 LLM agent 的可靠性越来越不只由 base model 决定，而由模型外部的 harness 决定。近期 Harness-Bench 明确指出，agent workflow 的表现依赖 harness 这个系统层，包括 context、tools、state、constraints、permissions、tracing 和 recovery；它还主张 agent 能力不应只归因于 base model，而应以 model-harness configuration 为单位报告。([arXiv](https://arxiv.org/abs/2605.27922?utm_source=chatgpt.com "Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows")) 另一些 harness engineering 工作也把 harness 定义为围绕 foundation-model software agent 的 runtime substrate，用于管理 context、tools、project memory、task state、observability、failure attribution、verification、permissions 和 maintenance state。([arXiv](https://arxiv.org/html/2605.13357v1?utm_source=chatgpt.com "A Runtime Substrate for Foundation-Model Software Agents"))

这说明 harness 已经成为一个正在成形的研究对象。但现有工作大多在以下几个方向展开：一类研究如何让 LLM 调用工具；一类研究如何自动生成 workflow；一类研究如何评测不同 harness 配置的影响；一类研究如何将 harness 逻辑自然语言化或代码化。它们尚未把“每个 query 要可靠成立需要哪些外部义务”作为第一层对象，也没有明确提出“query → obligations → minimal harness compiler → sufficiency/minimality verification”的完整问题形式。

因此，本项目的定位是：

> **不是 tool-use，不是 workflow generation，不是 harness benchmark，而是 obligation-first minimal harness synthesis。**

---

## 2. 相关工作与研究空缺

ReAct 将 reasoning 与 acting 交替起来，使模型在推理过程中调用外部信息源或环境，从而缓解 hallucination 和 error propagation；但 ReAct 默认进入 reasoning-action loop，并不先判断该 query 是否需要 loop、需要什么外部义务、以及最小 loop 是什么。([arXiv](https://arxiv.org/abs/2210.03629?utm_source=chatgpt.com "ReAct: Synergizing Reasoning and Acting in Language Models")) Toolformer 训练模型学习何时调用 API、调用什么参数以及如何把结果接回语言建模；Gorilla、ToolLLM/ToolBench 等方向也主要关注 tool-use 能力、API 调用和工具学习框架，而不是 API-only 的 runtime harness synthesis。([arXiv](https://arxiv.org/abs/2302.04761?utm_source=chatgpt.com "Toolformer: Language Models Can Teach Themselves to Use Tools"))

MetaTool 已经专门评估 LLM 是否知道该用工具、该用哪个工具；Adaptive Tool Use / MeCo 进一步讨论何时调用工具，以减少不必要工具调用带来的 latency 和错误；Model-Adaptive Tool Necessity 还指出 tool necessity 应该依赖具体模型能力边界，并发现模型在“知道该用工具”和“真的调用工具”之间存在 knowing-doing gap。([arXiv](https://arxiv.org/abs/2310.03128?utm_source=chatgpt.com "MetaTool Benchmark for Large Language Models: Deciding Whether to Use Tools and Which to Use")) 这些工作非常接近本项目，但它们仍然处在 tool necessity / tool selection 层面。本项目要上移一层：工具只是 obligation 的一个实现，真正要推导的是任务可靠完成所需的外部义务集合。

Workflow generation 方向也已经很密集。AutoFlow 自动生成 agent workflows；AFlow 将 workflow optimization 表述为 code-represented workflow 上的搜索问题；WorFBench 专门评测 agentic workflow generation；DAAO 根据 query difficulty、domain 和 features 动态生成 workflow 并权衡 performance-cost；AgentSwift 进一步把 workflow、memory、tool use 和 planning 放到 hierarchical search space 中。([arXiv](https://arxiv.org/abs/2407.12821?utm_source=chatgpt.com "AutoFlow: Automated Workflow Generation for Large Language Model Agents")) 这些工作说明“query-specific workflow”已经不是空白。因此，本项目不能说自己首创 query-specific agent workflow；它必须强调：本项目不是从 difficulty scalar 或 graph search 出发，而是从任务可靠性的 obligation vector 出发，再编译最小 harness。

最近也有直接研究 harness 的工作。Natural-Language Agent Harnesses 将 harness 行为表达成可编辑自然语言，并通过 Intelligent Harness Runtime 以 explicit contracts、durable artifacts 和 lightweight adapters 执行；Externalization in LLM Agents 把 memory、skills、protocols 和 harness 视为把模型内部负担外部化的系统基础设施。([arXiv](https://arxiv.org/abs/2603.25723?utm_source=chatgpt.com "Natural-Language Agent Harnesses")) AutoHarness 最接近“自动合成 harness”：它让模型在 TextArena 游戏环境中根据环境反馈合成 code harness，以防止非法动作，并报告在 145 个 TextArena games 中阻止非法动作。([arXiv](https://arxiv.org/abs/2603.03329?utm_source=chatgpt.com "AutoHarness: improving LLM agents by automatically synthesizing a code harness")) 但 AutoHarness 的核心场景是 game/environment feedback 下的非法动作防护；本项目的核心是自然语言 query 的 external obligation inference 与通用 minimal runtime harness synthesis。

因此，当前可守住的 novelty 是：

> **Prior work studies tool selection, tool necessity, workflow generation, harness representation, or harness evaluation. This project studies a complementary problem: given a query and a base model, infer the external obligations required for a response/action to be warranted, then compile the minimal runtime harness that satisfies those obligations.**

---

## 3. 第一性原理：从 token predictor 到 harness

LLM 的底层形式可以抽象为：

[
M\_\\theta: C \\rightarrow P(y\_{t+1})
]

即：给定上下文 (C)，预测下一个 token 的概率分布。这个定义本身决定了 LLM 原生缺少六类外部能力。

第一，LLM 没有可靠的外部观察能力。它不能天然知道网页、文件、数据库、系统环境、用户账户、当前价格、当前日期后的事实。

第二，LLM 没有确定性执行能力。它可以生成看似正确的数学、代码、表格或推理，但无法保证精确计算、运行测试、执行程序或验证 schema。

第三，LLM 没有持久状态能力。单次上下文内可以模拟状态，但不能天然维持 durable memory、task trace、workspace checkpoint 或跨步骤 artifact。

第四，LLM 没有真实行动能力。生成“我已经修改”不是修改文件；生成“我已发送”不是调用 API；生成“部署完成”不是改变外部系统状态。

第五，LLM 没有可强制的控制能力。权限、预算、风险、不可逆动作、工具边界、信息泄露边界不能只靠 prompt 保证，需要 runtime gate。

第六，LLM 没有独立验证能力。模型说“正确”不等于正确；必须通过证据、测试、引用、trace、validator 或 contract checker 来证明。

由此推出 harness 的第一性原理：

> **Harness 是把无状态 token predictor 转换为可观察、可执行、可控、可验证任务系统的外部运行时层。**

本项目进一步提出：

> **Minimal harness 是对特定 query 而言，覆盖其可靠完成所需外部义务的最小模块集合。**

---

## 4. 核心概念：Obligation，而不是 Tool

本项目不从工具分类出发，而从 obligation 出发。工具是实现方式，obligation 是任务可靠性的底层需求。

定义六个不可再拆的外部义务原语：

[
\\mathcal{O} = {
Observation,\\ Execution,\\ State,\\ Action,\\ Control,\\ Verification
}
]

它们分别表示：

**Observation**：任务需要当前上下文外的信息，例如网页、文件、数据库、repo、图片、PDF、用户账户、实时数据。

**Execution**：任务需要确定性过程，例如计算、代码执行、测试、lint、parser、schema validation、simulation。

**State**：任务需要跨步骤保持任务状态，例如 checklist、intermediate artifacts、workspace state、memory、trace。

**Action**：任务需要改变外部世界，例如编辑文件、调用 API、提交 PR、写数据库、发邮件、部署服务。

**Control**：任务涉及边界和约束，例如权限、预算、隐私、不可逆动作、工具白名单、风险等级、用户确认。

**Verification**：任务需要独立证明，例如 citation、source span、unit test、diff check、output contract、validator、counterfactual ablation。

这六个 obligation 是 bottom-to-top 设计的底层。真实世界 case 无穷无尽，但系统不试图枚举 case；它将 case 映射为 obligation 的组合。这样才能避免 toy 化。

---

## 5. 问题形式化

给定：

[
q
]

表示用户 query；

[
M
]

表示 base model；

[
\\mathcal{R} = {m\_1, m\_2, ..., m\_n}
]

表示 harness module registry。

每个 module (m\_i) 声明：

[
Provides(m\_i) \\subseteq \\mathcal{O}
]

以及 cost、risk、dependency、permission requirement 和 verifier。

Obligation Profiler 的目标是输出：

[
O(q, M) \\subseteq \\mathcal{O}
]

即该 query 对该模型而言需要哪些外部义务。

Harness Compiler 的目标是求解：

[
H^\* = \\arg\\min\_{H \\subseteq \\mathcal{R}} Cost(H)
]

subject to：

[
O(q, M) \\subseteq \\bigcup\_{m \\in H} Provides(m)
]

并满足：

[
Dependencies(H),\\ Permissions(H),\\ Risk(H),\\ Contract(q)
]

也就是说，系统不是选“看起来合适的工具”，而是在 obligation space 中求一个最小覆盖。

这可以被视为 weighted set cover / constrained optimization。第一版实现中，module 数量不大，可以直接 exact search；这样可以在技术报告中证明 relative minimality。后续如果 registry 变大，再换成 ILP 或 greedy approximation。

---

## 6. 相对完备性：如何证明不是 toy

本项目不能声称“解决所有真实世界 case”。这在学术上不成立。真实世界任务包含无限工具、未知环境、未知用户意图、权限限制和不断变化的外部状态。

本项目应主张 **relative completeness**：

> 对于所有可以被本系统 obligation primitives 表达的 query，只要 module registry 中存在覆盖这些 obligations 的模块，compiler 就能合成一个满足义务覆盖的 harness；如果不存在覆盖模块，系统应显式返回 unsupported / need permission / need clarification，而不是假装完成。

形式化为：

若：

[
O(q,M) \\subseteq \\mathcal{O}
]

且存在：

[
H \\subseteq \\mathcal{R}
]

使得：

[
O(q,M) \\subseteq \\bigcup\_{m \\in H} Provides(m)
]

则 compiler 可以返回一个 sufficient harness。若使用 exact search，则返回成本最小的 sufficient harness。

这个证明比“我们覆盖很多例子”更强。它说明系统的泛化不是来自 benchmark trick，而是来自 obligation 原语的组合性。

---

## 7. 系统设计

系统名可以保留为 **GapHarness**，论文概念名建议使用：

> **Obligation-First Harness Synthesis**

整体 pipeline：

```text
User Query
 → Obligation Profiler
 → Obligation Vector + Output Contract
 → Module Registry Lookup
 → Minimal Harness Compiler
 → Loop Template Compiler
 → Executor
 → Trace Recorder
 → Verifier
 → Minimality / Sufficiency Report
```

### 7.1 Obligation Profiler

输入 query，输出结构化对象：

```json
{
  "direct_llm_sufficient": false,
  "obligations": [
    "Observation",
    "Verification",
    "Control"
  ],
  "output_contract": {
    "must_include_source": true,
    "must_include_absolute_dates": true,
    "must_distinguish_current_and_historical": true
  },
  "forbidden_paths": [
    "answer_from_parametric_memory_without_evidence"
  ],
  "risk_level": "medium",
  "unsupported_possibility": []
}
```

Profiler 不是问“该用哪个工具”，而是问：

> 这个回答要成立，需要哪些外部条件？

为了降低单次 LLM 判断的不稳定性，可以使用两个 profiler 独立输出，再由 adjudicator 合并。这里不要包装成 multi-agent hype，而应称为 **consensus obligation inference**。

### 7.2 Module Registry

每个 module 必须声明 affordance，而不是靠系统 hardcode query type。

```json
{
  "name": "web_retrieval",
  "provides": ["Observation", "Verification"],
  "requires": [],
  "cost": 3,
  "risk": ["stale_source", "source_conflict"],
  "verifier": "source_span_checker"
}
```

```json
{
  "name": "python_executor",
  "provides": ["Execution", "Verification"],
  "requires": [],
  "cost": 2,
  "risk": ["runtime_error"],
  "verifier": "execution_log_checker"
}
```

```json
{
  "name": "file_editor",
  "provides": ["Action", "State"],
  "requires": ["Control"],
  "cost": 4,
  "risk": ["irreversible_change"],
  "verifier": "diff_checker"
}
```

这个 registry 让系统具有可扩展性。新工具只需要声明它提供哪些 obligation、依赖哪些条件、风险是什么、如何验证，而不需要重写整体系统。

### 7.3 Minimal Harness Compiler

Compiler 输入 obligation vector 和 registry，输出最小 module set。

示意伪代码：

```python
def compile_minimal_harness(query, model, registry):
    obligations = profile_obligations(query, model)

    candidates = enumerate_module_subsets(registry)
    valid = []

    for H in candidates:
        if covers(H, obligations) and satisfies_constraints(H, obligations):
            valid.append(H)

    if not valid:
        return Unsupported(
            missing=missing_obligations(obligations, registry),
            required_permission=required_permissions(obligations)
        )

    H_star = min(valid, key=total_cost)
    loop = compile_loop_template(H_star, obligations)
    return H_star, loop
```

第一版不用追求复杂算法。exact search 的优点是能证明 minimality。只要 module registry 控制在 8–12 个，完全可行。

### 7.4 Loop Template Compiler

不同任务不应默认进入 full agent loop。系统应根据 obligations 选择最小 loop topology。

基本 loop templates：

```text
direct_answer
retrieve_then_answer
compute_then_answer
retrieve_compute_verify
inspect_then_answer
inspect_edit_verify
permission_act_verify
unsupported_or_clarify
```

例如：

“写一句生日祝福” → direct\_answer。

“查今天某公司最新公告并总结” → retrieve\_then\_answer + evidence verifier。

“计算一批数据并生成表格” → compute\_then\_answer + execution verifier。

“修复 repo 中一个测试失败” → inspect\_edit\_verify + diff checker + test verifier。

这样可以直接打击 agent 领域的一个真实问题：很多系统 over-harness，小任务也开大 loop，增加成本、latency 和失败面。

---

## 8. Verification：项目成败的核心

没有 verifier，这个项目只是一个 planner。有 verifier，它才是 harness synthesis。

至少需要四类 verifier。

### 8.1 Contract Verifier

检查最终回答是否满足 output contract：

```text
是否回答了 query？
是否包含要求的格式？
是否包含绝对日期？
是否包含 citations？
是否区分当前事实和历史事实？
是否遵守用户限制？
```

### 8.2 Evidence Verifier

检查关键 factual claim 是否被 observation 支持。对于 retrieval 任务，最终回答中的关键 claim 必须能映射到 source span。对于文件任务，claim 必须能映射到 file span / diff / trace。

### 8.3 Execution Verifier

检查确定性执行是否真的发生，例如 calculator result、Python output、unit test、lint result、schema validation。

### 8.4 Minimality Verifier

这是本项目最像 paper 的部分。对已选择 harness 中的每个 module 做 drop-one ablation：

[
H\_{-m} = H \\setminus {m}
]

如果移除 module 后 verifier fail，则该 module 对任务是 necessary。若移除后仍通过，说明原 harness 可能 over-harness。

这能形成一个新指标：

[
Necessity(m) = \\mathbb{1}[Verifier(H\_{-m}) = fail]
]

并进一步定义：

[
Redundancy(H) = \\frac{|{m \\in H: Verifier(H\_{-m}) = pass}|}{|H|}
]

这使你的系统不只是“会选工具”，而是能证明自己选的 harness 不是多余的。

---

## 9. Evaluation：不只看准确率，而看 minimal sufficiency

传统 accuracy 不足以证明这个项目。因为一个 always-full agent 可能 accuracy 高，但成本和失败面也高；direct LLM 成本低，但 under-harness 严重。

本项目应定义以下指标：

### 9.1 Task Success

最终任务是否完成。

[
Success(q) \\in {0,1}
]

### 9.2 Cost-normalized Success

[
CNS = \\frac{Success}{TokenCost + ToolCost + LatencyCost}
]

### 9.3 Over-harness Rate

本来不需要某些外部义务，却调用了相关模块。

[
OverHarness = P(Cost(\\hat{H}) > Cost(H^\*\_{oracle}))
]

### 9.4 Under-harness Rate

需要某个 obligation，却没有覆盖。

[
UnderHarness = P(O(q,M) \\nsubseteq Affordances(\\hat{H}))
]

### 9.5 Wrong-harness Rate

选择了外部模块，但没有覆盖真正缺口。例如需要 Execution，却只做 Retrieval。

### 9.6 Minimality Regret

[
Regret = Cost(\\hat{H}) - Cost(H^\*\_{oracle})
]

### 9.7 Counterfactual Necessity

对系统选中的 module 做移除实验，观察 verifier 是否失败。

这些指标共同证明：GapHarness 不是追求“越多工具越强”，而是追求 **足够且最小**。

---

## 10. Benchmark 设计：GapBench-Factorial

为了证明不是 toy，不能只拿几十个 demo。需要构造一个小而严谨的 factorial benchmark。

核心思想：

> 不按场景枚举，而按 obligation combination 覆盖。

六个 primitives：

```text
Observation
Execution
State
Action
Control
Verification
```

数据集应覆盖：

```text
single-obligation tasks
pairwise-obligation tasks
triple-obligation tasks
pure-language negative tasks
tool-bait tasks
unsupported tasks
permission-gated tasks
ambiguous tasks
```

每条样本包括：

```json
{
  "query": "...",
  "gold_obligations": ["Observation", "Verification"],
  "oracle_minimal_harness": ["web_retrieval", "source_span_checker"],
  "success_checker": "...",
  "expected_failure_if_direct": "stale_or_unsupported_claim",
  "risk_level": "medium"
}
```

这不是为了造一个大 benchmark，而是为了证明 obligation ontology 的覆盖性和 compiler 的正确性。第一版 200–300 条足够写技术报告。

---

## 11. 真实 benchmark transfer

GapBench-Factorial 证明系统内部逻辑，真实 benchmark 证明不是 toy。

可以选择以下真实评测子集：

GAIA 包含需要 reasoning、多模态处理、web browsing 和 tool-use 的真实问题，并报告人类与带插件 GPT-4 之间存在明显差距，因此适合作为 general assistant 场景验证。([arXiv](https://arxiv.org/abs/2311.12983?utm_source=chatgpt.com "[2311.12983] GAIA: a benchmark for General AI Assistants")) WildToolBench 专门强调真实用户行为中的 compositional tasks、implicit intent 和 instruction transition，并报告 57 个 LLM 无一超过 15% accuracy，适合测试系统是否能处理真实 tool-use 行为复杂性。([OpenReview](https://openreview.net/forum?id=yz7fL5vfpn&utm_source=chatgpt.com "Benchmarking LLM Tool-Use in the Wild")) MCP-Bench 提供基于 MCP 的真实多步工具任务，连接 28 个 MCP servers 与 250 个 tools，测试 cross-tool coordination、parameter control 和 planning/reasoning，适合验证 registry + affordance + compiler 的扩展性。([arXiv](https://arxiv.org/abs/2508.20453?utm_source=chatgpt.com "MCP-Bench: Benchmarking Tool-Using LLM Agents with Complex Real-World Tasks via MCP Servers")) Terminal-Bench 2.0 包含 89 个 terminal environment 中的 hard realistic tasks，适合验证 coding / execution / state / verification 类 harness。([arXiv](https://arxiv.org/abs/2601.11868?utm_source=chatgpt.com "Terminal-Bench: Benchmarking Agents on Hard, Realistic ..."))

不需要一开始全量跑。技术报告中可以做 subset transfer，重点不是刷榜，而是证明：

> 在真实任务上，GapHarness 相比 direct LLM 降低 under-harness，相比 always-full agent 降低 over-harness 和成本，相比 tool router 提高 obligation coverage 和 verifier pass rate。

---

## 12. Baselines

实验至少比较五种系统：

**Direct LLM**：不使用外部 harness，测试 under-harness。

**Always-full Agent**：总是启用 retrieval、execution、planner、verifier、memory，测试 over-harness 和成本。

**Tool Router**：直接让 LLM 从工具列表中选择工具，作为 tool-first baseline。

**Difficulty Router**：让 LLM 判断 easy/medium/hard，再选择 direct/light/full harness，对照 difficulty-aware workflow 思路。

**Oracle Minimal Harness**：人工或 brute force 得到 gold minimal harness，作为上界。

GapHarness 的目标不是所有任务上超过 full agent，而是在 success 接近或更高的同时，显著降低 tool calls、loop steps、latency、minimality regret、over-harness 和 under-harness。

---

## 13. 可实现系统边界

第一版系统只需要少量模块：

```text
direct_answer
web_retrieval
source_span_checker
python_executor
file_state_reader
file_state_editor
contract_verifier
permission_gate
trace_recorder
```

不需要一开始做：

```text
multi-agent
复杂浏览器自动化
长期记忆系统
完整 MCP marketplace
自动部署系统
大规模 API ecosystem
```

原因是：本项目的研究价值不在工具数量，而在 obligation-first 的系统形式化和 minimality verification。工具越多，越容易变成杂乱工程 demo；工具少但原语清楚，反而更像 paper。

---

## 14. 预期论文贡献

论文贡献应写成四点。

第一，提出 **obligation-first view of harnessing**：LLM 的可靠回答/行动必须满足一组 token predictor 本身无法保证的外部义务，harness 是这些义务的运行时实现。

第二，提出 **Minimal Harness Compiler**：将 query-level obligation vector 编译为覆盖这些 obligations 的最小 module set 与 loop topology。

第三，提出 **Minimal Sufficiency Evaluation**：不只评估最终准确率，还评估 over-harness、under-harness、wrong-harness、minimality regret 和 counterfactual necessity。

第四，构建 **GapBench-Factorial** 并在真实 benchmark subset 上 transfer，证明系统不是为少量 demo hardcode，而是对 obligation composition 具有覆盖能力。

---

## 15. 论文边界与风险

这个项目必须克制自己的 claim。

不能声称：

> 我们解决所有真实世界 case。

应该声称：

> 我们证明一大类真实 LLM-agent 任务可以被表示为少量外部义务的组合；在这些义务可由 registry module 覆盖时，系统能合成最小充分 harness；当无法覆盖时，系统显式报告 unsupported / permission needed / clarification needed。

主要风险有三个。

第一，Obligation Profiler 仍然依赖 LLM API，可能出现误判。解决方式是 consensus profiling、gold obligation benchmark、ablation 和 verifier feedback。

第二，module affordance 声明可能不准确。解决方式是 registry schema 固定、每个 module 必须绑定 verifier，并在实验中报告 coverage failure。

第三，minimality 只能相对于当前 registry 和 cost function 成立。解决方式是在论文中明确：minimality 是 **relative minimality under a declared registry and cost model**，不是绝对世界最优。

---

## 16. 最终收敛后的技术计划

本项目最终应以如下形式实现和写作：

```text
Problem:
LLM 是无状态 token predictor。真实任务可靠完成需要外部观察、执行、状态、行动、控制和验证。现有 tool-use / workflow / harness 工作没有系统解决 query-conditioned minimal harness synthesis。

Core Idea:
先推导 query 的 external obligations，再根据 module affordance 编译最小 harness，而不是直接选择工具或默认启动完整 agent。

System:
Obligation Profiler
→ Module Registry
→ Minimal Harness Compiler
→ Loop Template Compiler
→ Executor
→ Trace Recorder
→ Contract/Evidence/Execution/Minimality Verifier

Formal Claim:
在 obligation profiler 正确、module affordance 正确、registry 可覆盖的条件下，compiler 能返回覆盖 obligations 的 sufficient harness；若使用 exact search，则返回 relative minimal harness；若不可覆盖，则显式 unsupported，而不是 hallucinated completion。

Evaluation:
GapBench-Factorial 测 obligation coverage 与 minimality；
GAIA / WildToolBench / MCP-Bench / Terminal-Bench subset 测真实任务 transfer；
指标包括 success、cost-normalized success、over-harness、under-harness、minimality regret、counterfactual necessity。

Contribution:
obligation-first harness theory；
minimal harness compiler；
minimal sufficiency metrics；
factorial benchmark + real benchmark transfer。
```

一句话收束：

> **GapHarness is an API-only, obligation-first harness compiler: it infers what external obligations a query imposes on a stateless token predictor, compiles the minimal runtime harness that satisfies those obligations, and verifies both sufficiency and minimality through execution traces and counterfactual ablations.**

中文版本：

> **GapHarness 是一个 API-only 的 obligation-first harness compiler：它先判断一个 query 对无状态 token predictor 提出了哪些外部义务，再合成覆盖这些义务的最小运行时 harness，并通过执行 trace 与反事实消融验证该 harness 既足够又不过度。**

这个版本已经足够收敛。继续推进时，不应该再扩展成“大而全 agent framework”，而应该围绕一个核心命题做深：

> **可靠 agent 不是给 LLM 加更多工具，而是给每个 query 补齐最小必要外部义务。**
>
