# Case study — a P2P transport change that breaks ordering and adds a fingerprint

> **ILLUSTRATIVE / SYNTHESIZED.** This case study is fictional. The project
> `overlaynet`, PR #351, and every file path, line number, byte constant, and
> doc reference are invented to demonstrate how invAIriant applies to a
> peer-to-peer transport change. It is not a report on any real system.

## Context

`overlaynet` is a peer-to-peer overlay network. Peers establish sessions over a
custom transport and exchange state-update messages. Two properties are core and
written down: **reachability under a blocking adversary**
(`docs/threat-model.md` claims session establishment is "statistically
indistinguishable from a standard TLS handshake") and **distributed state
integrity** (`docs/design/replication.md` promises updates are "applied in Seq
order and idempotent under retransmit").

**Risk assets:** reachability under blocking, distributed state integrity, peer
unlinkability, transport indistinguishability.

## The change (PR #351)

A +58 / −19 transport rework. Two moves, both innocent-looking. See
[`diff.md`](./diff.md):

1. **`transport/handshake.go`** — adds a session handshake that writes a
   constant 6-byte magic preamble (`OVRLY\x01`) as the first bytes of every
   session, then fixed-size, fixed-order header fields.
2. **`transport/apply.go`** — replaces the old `ApplyOrdered(msg)` (buffer and
   reorder by `Seq`) with `Apply(msg)` in **arrival order**, and re-applies on
   timeout retransmit with no dedup.

The handshake completes; the tests, which deliver messages in order, pass.

## The lenses

Two mandatory critical lenses drive this audit:

- **lamport** (`systems`) — time, ordering, and distributed state. Its premise:
  two communicating processes are already a distributed system, so every
  ordering and at-most-once assumption must be *written down and defended*, not
  hoped.
- **network-persistence** (`domain`) — reachability under adversarial pressure.
  Its bar: a transport must be *indistinguishable* from legitimate traffic and
  survive active probing, not merely "obfuscated."

`parnas` and `turing` round out the set — the boundary is clean and the resend
path is bounded, so they score well and stay out of the way.

## The miss

A generic AI PR reviewer read PR #351 and **okayed the happy path**: "handshake
looks well-structured, message apply is simpler now, tests pass." All true on
the path the tests exercise — which is the only path a happy-path reviewer
considers.

The lamport lens does not assume a well-ordered world; it *looks for the
assumption of one*. `apply.go` now applies in arrival order with an in-line
comment literally reading `assumes in-order arrival`, and `onTimeout` re-applies
on retransmit with no `Seq` guard. On this overlay — where packet loss and
reordering are the normal case — that silently corrupts state that cannot be
rebuilt from the stream, and `replication.md:37` promises the opposite. That is
**PT-001, S1 `ORDERING_ASSUMPTION`**.

The network-persistence lens does not ask "is the handshake tidy?"; it asks "is
it *indistinguishable*?" A constant `OVRLY\x01` in the clear is a stable
fingerprint a blocker blocks with a single rule — and `threat-model.md:28` claims
indistinguishability from TLS. That is **PT-002, S1 `DISTINGUISHABLE_TRANSPORT`**.

Two S1s, both blocking. The full side-by-side is in
[`ai-reviewer-miss.md`](./ai-reviewer-miss.md).

## Files in this case

- [`diff.md`](./diff.md) — the change
- [`invairiant.config.yml`](./invairiant.config.yml) — scope + lens config
- [`report.json`](./report.json) — schema-valid audit report
- [`report.md`](./report.md) — human-readable report
- [`rejected-hypotheses.md`](./rejected-hypotheses.md) — refuted candidates, kept
- [`ai-reviewer-miss.md`](./ai-reviewer-miss.md) — happy-path review vs. the lens
