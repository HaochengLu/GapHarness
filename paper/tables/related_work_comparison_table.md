# Related Work Comparison Table

| Work | Synthesizes harness? | Finite declared registry? | Obligation inference? | Exact minimality? | Certificate? | Real execution? | Difference from GapHarness |
|---|---|---|---|---|---|---|---|
| ReAct / Toolformer | no | tool set | no | no | no | mixed | Studies tool-using behavior; GapHarness compiles declared runtime support from obligations. |
| Gorilla / ToolLLM / MetaTool | no | API catalog | partial/tool-level | no | no | mixed | Focuses on API selection/necessity; GapHarness separates obligation inference from support compilation. |
| AutoFlow / AFlow / WorFBench | workflow/DAG | no fixed affordance registry | no | workflow objective | no | benchmark-dependent | Optimizes or benchmarks workflows; GapHarness targets minimal runtime coverage under declared affordances. |
| AutoHarness | code harness | partial | no | no | no | yes | Synthesizes code harnesses through feedback; GapHarness selects from a finite registry with certificates. |
| Natural-Language Agent Harnesses | natural-language harness specification | no | no | no | no | yes | Externalizes harness behavior in language; GapHarness uses typed affordances and exact compilation. |
| Harness-Bench | benchmark of harness effects | no | no | no | no | yes | Measures harness configuration effects; GapHarness is a compiler plus anti-circularity diagnostics. |
| Weighted set cover / service composition | no | yes | no | yes/approx | usually no | no | Provides optimization ancestry; GapHarness applies it to auditable LLM runtime support. |
| Feature-model configuration | no | yes | no | constraint solving | sometimes | no | Studies valid product selections; GapHarness adds obligation profiles and runtime-support certificates. |
| Runtime verification / assurance cases | no | policy/spec dependent | no | no | yes | yes | Checks behavior against claims; GapHarness compiles and certifies the support set before execution. |
| GapHarness | registry-selected harness | yes | yes | yes | yes | sandbox traces | Obligation-first, certificate-carrying runtime harness compilation over a declared registry. |
