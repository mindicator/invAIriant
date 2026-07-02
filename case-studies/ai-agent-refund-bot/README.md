# Case study — AI support agent that decides refunds

> **ILLUSTRATIVE / SYNTHESIZED.** This case study is fictional. The project
> `refund-agent`, the PR, every file path, line number, and log excerpt are
> invented to demonstrate how invAIriant applies to an agent-executed
> money-movement change. It is not a report on any real system.

## Context

`refund-agent` is an LLM support agent for a subscription product. Until this
PR, it was a drafting assistant: it read a customer ticket and produced a
recommendation and reply text; a human agent then approved and executed any
refund from the support console. The decision boundary was written down —
`docs/agent-decision-boundary.md` reserves "issuing or executing a refund" for
deterministic, human-owned code, and requires a human approve step before any
money moves.

**Risk assets:** customer funds, refund authority, fraud exposure, financial
reconciliation integrity.

## The change (PR #218)

The PR retitles the tool from `draft_refund_reply` to `decide_and_refund` and
lets the agent execute end-to-end. The model is now asked to return structured
JSON — `{"refund": bool, "amount_cents": int, "reason": str}` — and the code
passes `decision["amount_cents"]` **straight into** the payment provider's
refund call. See [`diff.md`](./diff.md). The prompt is clean, the JSON contract
is explicit, and there is even a decode-failure retry. It looks like careful
work.

## The lenses

Two mandatory critical lenses drive this audit:

- **oracle-boundary** (`ai-generated-code`) — what the model may decide, and
  what deterministic code must own. Its central demand: every model output that
  can reach state passes through validation — schema, allowlist, bounds —
  before it touches anything.
- **leveson** (`security-safety`) — which control action is unsafe in which
  state, and what prevents it being issued there. For automation that moves
  money: bounded authority, execution-time preconditions, human override in the
  loop.

`parnas` and `turing` round out the mandatory set but are not where the defect
lives.

## The miss

A generic AI PR reviewer looked at PR #218 and **approved it with compliments**:
tidy prompt, explicit JSON schema, nice typed `RefundResult`, thoughtful retry
on malformed output. Every comment was about surface and style. All true. All
beside the point.

The oracle-boundary lens asked one question the style review never does: *does
model output reach a money movement without passing through deterministic
validation?* It does. `decision["amount_cents"]` — a number the model chose,
parsed from free text — is handed to `StripeClient().refund` with no clamp to
the order total, no per-ticket cap, and no allowlist. A hallucination, a model
regression, or a prompt injected into the ticket body moves real customer funds
in an amount the model picked.

That is **RB-001, S0 `UNVALIDATED_ORACLE_OUTPUT`** — and it blocks the merge.
The boundary doc explicitly forbids exactly this. **RB-002 (S1)** compounds it:
the executing path has no bounded authority — no cap, no rate limit, no human
approve step that the same doc requires — so one bad decision is unbounded.

The full side-by-side is in [`ai-reviewer-miss.md`](./ai-reviewer-miss.md).

## Files in this case

- [`diff.md`](./diff.md) — the change
- [`invairiant.config.yml`](./invairiant.config.yml) — scope + lens config
- [`report.json`](./report.json) — schema-valid audit report
- [`report.md`](./report.md) — human-readable report
- [`rejected-hypotheses.md`](./rejected-hypotheses.md) — refuted candidates, kept
- [`ai-reviewer-miss.md`](./ai-reviewer-miss.md) — style review vs. the lens
