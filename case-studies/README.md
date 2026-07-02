# Case Studies

A case study shows invAIriant applied to a real code change, end to end:

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

| Case | Kind | Lenses | The miss |
|---|---|---|---|
| [`persistent-mesh-transport`](persistent-mesh-transport/) | **real diff** | cormen · security-threat · parnas · network-persistence | a documented "fail-closed" fallback actually ships a cert/SNI active-probe tell |
| [`ai-agent-refund-bot`](ai-agent-refund-bot/) | illustrative | oracle-boundary · leveson | model output moves customer money with no cap or validation |
| [`generated-typescript-api`](generated-typescript-api/) | illustrative | generated-surface-area · review-bottleneck | one near-duplicate handler silently drops an authz check |
| [`p2p-network-transport-change`](p2p-network-transport-change/) | illustrative | lamport · network-persistence | an ordering assumption + a distinguishable handshake fingerprint |

**Real vs illustrative.** `persistent-mesh-transport` is built from an actual diff and a
real finding in a production blocking-resistance project; its most
operationally-sensitive specifics are lightly abstracted (the architectural
lesson is the point, not a probe playbook). The other three are
**synthesized-but-realistic** — clearly labelled at the top of each — exercising
the AI-era and systems lenses on scenarios that recur constantly in
AI-assisted codebases.

Each case directory contains: `README.md` (narrative), `diff.*` (the change),
`invairiant.config.yml` (scope), `report.json` + `report.md` (the audit),
`rejected-hypotheses.md` (kept), and `ai-reviewer-miss.md` (the side-by-side).
