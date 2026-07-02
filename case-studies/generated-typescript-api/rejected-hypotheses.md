# Rejected hypotheses — orders-api PR #874

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. Kept, not deleted: recording why a
> plausible worry was refuted keeps the audit honest and stops the same guess
> re-surfacing. Evidence-first throughout.

## H1 — "A generated repo omits the `tenant_id` filter, widening the exposure below the handler"

**The instinct.** If the handlers are near-duplicates that diverge (GT-001), the
repos generated alongside them might diverge too — and a repo that forgets
`WHERE tenant_id = ?` would make the cross-tenant leak far worse and harder to
fix. Worth checking before sizing the blast radius.

**Refuted by reading all three repos.** Each repo takes `tenantId` and filters on
it. `src/repos/invoices.ts:22-31`:

```ts
static byId(id: string, tenantId: string) {
  return db.one(`SELECT * FROM invoices WHERE id = $1 AND tenant_id = $2`, [id, tenantId]);
}
```

`orders` and `shipments` repos match. The repo layer is consistent; the exposure
is **solely** the missing handler-level `requireTenantScope` (GT-001). This
matters for the fix: because the repo still scopes by `tenantId`, the leak is
"read any invoice whose id you can guess/enumerate," not "dump the whole table" —
but it is a leak, and the S1 stands. The hypothesis was right to check and wrong
on the facts.

## H2 — "`requireAuth` is a no-op stub, so every route is unauthenticated"

**The instinct.** Generated middleware is a common place for a stub that "returns
`next()`" to slip through. If `requireAuth` did nothing, the whole surface would
be open and GT-001 would be a footnote to a much bigger fire.

**Refuted by the middleware and its test.** `mw/auth.ts:14-40` verifies the
session token and populates `req.tenantId`; `test/mw/auth.test.ts:9-27` asserts a
missing/invalid token is rejected with 401, and it passes. Authentication works.
The defect is the missing **authorization** step on one route, not authentication
everywhere. (`mw/auth.ts` is out of the audited scope, but was read to bound the
blast radius — the difference between "one route over-shares" and "everything is
open.")

## H3 — "The 1,612-line diff ships speculative dead endpoints because they came with the generation"

**The instinct.** Classic generated-surface-area red flag: a big generation
carries unused exports, endpoints, and knobs that inflate the maintained surface.
On a +1,612-line PR it would be surprising if *nothing* were dead.

**Rejected — no evidence of dead surface.** Coverage report CI build 3391 shows
every generated route has at least one caller in the test suite, and the OpenAPI
spec references each endpoint; a repo-wide search found no zero-caller export.
The diff mass is genuinely high (which feeds GT-002's review-bottleneck story),
but "high volume" is not "dead code." With no locator for an actual unused
export, there is no finding — recording the negative result rather than padding
the report with a speculative dead-code item.

---

**Why keep these.** The real defects are GT-001 (a divergent duplicate dropped an
authz check) and GT-002 (it sailed through because the diff was too big to read
and the gate was off). The three rejected hypotheses were all *reasonable* — they
are the shapes this lens pack teaches you to look for — and all three were
refuted by reading specific files. That is the discipline: look widely, file only
what the evidence supports.
