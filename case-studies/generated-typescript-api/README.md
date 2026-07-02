# Case study — a divergent line in bulk-generated TypeScript handlers

> **ILLUSTRATIVE / SYNTHESIZED.** This case study is fictional. The project
> `orders-api`, PR #874, and every file path, line number, coverage figure, and
> CI reference are invented to demonstrate how invAIriant applies to a large
> AI-generated diff. It is not a report on any real system.

## Context

`orders-api` is an Express + TypeScript service exposing tenant-facing CRUD over
orders, invoices, and shipments. The team leaned on an AI assistant to generate
the route handlers in bulk: one template, replicated per resource. The security
rule is written down — `docs/security/authz.md` requires that *every*
tenant-scoped read pass `requireTenantScope` before touching a repo.

**Risk assets:** tenant data isolation, authorization correctness, reviewer
capacity, maintainability of generated code.

## The change (PR #874)

One PR: **+1,612 / −40 across 22 files** — handlers, repos, and tests for three
resources, all generated from the same template. The handlers are near-identical
by construction. See [`diff.md`](./diff.md). It was approved in a single pass,
about nine minutes after it was pushed.

## The lenses

Two mandatory critical lenses drive this audit:

- **generated-surface-area** (`ai-generated-code`) — bounds what an oracle may
  *add* to a codebase per unit of human attention. Its signature target:
  near-duplicate abstractions with small behavioral inconsistencies — different
  timeouts, error handling, or (here) a dropped security check.
- **review-bottleneck** (`ai-generated-code`) — human capacity vs. generation
  rate. When a reviewer can no longer actually read the diff, a deterministic
  gate must take up the slack. Its target: rubber-stamp approvals and gates
  quietly waived on the generated path.

`parnas` and `mcconnell` round out the set; the layering is fine, so they score
well and stay out of the way.

## The miss

A generic AI PR reviewer read PR #874 and **approved it, praising the
consistency**: "clean, uniform handlers, nice types, good coverage of the
happy path." The uniformity was the whole reason it looked safe.

The generated-surface-area lens does not grade uniformity — it *hunts for the
break in it*. Diffed line by line, `invoices.ts` is identical to `orders.ts` and
`shipments.ts` except for one thing: it dropped `requireTenantScope("invoices:read")`
from the middleware chain. Its handler reaches `InvoicesRepo.byId` with only
`requireAuth`. Any authenticated user can read any tenant's invoices by id —
**cross-tenant data exposure**, and `authz.md:19` says it must not happen.

That is **GT-001, S1 `DIVERGENT_DUPLICATE`** — it blocks the merge. The
review-bottleneck lens explains *how it got in*: **GT-002, S2** — a 1,612-line
generated diff approved in one pass, with the 80% coverage floor disabled on
exactly `src/routes/**`, so neither a human nor a gate would ever see the one
line that diverged. The gate that could have caught it is switched off precisely
where the defect lives.

The full side-by-side is in [`ai-reviewer-miss.md`](./ai-reviewer-miss.md).

## Files in this case

- [`diff.md`](./diff.md) — the change
- [`invairiant.config.yml`](./invairiant.config.yml) — scope + lens config
- [`report.json`](./report.json) — schema-valid audit report
- [`report.md`](./report.md) — human-readable report
- [`rejected-hypotheses.md`](./rejected-hypotheses.md) — refuted candidates, kept
- [`ai-reviewer-miss.md`](./ai-reviewer-miss.md) — style review vs. the lens
