# invAIriant Audit Report

- **Date:** 2026-07-03
- **Audit type:** full-scale
- **Scope:** The subsystem built across phases 1–6: `invairiant collect`, the audit-pr UX, `render-comment`, the `validate-report` semantic linter, committed audit memory (`record`/`history`), and the skill wiring. Applied to the framework's own repo. Out of scope: the lens library and docs prose (covered by self-audit #1).

## Executive Summary

The six-phase build holds together: the CLI stayed a narrow, judgment-free seatbelt (parnas 9, dijkstra 8), the semantic linter and now-idempotent record encode real invariants (cormen 8), and secrets/raw-evidence handling is sound (security-threat 8). No S0/S1. Three low-severity items remain: audit memory is CWD-relative (CLOSE-001, S3), the collect fallback is unbounded in files scanned (CLOSE-002, NOTE), and the CLI has CI smokes but no unit tests (CLOSE-003, NOTE). The record-duplication risk raised during the audit was fixed in-phase and kept as a recorded, refuted hypothesis.

**Verdict:** pass

## Lens Scores

| Pack | Lens | Score | Verdict |
|---|---|---:|---|
| core | parnas | 9 | the CLI/skill boundary holds: the CLI runs no lenses and produces no findings; judgment lives only in the skill/prompts |
| core | cormen | 8 | the semantic linter encodes the verdict↔severity and reference-integrity invariants; `record` is now idempotent by audit label |
| core | mcconnell | 8 | six small phased commits, CI green throughout, docs/CHANGELOG synced; only gap is unit tests vs CI smokes (CLOSE-003) |
| core | brooks | 8 | one story held across six phases — skill primary, CLI seatbelt, memory sanitized; no entity sprawl |
| core | dijkstra | 8 | the CLI stayed narrow — ten deterministic subcommands, no creep toward 'auditing' |
| implementation | kernighan | 7 | error messages are actionable, but audit memory resolves relative to CWD (CLOSE-001) and the collect fallback scans all files (CLOSE-002) |
| security-safety | security-threat | 8 | record sanitizes and stores no raw evidence; raw bundles gitignored; subprocess list-form (no shell); no secrets committed |

## Unsupported Hypotheses

- `invairiant record` duplicates memory rows when run twice on the same report, skewing history trends. — Refuted at HEAD — record now dedups by audit label (cli/invairiant.py:790-799); re-running record on the self-audit prints 'already in memory — skipping' and leaves the CSV at 6 rows. Fixed in this phase; kept here as the record of the decision.
- The local authorship hook could block legitimate commits. — Refuted — the commit-msg hook rejects only Co-Authored-By/Assisted-By trailers naming an AI agent; ordinary commits (no such trailer) pass. Verified across six phased commits, all accepted.

