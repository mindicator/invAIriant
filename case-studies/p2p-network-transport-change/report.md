# invAIriant Audit Report — overlaynet PR #351

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional project and PR; all paths, line
> numbers, byte constants, and doc references are invented. Machine-readable
> twin: [`report.json`](./report.json).

- **Date:** 2026-07-02
- **Audit type:** pr
- **Project / commit range:** overlaynet · `main..f18c07d` (`feat/transport-handshake-v1`)
- **Participants:** claude-agent (lens auditor: lamport, network-persistence,
  parnas, turing), claude-agent-2 (evidence verifier)
- **Config:** `invairiant.config.yml` (this directory)

## Scope

PR #351, which adds a session handshake with a fixed magic preamble to
`transport/handshake.go` and changes `transport/apply.go` to apply incoming
state updates in arrival order, re-applying on retransmit. Audited against
`docs/threat-model.md` and `docs/design/replication.md`. **Out of scope:** the
cryptographic key exchange (`transport/noise.go`), peer discovery, and the state
CRDT internals.

## Executive Summary

PR #351 makes two changes that each defeat a core property of the overlay.
First, `transport/apply.go` now applies state updates in arrival order and
re-applies them on retransmit with no `Seq` check or dedup, so ordinary packet
reordering or a timeout race corrupts distributed state that cannot be rebuilt
from the stream (**PT-001, S1 `ORDERING_ASSUMPTION`**) — and `replication.md`
explicitly promises Seq-ordered, idempotent apply. Second, the new handshake
opens with a constant `OVRLY\x01` magic preamble in the clear, a stable
fingerprint a blocker blocks with one rule, while `threat-model.md` claims the
handshake is indistinguishable from TLS (**PT-002, S1
`DISTINGUISHABLE_TRANSPORT`**). The transport boundary is clean (parnas 7), but
two S1s block the merge.

**Verdict:** fail — blocked on PT-001 and PT-002.

## Lens Scores

| Pack | Lens | Score | Verdict |
|---|---|---:|---|
| systems | lamport | 3 | `Recv` applies in arrival order with no Seq check, `onTimeout` re-applies on retransmit with no dedup; reorder/duplicate corrupts state (PT-001) |
| domain | network-persistence | 3 | handshake opens with a constant 6-byte magic preamble + fixed fields — a stable fingerprint matchable on the first packet (PT-002) |
| core | parnas | 7 | the transport/state boundary is clean; both defects live inside the transport module (obs O-1) |
| core | turing | 6 | the resend path is bounded (single resend, no loop) — a correctness defect, not liveness (obs O-2) |

## High Findings

### PT-001 — Arrival-order apply + retransmit re-apply corrupts distributed state (S1, lamport, confidence: high)

- **Claim:** The receive path assumes messages arrive in production order and at
  most once: `Recv` applies in arrival order without a sequence check, and
  `onTimeout` re-applies on retransmit with no dedup, so reordering or a
  retransmit-plus-original double-applies state.
- **Evidence:**
  - `file_lines` — `transport/apply.go:44-49` @ f18c07d: `Recv` calls
    `s.state.Apply(msg)` with comment `assumes in-order arrival`; the prior
    `ApplyOrdered(msg)` that reordered by `msg.Seq` was removed.
  - `file_lines` — `transport/apply.go:51-57` @ f18c07d: `onTimeout` calls
    `s.state.Apply(msg)` then `resend(msg)`; if the original also lands, `Apply`
    runs twice — no processed-`Seq` guard.
  - `diff_hunk` — removal of `ApplyOrdered` in favor of arrival-order `Apply`.
  - `doc_code_contradiction` — `docs/design/replication.md:37`: "state updates
    are applied in Seq order and idempotent under retransmit" — contradicted.
  - `missing_test` — `transport/apply_test.go` covers only in-order,
    single-delivery; no out-of-order or duplicate-Seq case.
- **Risk:** Two peers are already a distributed system: network reordering or a
  timeout-triggered retransmit racing its original diverges peer state and cannot
  be reconciled from the stream. Under real packet loss — the normal case here —
  state silently corrupts.
- **Recommendation:** Buffer/apply by `msg.Seq` (reject or hold out-of-order);
  guard `Apply` with a processed-`Seq` set so retransmit-plus-original is a
  second-delivery no-op; add out-of-order and duplicate-delivery tests.
- **Category:** ORDERING_ASSUMPTION
- **Owner / deadline:** transport team / 2026-07-08 (blocking merge)

### PT-002 — Cleartext magic preamble gives the transport a blockable fingerprint (S1, network-persistence, confidence: high)

- **Claim:** The handshake begins with a constant 6-byte magic preamble followed
  by fixed-size, fixed-order fields, giving the transport a stable per-session
  fingerprint a passive DPI classifier matches on the first packet — obfuscated,
  not indistinguishable.
- **Evidence:**
  - `file_lines` — `transport/handshake.go:23-31` @ f18c07d:
    `sessionMagic = []byte{0x4F,0x56,0x52,0x4C,0x59,0x01}` (`OVRLY\x01`) written
    first, before the TLS-looking wrapper, then a fixed `handshakeHeader`.
  - `diff_hunk` — the added `sessionMagic` constant and its `writeHandshake`.
  - `doc_code_contradiction` — `docs/threat-model.md:28`: "statistically
    indistinguishable from a standard TLS handshake and survives active probing"
    — a fixed cleartext constant is a trivially matchable signature.
  - `missing_test` — no fingerprint/indistinguishability test compares the
    handshake byte distribution against a real TLS ClientHello.
- **Risk:** A blocker blocks the entire overlay on the constant `OVRLY\x01`
  preamble with one rule and near-zero false positives — reachability collapses
  to a single string match, and the threat-model claim is false.
- **Recommendation:** Remove the cleartext magic; derive session framing from the
  negotiated key so the first bytes are pseudorandom and match TLS record
  framing; add a fingerprint test vs a reference ClientHello; correct
  `threat-model.md` to the real guarantee.
- **Category:** DISTINGUISHABLE_TRANSPORT
- **Owner / deadline:** transport team / 2026-07-08 (blocking merge)

## Notes / Observations

- **O-1 (parnas):** The transport/state boundary is clean; both defects live
  inside the transport module and are fixable without touching the CRDT
  interface.
- **O-2 (turing):** The resend path is bounded (single resend, no loop), so
  PT-001 is state corruption, not a liveness defect.

## Unsupported Hypotheses

| Hypothesis | Proposed by | Rejection / status |
|---|---|---|
| Removing `ApplyOrdered` means messages can now be lost entirely | claude-agent (lamport pass) | **Rejected:** the transport still acks and retransmits on timeout (`transport/session.go:120-138`), so loss is recovered; the defect is re-apply without a Seq guard (PT-001), not message loss |
| The magic constant leaks the peer's identity to a passive observer | claude-agent (network-persistence pass) | **Rejected as separate finding:** `sessionMagic` is identical for every peer (`transport/handshake.go:23`) — it identifies the protocol, not the peer; folded into PT-002's "first bytes must be pseudorandom" fix |
| `binary.BigEndian` header write is a cross-architecture portability bug | claude-agent (parnas pass) | **Rejected:** byte order is explicit and consistent on write and read (`transport/handshake.go:30`, `transport/read.go:41`); no mismatch |

## Weakest Lens

**lamport (3/10).** The receive path assumes a single well-ordered, at-most-once
world — arrival-order apply and retransmit re-apply — with nothing enforcing it
(PT-001). That is the defining failure mode of this lens. A critical lens this
low, tied to distributed-state-integrity risk, yields S1.

## Required Actions Before Merge

1. **PT-001** — apply by `msg.Seq` and dedup on a processed-`Seq` set; add
   out-of-order and duplicate-delivery tests. Owner transport team, due
   2026-07-08. **Blocking merge.**
2. **PT-002** — remove the cleartext preamble; pseudorandom key-derived framing;
   fingerprint test; correct the threat model. Owner transport team, due
   2026-07-08. **Blocking merge.**
