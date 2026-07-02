# invAIriant Audit Report — refund-agent PR #218

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional project and PR; all paths, line
> numbers, and excerpts are invented. The structure and rule applications are
> the point. Machine-readable twin: [`report.json`](./report.json).

- **Date:** 2026-07-02
- **Audit type:** pr
- **Project / commit range:** refund-agent · `main..c7d1e9a` (`feat/agent-refund-e2e`)
- **Participants:** claude-agent (lens auditor: oracle-boundary, leveson,
  parnas, turing), claude-agent-2 (evidence verifier)
- **Config:** `invairiant.config.yml` (this directory)

## Scope

PR #218, which changes `agent/refund_tool.py` from drafting a reply for human
review into deciding **and executing** refunds against the payment provider in
one pass. Audited against `docs/agent-decision-boundary.md` and
`docs/ARCHITECTURE.md`. **Out of scope:** the chat/LLM transport, the payments
SDK internals, and unrelated ticket-triage code.

## Executive Summary

PR #218 turns the support agent from a drafting assistant into an executor of
refunds, and does it by passing the model's chosen amount straight into the
payment provider with no deterministic validation between them (**RB-001, S0
`UNVALIDATED_ORACLE_OUTPUT`**). The decision-boundary doc reserves refund
execution for deterministic, human-owned code and requires a human approve
step; the code violates both. **RB-002 (S1)** compounds it: the executing path
has no per-ticket cap, no rate limit, and no approval gate, so one hallucinated
or injected ticket is unbounded. Prompt clarity and error handling are fine and
irrelevant to the verdict.

**Verdict:** fail — blocked on RB-001; RB-002 blocking before this path ships.

## Lens Scores

| Pack | Lens | Score | Verdict |
|---|---|---:|---|
| ai-generated-code | oracle-boundary | 2 | model `amount_cents` flows directly into a money-movement call with no bound/allowlist between model and provider (RB-001) |
| security-safety | leveson | 3 | execute action unsafe in most states; no cap, no approval in the executing path, no reversibility bound (RB-002) |
| core | parnas | 6 | the tool boundary itself is clean; the defect is what crosses it, not coupling (obs O-1) |
| core | turing | 3 | decode fallback retries once then raises; the uncertain/garbage path has no typed outcome (obs O-2) |

## Critical Findings

### RB-001 — Refund amount taken straight from model output, executed unvalidated (S0, oracle-boundary, confidence: high)

- **Claim:** The refund amount comes straight from the LLM's JSON output and is
  passed to the provider's refund call with no schema validation, bounds check,
  or allowlist between the model and the money movement.
- **Evidence:**
  - `file_lines` — `agent/refund_tool.py:41-52` @ c7d1e9a:
    `StripeClient().refund(..., amount_cents=decision["amount_cents"], ...)`;
    `decision["amount_cents"]` is parsed from raw model text and used unmodified
    — no clamp to order total, no per-ticket cap, no reason allowlist.
  - `diff_hunk` — the change replaces `draft_refund_reply` (human executes) with
    `decide_and_refund` (agent executes) and wires model output into `refund()`.
  - `doc_code_contradiction` — `docs/agent-decision-boundary.md:14` lists
    "issuing or executing a refund" as deterministic / human-owned; the code
    executes it directly from model output.
  - `missing_test` — `tests/agent/test_refund_tool.py` covers only a well-formed,
    within-total decision; no over-total, negative, post-retry non-JSON, or
    hostile-reason case.
- **Risk:** A model regression, a prompt injected into a ticket, or an ordinary
  hallucination moves real customer funds in an amount the model chose. The
  effective refund-authority contract is whatever the model emits per request.
- **Recommendation:** Insert a deterministic layer between model and provider:
  typed `RefundDecision`, reject nonconforming output as a typed
  `ModelRejected` outcome, clamp to the remaining refundable balance, enforce a
  per-ticket/per-day cap, allowlist reason codes. Only a validated, bounded
  decision may reach `refund()`. Add hostile/malformed model-output tests.
- **Category:** UNVALIDATED_ORACLE_OUTPUT
- **Owner / deadline:** agent team / 2026-07-07 (blocking merge)

## High Findings

### RB-002 — Unbounded refund authority, no human approval in the executing path (S1, leveson, confidence: high)

- **Claim:** The refund execution has no bounded authority and no human
  confirmation on the executing path: nothing in code limits the amount, rate,
  or blast radius, and the action fires unconditionally once the model says
  `refund=true`.
- **Evidence:**
  - `file_lines` — `agent/refund_tool.py:36-52` @ c7d1e9a: the `refund=true`
    branch goes straight to `refund()` with no approval gate, per-window limit,
    or check of order state (already refunded, disputed).
  - `doc_code_contradiction` — `docs/agent-decision-boundary.md:22` requires "a
    human approve step in the console before execution"; the executing path has
    none.
  - `missing_test` — no test refuses an over-cap or already-refunded refund; no
    approval/kill-switch test because no such control exists.
- **Risk:** One bad decision is unbounded — no cap, no rate limit, no
  reversibility check — so a single injected or hallucinated ticket can drain
  funds up to the full charge on every order the agent touches, with no operator
  interruption in the loop.
- **Recommendation:** Enforce refund authority in code: hard per-ticket and
  per-window caps, a refundable/not-disputed check, and a human approve step
  above a low auto-approve threshold; add an operator action log and a kill
  switch. Cover cap / already-refunded / above-threshold paths with tests.
- **Category:** UNBOUNDED_AUTHORITY
- **Owner / deadline:** agent team / before this path ships

## Notes / Observations

- **O-1 (parnas):** The tool boundary is clean — typed `Ticket`/`Order` in,
  typed `RefundResult` out — so the fix is a validation+authority layer inside
  the tool, not a re-plumbing.
- **O-2 (oracle-boundary):** Model decisions are not replayable: raw response,
  prompt version, and sampling parameters are not persisted per refund. Debt,
  separate from RB-001.

## Unsupported Hypotheses

| Hypothesis | Proposed by | Rejection / status |
|---|---|---|
| The single JSON-decode retry can loop forever and hang the worker | claude-agent (turing pass) | **Rejected:** the fallback retries exactly once then lets `json.loads` raise (`agent/refund_tool.py:22-33`) — an unhandled-exception path, not an unbounded loop; folded into RB-001's missing-test evidence |
| `idempotency_key=None` risks double refunds on client retry | claude-agent (lamport pass) | **Demoted to observation:** the tool is called once per ticket from a synchronous handler with no retry wrapper (`agent/worker.py:88`); revisit if moved behind a retrying queue |
| The prompt change leaks internal reasoning to the customer | claude-agent (oracle-boundary pass) | **Rejected:** the executing path returns a `RefundResult`, not the model prose (`agent/refund_tool.py:44-52`) |

## Weakest Lens

**oracle-boundary (2/10).** The model became the decision-maker for money
movement with no deterministic contract wrapping the crossing (RB-001) — the
defining failure mode of this lens. A critical lens this far below threshold,
tied to a concrete financial risk asset, yields S0.

## Required Actions Before Merge

1. **RB-001** — deterministic validation+bounds layer between model output and
   the refund call; hostile/malformed model-output tests. Owner agent team, due
   2026-07-07. **Blocking merge.**
2. **RB-002** — enforced authority bounds + human approve step + action
   log/kill switch; cap/already-refunded/approval tests. Owner agent team.
   Blocking before this path ships.
