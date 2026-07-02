# Rejected hypotheses — refund-agent PR #218

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. invAIriant keeps rejected
> hypotheses rather than deleting them: a reviewer's instinct is data, and
> recording why it was refuted stops the same guess re-appearing next audit.
> Every rejection here is evidence-first.

## H1 — "The JSON-decode retry can loop forever and hang the ticket worker"

**The instinct.** A retry inside a request path that talks to an unreliable
model is a classic liveness trap. Reviewer worry: if the model keeps returning
malformed JSON, does `decide_and_refund` spin?

**Refuted by reading the code.** `agent/refund_tool.py:22-33` retries exactly
once, then lets `json.loads` raise on the second failure:

```python
try:
    decision = json.loads(raw)
except json.JSONDecodeError:
    raw = chat(REFUND_PROMPT, ...)   # one retry, no loop
    decision = json.loads(raw)       # second failure propagates
```

There is no `while`, no unbounded recursion. This is an **unhandled-exception**
path, not an unbounded one. It matters — an uncaught exception on a money path
is sloppy — but it is captured under **RB-001's missing-test evidence** (the
garbage/timeout path has no typed outcome), not as a separate liveness finding.
Filing it twice would double-charge one defect.

## H2 — "`idempotency_key=None` risks double refunds on client retry"

**The instinct.** The refund call passes `idempotency_key=None`. A Lamport-lens
reflex fires: any network effect can be duplicated by a retry, and a double
refund is a real money bug.

**Demoted to observation, not a finding — for now.** The lens question is
*which writes can actually be duplicated on this path today?* The tool is
invoked once per ticket from a synchronous handler with no retry wrapper:
`agent/worker.py:88` calls it inside the request, and
`tests/agent/test_refund_tool.py:11-19` exercises that single call site.
At-least-once delivery is not in play on this code path, so there is no
duplicate to guard against yet. That makes it a real latent risk with **no
current evidence of duplication** — the definition of an observation. It is
recorded with a follow-up: promote to a finding the moment the tool is moved
behind a retrying queue or an at-least-once webhook. (Contrast the infra
example's CNV-042, where a genuine retry loop existed — there the missing
idempotency key was a verified S1.)

## H3 — "The prompt change leaks the model's internal reasoning to the customer"

**The instinct.** The old function returned the model's prose reply. The new
prompt asks for a `reason` field. Does that raw reasoning now get emailed to the
customer, exposing internal policy?

**Refuted by the return type.** `agent/refund_tool.py:44-52` shows the executing
path returns a typed `RefundResult(refunded=True, amount_cents=...)` — it no
longer returns the model prose at all. The `reason` string is passed to the
provider as refund metadata, not surfaced to the customer on this path. The
leak the hypothesis imagined does not exist in the changed code.

---

**Why keep these.** None of the three is the defect. The defect is that money
moves on unvalidated model output (RB-001) with unbounded authority (RB-002).
Recording the near-misses shows the audit looked hard in several directions and
did not pad the report with plausible-sounding items that the evidence does not
support — the "no evidence, no finding" rule, applied honestly.
