# What a normal AI reviewer missed — overlaynet PR #351

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. Left column: the kind of comment a
> generic AI PR reviewer leaves on this diff. Right column: what the lamport and
> network-persistence lenses caught. The left column is not wrong — it grades the
> happy path, and both defects live off it.

## The one-line version

The generic reviewer checked that the code **works when the network behaves**.
The lenses checked what happens **when it doesn't** — reordering, retransmits, and
a blocker reading the first six bytes — which is the only regime that matters for
a P2P overlay.

## Side by side

| Generic AI reviewer said (surface / happy path) | The lens caught (the real defect) |
|---|---|
| "The message-apply path is simpler now — dropping the reorder buffer removes complexity." | The reorder buffer *was the invariant*. `apply.go:44-49` now applies in arrival order (comment: `assumes in-order arrival`); on a lossy overlay, reordering silently diverges peer state. Simpler and wrong. (**PT-001, S1**) |
| "Timeout handling looks right — it retransmits the message." | It also **re-applies** it: `onTimeout` calls `Apply(msg)` then `resend(msg)` with no `Seq` dedup (`apply.go:51-57`). If the original also lands, the update applies twice. (**PT-001**) |
| "Tests pass." | The tests deliver messages **in order, once** (`apply_test.go`). They exercise precisely the regime where the bug can't fire; there is no out-of-order or duplicate-delivery test. "Tests pass" certifies the happy path only. (**PT-001** missing-test) |
| "The handshake is clean and well-structured — nice fixed layout." | The fixed layout *is* the problem: a constant `OVRLY\x01` preamble (`handshake.go:23-31`) is a stable fingerprint a blocker matches on the first packet. "Well-structured" and "blockable" are the same property here. (**PT-002, S1**) |
| "Writing a magic number first is a reasonable framing choice." | For a persistent-mesh transport it is the opposite: the threat model (`threat-model.md:28`) claims indistinguishability from TLS, and a cleartext marker is a one-rule block with near-zero false positives. (**PT-002** doc/code contradiction) |
| (silent — no comment on the design docs) | Neither `replication.md:37` (Seq-ordered, idempotent) nor `threat-model.md:28` (TLS-indistinguishable) was read against the diff. Both are now false. (PT-001, PT-002) |

## Why the generic reviewer misses this every time

A happy-path reviewer evaluates the code against the **execution it can imagine**:
it traces a message that arrives once, in order, and a handshake that completes.
Both defects live in the executions it *doesn't* imagine — the reordered packet,
the retransmit that races its original, the blocker's classifier reading bytes it
never simulates. The reviewer has no model of "the network is adversarial and
unreliable," so it cannot miss what it never considered.

The lamport lens supplies that model as a standing assumption:

> **Any network effect can be duplicated by a retry, and events do not arrive in
> production order unless something enforces it.**

Applied to `apply.go`, that assumption immediately flags both the arrival-order
apply and the retransmit re-apply — the reviewer's "simpler" is the lens's
"unguarded."

The network-persistence lens supplies the adversary the reviewer lacks:

> **Is traffic statistically indistinguishable from legitimate HTTPS/QUIC, and
> does it survive active probing — or is it merely obfuscated?**

Applied to `handshake.go`, a constant in the clear fails on sight: obfuscated,
not indistinguishable.

## The fix each lens implies (and the reviewer never asked for)

**PT-001 (lamport):**
1. Apply by `msg.Seq` — buffer or reject out-of-order arrivals; never apply in
   raw arrival order.
2. Guard `Apply` with a processed-`Seq` set so a retransmit-plus-original is a
   no-op on the second delivery.
3. Add out-of-order and duplicate-delivery tests — exercise the regime the
   original tests skipped.

**PT-002 (network-persistence):**
1. Remove the cleartext `sessionMagic`; derive session framing from the
   negotiated key so the first bytes are pseudorandom.
2. Match legitimate TLS record framing rather than prefixing a marker.
3. Add a fingerprint test comparing the handshake against a reference TLS
   ClientHello and asserting no static preamble; correct the threat model.

The reviewer's praise for simplicity and clean structure survives none of these
without qualification — because simplicity that drops an invariant, and structure
that leaks a signature, are exactly what the two lenses exist to catch.
