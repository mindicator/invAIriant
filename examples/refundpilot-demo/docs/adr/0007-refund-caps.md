# ADR-0007: Refund auto-approval cap

## Status

Accepted — 2026-05-12

## Context

`refund_agent.py` lets an LLM adjudicate customer refunds and issue the payout
autonomously. The model's output is **advisory and untrusted**: a prompt
injection in the order notes, or an ordinary hallucination, can make it return
an arbitrary `amount`. Money leaving the system is the highest-value asset we
have.

## Decision

The agent may auto-approve and issue a refund **only up to `MAX_AUTO_REFUND_USD`
($50)**. Any refund **above the cap MUST be routed to a human reviewer** — the
agent must not issue it autonomously.

The cap is a **hard boundary on automation authority**, enforced on the
executing path in `handle_refund` (`refund_agent.py`): the model's recommended
`amount` is advisory; the cap is what actually gates `issue_payout`. There is no
server-side cap in the payments provider, so this is the *only* enforcement
point.

## Consequences

- A refund over $50 blocks on a human; SLAs account for that.
- The cap constant lives with the enforcement so they cannot drift apart.
