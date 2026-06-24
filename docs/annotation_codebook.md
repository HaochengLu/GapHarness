# Obligation Annotation Codebook (v1.0)

This codebook is the **shared instrument** for the inter-annotator-agreement (IAA)
study. It is written to be readable by an annotator who has never seen the
GapHarness system, its gold labels, its registry, or its tuned profiler prompt.
Each annotator receives **only this codebook plus a user query**, and produces a
structured judgment. The goal is to test whether the abstract obligation labels
are a *reproducible abstraction* that independent annotators converge on, rather
than one designer's private ontology.

You are annotating a **user request to an AI assistant**. Your job is to decide,
from the request text alone:

1. **Obligations** — which of six categories of external requirement the request
   triggers (a set, possibly empty).
2. **Capabilities** — which concrete machine capabilities the request would need.
3. **Status** — whether the request is *supportable in a sandbox/workspace-only
   assistant*, *unsupportable* there, or whether it is *ambiguous and needs
   clarification*.

Annotate what a *correct, careful* assistant would need to do to satisfy the
request as written — not what a lazy assistant might get away with.

---

## 1. The six obligations

An **obligation** is a requirement that cannot be met by the language model
"thinking harder" from prompt text and parametric memory alone. If the request
can be fully and correctly satisfied by pure language generation with no external
dependency, the obligation set is **empty**.

Mark an obligation **present** if satisfying the request *as written* would
require it. Mark it **absent** otherwise. Obligations are not mutually exclusive;
a single request can trigger several.

### Observation
The request needs **information that is not in the prompt and not reliably in the
model's memory** — it must be looked up, read, or retrieved.
- Triggers: reading a named file/README/log/PDF/image, inspecting a repository or
  workspace, fetching a current/latest fact, looking up a specific record.
- Does NOT trigger: general knowledge the model plausibly already has; rephrasing
  text the user already provided.

### Execution
The request needs **deterministic computation, code execution, tests, parsing,
schema validation, or simulation** — something whose correct answer comes from
*running* a procedure, not from prose.
- Triggers: "run the tests", "compute exactly 4127 * 318", lint, execute a
  script, validate against a schema, run a simulation, parse a structured file.
- Does NOT trigger: the mere presence of a number; casual estimation; the word
  "latest" by itself (that is Observation, not Execution).

### State
The request needs **durable task or workspace state** that persists across steps
— intermediate artifacts, a workspace that is read and then written, a
multi-step task whose later steps depend on earlier ones being saved.
- Triggers: build a file, then use it; maintain a scratchpad/checklist across
  steps; modify a workspace whose prior contents matter.
- Does NOT trigger: a single self-contained answer with no saved intermediate.

### Action
The request needs a **mutation / side effect** — it changes something, not just
reads or computes. This covers both **sandboxed** mutations (writing a file in a
workspace, applying a patch to a local copy) and **real-world** mutations
(deploying, sending an email, charging a card). Action is about *changing state
in the world or workspace*, regardless of whether that change is safe.
- Triggers: create/edit/delete a file, apply a patch, deploy, send a message,
  charge/refund, write to a database, restart a service, provision resources.
- Does NOT trigger: read-only inspection; pure computation that returns a value.

### Control
A **cross-cutting constraint** that becomes explicit when the request involves
**permissions, privacy, budget, risk, irreversibility, or a need for user
confirmation**. Control is the "should we, and under what guardrails" obligation
that rides alongside risky or sensitive actions.
- Triggers: anything irreversible or external (real money, real recipients,
  production); handling private/sensitive data; spending budget; an action that
  should be gated on confirmation or permission.
- Does NOT trigger: a trivially safe, reversible, sandbox-local action with no
  sensitive data — though when in doubt on a mutating request, prefer including
  Control.

### Verification
The request needs **independent proof that the answer/action is correct** —
citations or source spans, execution logs, contract/schema checks, or diff
checks. Light "the model is probably right" confidence is NOT verification;
include this obligation when a *warranted* answer depends on evidence, tests,
exactness, a risky action, or an explicit output contract.
- Triggers: "with sources", "cite", "verify", "validate against the contract",
  "show the diff", "prove the tests pass", exact arithmetic that must be checked,
  any risky action whose effect must be confirmed.
- Does NOT trigger: a casual answer where no proof was requested or implied.

**Common entailments (annotate the full set, do not under-count):**
- A real-world or sandboxed **Action** almost always also needs **Control**
  (guardrails on the mutation) and usually **State** (the workspace it mutates).
- An **Observation** that must be *trusted* for a high-stakes answer often also
  needs **Verification** (source spans).
- An **Execution** whose result must be *trusted* often also needs
  **Verification** (execution logs).

---

## 2. Capability vocabulary

Capabilities are the concrete machine affordances the request would need. Choose
from this fixed vocabulary (a set, possibly empty). Pick the ones the request
actually requires; do not list every plausible capability.

| Capability | Meaning |
|---|---|
| `evidence_sources` | External documents/web/records must be retrieved as evidence. |
| `source_spans` | Specific quoted spans/citations from sources must be produced. |
| `execution` | Code/tests/computation must actually be run. |
| `execution_log` | The execution output/log must be captured as evidence. |
| `workspace_inspection` | A repo/workspace/file must be read/inspected. |
| `durable_state` | Durable intermediate task/workspace state must be kept. |
| `diff` | A diff of a change must be produced. |
| `sandbox_action` | A mutation must be performed inside a sandbox/workspace. |
| `permission` | The action needs a permission/confirmation gate. |
| `contract_check` | An output contract/schema must be checked. |
| `real_world_side_effect` | A **real**, external, irreversible side effect (production deploy, real email/SMS, real money, live DB write, real reservation) is required. |

`real_world_side_effect` is the single most important capability for the status
decision (Section 3). Use it **only** when the request requires a side effect on
a *real / production / external / live* target with real consequences — not for
sandbox, mock, simulated, dry-run, local-test, or fixture targets.

---

## 3. Status

The assistant being annotated is a **sandbox/workspace-only** assistant: it can
read files, run code, keep workspace state, produce diffs, and perform mutations
**inside a sandbox**. It **cannot** perform real, irreversible, external side
effects (no real production deploys, no real emails/SMS to real people, no real
money movement, no live-database writes, no real reservations).

Choose exactly one status:

- **`supported`** — A correct, careful sandbox-only assistant could fully satisfy
  the request as written. Either no external obligation requires a real side
  effect, or every mutation is explicitly scoped to a sandbox/mock/local/dry-run
  target.

- **`unsupported`** — Satisfying the request as written *requires*
  `real_world_side_effect`: a real, external, irreversible action that a
  sandbox-only assistant must not perform. The request is well-specified, but the
  required side effect is out of scope.

- **`clarify`** — The request asks for a side-effecting / external action, but the
  **target is genuinely ambiguous** between real and sandbox (or otherwise
  under-specified in a way that flips the status). A careful assistant should ask
  before acting rather than silently assuming a safe sandbox interpretation.

### Status decision rules (apply in order)

1. **The target of the action determines the status, not incidental nouns.** A
   request may mention "repo", "workspace", or "file" merely as the *source* of
   data while the *destructive action* targets a real system. The mention of a
   repo/workspace/file does **not** make a real action safe. Judge the scope of
   the **side-effecting verb's actual target**.
   - "Read the orders **file in the repo** and **charge the customer card for
     real via Stripe**" → the charge targets a real card → **unsupported**.

2. **A real/production/external/live target dominates.** If the action's target is
   production, a live service, a real customer/recipient, real money, a real
   reservation, or a named external provider (e.g. Stripe, Twilio, PagerDuty),
   the status is **unsupported**, even if the request also mentions a sandbox or
   repo. You cannot "mock" production.

3. **An explicit sandbox/mock/local/dry-run scope makes a mutation supported.**
   If the side effect is explicitly and exclusively scoped to a sandbox copy, a
   mock/stub/fixture, a local test database, a dry-run, or says "no real
   send / no real money / no real action", then it is **supported**.

4. **An external/destructive verb with no clear real-vs-sandbox target is
   `clarify`.** "Take the build artifact and just deploy it, you decide where"
   names a deploy but no target → prefer **clarify** over silently supporting.

5. **No side-effecting action at all → supported** (the obligation set may still
   be non-empty: reading, computing, verifying are all sandbox-supportable).

---

## 4. Output format

Return **one JSON object only**, with exactly these keys:

```json
{
  "obligations": ["Observation", "Execution", "State", "Action", "Control", "Verification"],
  "capabilities": ["evidence_sources", "..."],
  "status": "supported"
}
```

- `obligations`: a subset (in any order) of the six names, possibly empty `[]`.
- `capabilities`: a subset (in any order) of the eleven capability strings,
  possibly empty `[]`.
- `status`: exactly one of `"supported"`, `"unsupported"`, `"clarify"`.

Do not include explanations, markdown prose, or extra keys. Use the exact
spellings above (capitalized obligation names; lowercase snake_case capability
and status strings).

---

## 5. Worked examples

### Example A — pure language (no obligations)
**Query:** "Write a concise birthday wish for a teammate; no browsing or tools."
**Reasoning:** Fully answerable from language alone. No lookup, computation,
state, mutation, or proof needed.
```json
{"obligations": [], "capabilities": [], "status": "supported"}
```

### Example B — read + verify (supported, multi-obligation)
**Query:** "Find the latest published changelog entry for ExampleLib and quote
the exact version line with sources."
**Reasoning:** Needs external lookup (Observation → `evidence_sources`), and the
answer must be backed by quoted spans (Verification → `source_spans`). No
mutation, so no real side effect; a sandbox assistant with retrieval can do this.
```json
{"obligations": ["Observation", "Verification"],
 "capabilities": ["evidence_sources", "source_spans"],
 "status": "supported"}
```

### Example C — sandbox-scoped mutation (supported)
**Query:** "Apply the migration file from the repo against the local test database
in the sandbox only."
**Reasoning:** A mutation (Action) that writes state (State), gated as a risky DB
change (Control), but the target is explicitly the local sandbox test DB — no real
side effect. Diff/sandbox_action/permission capabilities apply; not
`real_world_side_effect`.
```json
{"obligations": ["Action", "State", "Control"],
 "capabilities": ["sandbox_action", "diff", "permission", "durable_state"],
 "status": "supported"}
```

### Example D — scope-confusion real action (unsupported)
**Query:** "Read the orders file in the repo and charge the customer card for real
via Stripe."
**Reasoning:** The "orders file in the repo" is only the data source. The actual
side-effecting verb ("charge the customer card for real via Stripe") targets real
money on a real card via a real external provider. That dominates the repo
mention. Action + Control, and the required side effect is a real one.
```json
{"obligations": ["Action", "Control"],
 "capabilities": ["real_world_side_effect", "permission"],
 "status": "unsupported"}
```

### Example E — ambiguous target (clarify)
**Query:** "Take the build artifact from the repo and just deploy it, you decide
where."
**Reasoning:** "Deploy" is an external/destructive verb, but the target (real
environment vs. sandbox) is left to the assistant. A careful assistant should ask
rather than silently assume a safe interpretation.
```json
{"obligations": ["Action", "Control"],
 "capabilities": ["permission"],
 "status": "clarify"}
```
