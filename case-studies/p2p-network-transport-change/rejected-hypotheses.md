# Rejected hypotheses — overlaynet PR #351

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. Kept, not deleted: a refuted worry
> is still a record of where the audit looked. Evidence-first throughout.

## H1 — "Removing `ApplyOrdered` means messages can now be lost entirely, not just reordered"

**The instinct.** The old path buffered and reordered by `Seq`. Ripping it out
looks like it might also remove the machinery that recovers a dropped message —
in which case the defect would be silent data *loss*, not just corruption on
reorder.

**Refuted by reading the resend path.** The transport still acknowledges and the
sender still retransmits on timeout: `transport/apply.go:51-57` calls
`resend(msg)`, and the ack/retransmit loop lives at
`transport/session.go:120-138`. So a lost message is recovered by retransmit. The
actual defect is the *opposite* of loss — recovery re-applies the update with no
`Seq` guard, so a retransmit that races its original applies twice (**PT-001**).
The hypothesis pointed at the right file and drew the wrong conclusion; the real
bug is double-apply, and it is already captured inside PT-001 rather than filed
as a separate loss finding.

## H2 — "The magic constant leaks the peer's identity to a passive observer"

**The instinct.** A fixed marker at the start of every session smells like it
might encode or expose *who* is connecting — an unlinkability problem distinct
from the blocking problem.

**Rejected as a separate finding.** `sessionMagic` at `transport/handshake.go:23`
is a single constant, byte-for-byte identical for every peer. It identifies the
*protocol*, not the *peer* — so it is a distinguishability/blocking problem
(**PT-002**), not a per-peer unlinkability leak. There *is* a real adjacent
concern — the peer id travels inside `handshakeHeader` after the marker but
before encryption — but the fix for PT-002 ("the first bytes must be
pseudorandom, derived from the negotiated key") already moves the whole preamble,
id included, behind key-derived framing. Filing a separate unlinkability finding
would double-charge the one cleartext-handshake defect. Recorded here so the peer
id exposure is not forgotten when PT-002 is fixed.

## H3 — "`binary.BigEndian` header write is a cross-architecture portability bug"

**The instinct.** Hand-rolled binary framing across heterogeneous peers is a
classic endianness trap: if writer and reader disagree on byte order, the header
decodes to garbage.

**Rejected — no mismatch exists.** Byte order is explicit and consistent on both
sides: `transport/handshake.go:30` writes with `binary.BigEndian` and
`transport/read.go:41` reads with `binary.BigEndian`. There is no place where one
side assumes native order. With no locator for an actual inconsistency, there is
no finding — a real-sounding portability worry with zero supporting evidence
stays out of the report.

---

**Why keep these.** The defects that matter are PT-001 (the code assumes a
well-ordered, at-most-once world and nothing enforces it) and PT-002 (a cleartext
marker turns "indistinguishable" into "blockable with one rule"). The three
rejected hypotheses are the kinds of things these lenses train you to suspect —
message loss, identity leakage, framing bugs — and each was refuted by reading a
specific file. Looking widely and filing narrowly is the whole discipline.
