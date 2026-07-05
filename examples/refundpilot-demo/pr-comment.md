# invAIriant PR Audit — refundpilot (ADR-0007 ↔ code)

**Verdict:** fail
**Audited:** handle_refund in refund_agent.py against ADR-0007 (refund au · **Lenses:** oracle-boundary, security-threat, turing, leveson

## Findings

**RFP-001 (S1, oracle-boundary, confidence high)** — The $50 auto-refund cap is checked but not enforced: handle_refund logs a warning when the model's amount exceeds MAX_AUTO_REFUND_USD, then issues the payout unconditionally. The agent can autonomously pay out any amount the model returns — the exact boundary ADR-0007 says must gate the executing path.
- Evidence: `refund_agent.py:29-30` — `if rec["amount"] > MAX_AUTO_REFUND_USD: log.warning(...)` — the over-cap branch only logs; no return, no human-routing
- Risk: A prompt injection in order data, or an ordinary model hallucination, yields an arbitrary `amount` that is paid out with no cap and no human — direct, unbounded loss of customer funds. The warning log makes it look handled in review and in dashboards.
- Fix: Gate issue_payout on the cap: for amount > MAX_AUTO_REFUND_USD, route to human review and return — do not call issue_payout. Add a test that a $5000 model-approved refund does NOT pay out. Treat the model `amount` as advisory, the cap as the enforced bound.

## Conditions

1. Gate issue_payout on MAX_AUTO_REFUND_USD; route over-cap refunds to a human and return; add a 'model-approved $5000 refund does not pay out' test (agent team)

## Observations / Hypotheses (non-blocking)

- llm.py returns the model's JSON parsed and trusted as-is; the whole design treats an advisory, injectable input as authority on the money-moving path.
- Rejected hypothesis: Prompt injection via order data could exfiltrate customer PII into the model prompt. — the prompt at refund_agent.py:20-22 interpolates only order.id and order.total — no customer PII or free-text notes are read into it. No evidence, so not a finding.

