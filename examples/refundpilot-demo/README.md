# refundpilot — a runnable invAIriant demo

A real, runnable audit that catches a real bug a normal review misses. Walkthrough
with the recording: [`../../docs/demo.md`](../../docs/demo.md).

**The bug.** `refundpilot` is an autonomous refund agent: an LLM decides refunds
and the code issues the payout. The $50 auto-approval cap is *checked* — the
over-cap branch logs a warning — but the next line issues the payout anyway. The
cap is **logged, not enforced.** A normal review sees the check and passes it.

**The catch.** `ADR-0007` calls that cap the *enforced* boundary on the
money-moving path. invAIriant reads the ADR, traces the executing path in
`refund_agent.py`, and files it as an **S1 with cited lines** — the warning at
lines 29–30, the unconditional payout at line 33. `ci-gate` exits 1: the merge is
blocked.

## Run it

```bash
pip install invairiant
cd examples/refundpilot-demo
./run-demo.sh                # collect → validate-report → ci-gate (real, colored output)
```

`report.json` is the agent's audit output (`/invairiant audit-adr`), shipped
here; `run-demo.sh` runs the deterministic CLI seatbelt around it. Regenerate the
recording with `vhs demo.tape` (needs [vhs](https://github.com/charmbracelet/vhs)).

## What's here

| file | what it is |
|---|---|
| `refund_agent.py` | the agent — the planted "cap checked but not enforced" bug |
| `payments.py`, `llm.py`, `obs.py` | stubs: no server-side cap; model output trusted as-is |
| `docs/adr/0007-refund-caps.md` | the ADR the code is supposed to enforce |
| `invairiant.config.yml` | project config (ai-agent-system; oracle-boundary mandatory) |
| `report.json` | the audit output — S1 `RFP-001` + cited evidence + a rejected hypothesis |
| `pr-comment.md` | the paste-ready PR comment `render-comment` produces |
| `run-demo.sh`, `demo.tape` | run the flow / record the GIF |

A focused ADR audit: a few lenses, one verified S1, one rejected hypothesis.
No evidence, no finding, no lens theater. *This demo is intentionally small and
will grow.*
