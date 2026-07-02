# invAIriant Audit Report — orders-api PR #874

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional project and PR; all paths, line
> numbers, coverage figures, and CI references are invented. Machine-readable
> twin: [`report.json`](./report.json).

- **Date:** 2026-07-02
- **Audit type:** pr
- **Project / commit range:** orders-api · `main..9b34ac1` (`feat/generate-crud-handlers`)
- **Participants:** claude-agent (lens auditor: generated-surface-area,
  review-bottleneck, parnas, mcconnell), claude-agent-2 (evidence verifier)
- **Config:** `invairiant.config.yml` (this directory)

## Scope

PR #874, a single 1,612-line change adding AI-generated Express/TypeScript route
handlers for orders, invoices, and shipments, plus repos and tests. Audited
against `docs/security/authz.md` and `CONTRIBUTING.md`. **Out of scope:** the
auth middleware implementation (`mw/auth.ts`), the ORM, and unrelated migrations
bundled in the branch.

## Executive Summary

PR #874 adds 1,612 lines of near-identical generated CRUD handlers. They read as
interchangeable — which is the problem: `invoices.ts` dropped the
`requireTenantScope` authorization middleware its siblings apply, opening
cross-tenant reads of invoice data (**GT-001, S1 `DIVERGENT_DUPLICATE`**). It
reached main because a 1,612-line generated diff was approved in a single pass
minutes after push, and the coverage floor that might have forced a test is
disabled on exactly `src/routes/**` (**GT-002, S2 `RUBBER_STAMP_MERGE`**). The
layering is otherwise sound (parnas 7); the S1 blocks the merge.

**Verdict:** fail — blocked on GT-001; condition on GT-002.

## Lens Scores

| Pack | Lens | Score | Verdict |
|---|---|---:|---|
| ai-generated-code | generated-surface-area | 3 | near-duplicate handlers from one template diverged on the security line: `invoices.ts` dropped `requireTenantScope` present in `orders.ts`/`shipments.ts` (GT-001) |
| ai-generated-code | review-bottleneck | 4 | 1,612-line generated PR approved in one pass ~9 min after push; changed-line coverage 41% vs the documented 80% floor; no missing-authz test (GT-002) |
| core | parnas | 7 | handler/repo/middleware layering is sound; the defect is a dropped call inside a consistent boundary (obs O-1) |
| core | mcconnell | 6 | localized and readable, but the near-duplication invites a fourth copy; consolidation not scheduled (obs O-2) |

## High Findings

### GT-001 — Divergent generated handler drops the tenant-scope authz check (S1, generated-surface-area, confidence: high)

- **Claim:** Three route handlers were generated from one template but one
  diverged on the security-relevant line: the invoices GET handler omits the
  `requireTenantScope` middleware the others apply, so any authenticated user can
  read any tenant's invoice by id.
- **Evidence:**
  - `file_lines` — `src/routes/invoices.ts:8-14` @ 9b34ac1: chain is
    `requireAuth` only; no `requireTenantScope("invoices:read")` (a comment even
    notes the omission).
  - `file_lines` — `src/routes/orders.ts:8-13` @ 9b34ac1: the sibling from the
    same template carries `requireTenantScope("orders:read")`, establishing the
    intended pattern.
  - `doc_code_contradiction` — `docs/security/authz.md:19` requires "every
    tenant-scoped read must pass `requireTenantScope` before touching a repo";
    the invoices handler reaches `InvoicesRepo.byId` without it.
  - `missing_test` — no test asserts tenant A is denied tenant B's invoice; the
    generated tests assert only 200/404 for the caller's own tenant.
- **Risk:** Cross-tenant data exposure — any authenticated tenant can enumerate
  and read other tenants' invoices and billing metadata. The near-duplication
  hides it: the three files read as interchangeable.
- **Recommendation:** Restore `requireTenantScope("invoices:read")`. Then kill
  the defect class: extract the shared middleware chain into one factory, add an
  arch-conformance test asserting every tenant-scoped route includes
  `requireTenantScope`, and add a cross-tenant-denied test per resource.
- **Category:** DIVERGENT_DUPLICATE
- **Owner / deadline:** api team / 2026-07-05 (blocking merge)

## Medium Findings

### GT-002 — 1,612-line generated PR rubber-stamped; coverage floor disabled where it landed (S2, review-bottleneck, confidence: high)

- **Claim:** A 1,612-line generated PR was approved in a single pass minutes
  after push, with changed-line coverage well below the documented floor and no
  test covering the authz divergence, so neither review nor the gates would catch
  GT-001.
- **Evidence:**
  - `ci_output` — PR #874 timeline: pushed 14:02, single approval 14:11, no line
    comments on a 22-file / 1,612-line diff.
  - `ci_output` — `jest --coverage`, CI build 3391: changed-line coverage 41%
    across `src/routes/**`; generated tests mirror the handlers.
  - `doc_code_contradiction` — `CONTRIBUTING.md:52` states an 80% changed-line
    floor "applies to all merges"; `.github/workflows/ci.yml:39-47` sets
    `coverage-threshold: 0` for `src/routes/**`, so it is not enforced where the
    generated code landed.
  - `missing_test` — no test exercises the missing-authz path; the gate that
    could catch it (cross-tenant test or arch-conformance check) does not exist.
- **Risk:** The highest-volume, least-examined code is the least-gated: a large
  generated diff clears review as a formality and clears CI because the floor is
  off on the very directory it touched, so a divergence like GT-001 ships
  unblocked.
- **Recommendation:** Restore the 80% floor for `src/routes/**` (fix the tests,
  not the threshold); add the arch-conformance test so no one must eyeball 22
  near-identical files; split future bulk generations into stacked per-resource
  PRs; report a rubber-stamp metric.
- **Category:** RUBBER_STAMP_MERGE
- **Owner / deadline:** platform / next cycle

## Notes / Observations

- **O-1 (parnas):** Layering is sound; GT-001's fix is a shared middleware
  factory plus a conformance test, not a re-architecture.
- **O-2 (mcconnell):** The three modules are near-duplicates with no shared
  abstraction; the next generated resource likely adds a fourth copy.
  Consolidation is not scheduled.

## Unsupported Hypotheses

| Hypothesis | Proposed by | Rejection / status |
|---|---|---|
| A generated repo omits the `tenant_id` filter, widening exposure below the handler | claude-agent (generated-surface-area pass) | **Rejected:** all three repos filter on `tenantId` (`src/repos/invoices.ts:22-31` applies `WHERE tenant_id = $2`); exposure is solely the missing handler-level check |
| `requireAuth` is a no-op stub, so every route is unauthenticated | claude-agent (review-bottleneck pass) | **Rejected:** `mw/auth.ts:14-40` verifies the token and sets `req.tenantId`; `test/mw/auth.test.ts:9-27` passes. The defect is missing authorization, not authentication |
| The diff ships speculative dead endpoints "because they came with the generation" | claude-agent (generated-surface-area pass) | **Rejected:** CI build 3391 coverage shows every route has a caller and the OpenAPI spec references each; no zero-caller export — diff mass is high but not dead |

## Weakest Lens

**generated-surface-area (3/10).** Near-duplicate handlers with a small,
security-relevant inconsistency — the dropped authz check — is the exact defect
shape this lens exists to surface (GT-001). A critical lens this low, tied to
tenant-data-isolation risk, yields S1.

## Required Actions Before Merge

1. **GT-001** — restore `requireTenantScope` on invoices; extract a shared
   middleware factory; add an arch-conformance test and cross-tenant-denied
   tests. Owner api team, due 2026-07-05. **Blocking merge.**
2. **GT-002** — restore the 80% floor for `src/routes/**`; stacked per-resource
   PRs; rubber-stamp metric. Owner platform, next cycle. Non-blocking.
