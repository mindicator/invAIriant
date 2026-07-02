# What a normal AI reviewer missed — refund-agent PR #218

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. The left column is the kind of
> comment a generic AI PR reviewer produces on this diff. The right column is
> what the oracle-boundary and leveson lenses caught. The point is not that the
> left column is wrong — it is that it is about the wrong thing.

## The one-line version

A generic reviewer graded the **prose around the money movement** and approved.
The lens audited **the money movement itself** and blocked the merge. Same diff.

## Side by side

| Generic AI reviewer said (surface / style) | The lens caught (the real defect) |
|---|---|
| "Nice — the prompt now returns structured JSON with an explicit schema. Much cleaner than free-text parsing." | The schema exists **in the prompt**, not **in the code**. Nothing validates the returned `amount_cents` against that schema, the order total, or a cap before it hits `refund()`. The contract is aspirational. (**RB-001, S0**) |
| "Good defensive touch adding a retry on `JSONDecodeError`." | The retry handles *malformed* output. It does nothing about *well-formed but wrong* output — a clean JSON `{"refund": true, "amount_cents": 999999}` sails straight through to the provider. The dangerous path is the happy path. (**RB-001**) |
| "Typed `RefundResult` return value — good API hygiene." | The return type is clean; the **input to `refund()`** is not. Style at the boundary says nothing about what crosses it. (obs O-1, parnas) |
| "LGTM, tests pass." | The single test mocks a well-behaved model returning a within-total amount. There is **no test** for an over-total, negative, or injected amount — so "tests pass" certifies only the case that was never in doubt. (**RB-001** missing-test evidence) |
| (silent — no comment on authority) | The executing path has **no cap, no rate limit, and no human approve step**, which `docs/agent-decision-boundary.md:22` explicitly requires. One injected ticket is unbounded. (**RB-002, S1**) |
| (silent — no comment on the boundary doc) | `docs/agent-decision-boundary.md:14` lists "issuing or executing a refund" as **deterministic / human-owned**. The PR moves it to the model. The reviewer never read the boundary doc against the code. (**RB-001** doc/code contradiction) |

## Why the generic reviewer misses this every time

A style-and-correctness reviewer optimizes for *does this code do what it says
cleanly?* It reads the diff, not the **system property** the diff changes. It
has no concept of a *decision boundary* — a written list of what the model may
decide and what must stay deterministic — so it cannot notice that this PR
silently moves refund authority across that line. It sees a retry and calls it
"defensive"; it cannot see that defense against malformed output is not defense
against wrong output when the output moves money.

The oracle-boundary lens carries exactly one non-negotiable question that the
generic reviewer does not have:

> **Can model output reach a production mutation, shell command, or SQL
> without passing through deterministic validation?**

Here the mutation is a refund. The answer is yes. That is an S0 regardless of
how clean the prompt is — and the leveson lens then asks the second question
the reviewer also lacks: *in which states is this action unsafe, and what
prevents it being issued there?* Nothing does. That is the S1.

## The fix the lens implies (and the reviewer never asked for)

Model **proposes**, deterministic code **disposes**:

1. Parse the model output into a typed `RefundDecision`; reject anything
   nonconforming as a typed `ModelRejected` with a safe default.
2. Clamp `amount_cents` to the remaining refundable balance on the charge.
3. Enforce a per-ticket and per-day cap and an allowlist of reason codes — in
   code, not in the prompt.
4. Require a human approve step above a low auto-approve threshold; log every
   action for the operator; ship a kill switch.
5. Test the over-total, negative, non-JSON, and injected-reason paths.

None of that changes the prompt the reviewer praised. All of it is what stands
between a hallucinated number and a customer's bank account.
