# Case Studies

A case study shows invAIriant applied to a code change, end to end:

```
the diff → selected lenses → candidate findings → rejected hypotheses (kept)
        → verified findings → final report → what a normal AI reviewer missed
```

The last line is the point. A generic AI PR reviewer comments on style,
naming, and the happy path. invAIriant is built to catch the *architectural*
defect a diff-level reviewer waves through — and to make that catch
evidence-bound and auditable, not a vibe.

Every finding in every case study cites concrete evidence. Reports are
schema-valid (`invairiant validate-report`) and gate-able (`invairiant
ci-gate`).

| Case | Lenses | The miss |
|---|---|---|
| [`persistent-mesh-transport`](persistent-mesh-transport/) | cormen · security-threat · parnas · network-persistence | a documented "fail-closed" fallback actually ships a cert/SNI active-probe tell |
| [`ai-agent-refund-bot`](ai-agent-refund-bot/) | oracle-boundary · leveson | model output moves customer money with no cap or validation |
| [`generated-typescript-api`](generated-typescript-api/) | generated-surface-area · review-bottleneck | one near-duplicate handler silently drops an authz check |
| [`p2p-network-transport-change`](p2p-network-transport-change/) | lamport · network-persistence | an ordering assumption + a distinguishable handshake fingerprint |

All four are **illustrative / synthesized** — clearly labelled at the top of
each — modelling real, recurring defect classes in AI-assisted codebases
without naming any project. `persistent-mesh-transport` is drawn from a
real, *fixed* defect pattern; the rest exercise the AI-era and systems lenses
on scenarios that come up constantly.

Each case directory contains: `README.md` (narrative), `diff.*` (the change),
`invairiant.config.yml` (scope), `report.json` + `report.md` (the audit),
`rejected-hypotheses.md` (kept), and `ai-reviewer-miss.md` (the side-by-side).
