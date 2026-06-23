# Related Work Comparison Table

| Work | Primary object | Obligation-level? | Registry-relative minimality? | Query-conditioned? | Verifier/stress tests? | Difference from GapHarness |
|---|---|---|---|---|---|---|
| ReAct / Toolformer | tool-using LM behavior | no | no | yes | task eval | GapHarness compiles declared harnesses from obligations. |
| Gorilla / ToolLLM | API selection/calling | no | no | yes | API benchmarks | GapHarness separates obligation inference from module selection. |
| MetaTool | tool necessity | partial/tool-level | no | yes | tool-choice eval | GapHarness adds registry-relative minimal compilation and stress tests. |
| AutoFlow / AFlow / WorFBench | agentic workflow generation | no | no; workflow optimization | yes | workflow benchmarks | GapHarness targets minimal runtime coverage, not workflow synthesis. |
| AutoHarness / NL Agent Harnesses | harness synthesis/specification | partial | not over finite obligation registry | yes | system eval | GapHarness formalizes obligation/capability coverage over a finite registry. |
| Harness-Bench | harness effects benchmark | no | no | mixed | benchmarked effects | GapHarness provides a compiler and anti-circularity tests for declared harness synthesis. |
