# What a normal AI reviewer missed — orders-api PR #874

> **ILLUSTRATIVE / SYNTHESIZED.** Fictional. Left column: the kind of comment a
> generic AI PR reviewer leaves on this diff. Right column: what the
> generated-surface-area and review-bottleneck lenses caught. The left column
> is not wrong — it grades the wrong property.

## The one-line version

The generic reviewer praised the **consistency** of 22 near-identical files.
The lens treated that consistency as camouflage and went looking for the **one
line that broke it**. It found the dropped authorization check.

## Side by side

| Generic AI reviewer said (surface / style) | The lens caught (the real defect) |
|---|---|
| "Nice, the handlers are clean and uniform — same shape across orders, invoices, shipments." | Uniform *except one line*: `invoices.ts:8-14` dropped `requireTenantScope("invoices:read")` that `orders.ts:8-13` carries. Uniformity is why a human eye slides right past the exception. (**GT-001, S1**) |
| "Good TypeScript — typed params, typed repo returns." | Types are correct and irrelevant here: the missing middleware is a *runtime authorization* gap, not a type error. The compiler cannot see a missing `requireTenantScope`. (**GT-001**) |
| "Coverage looks reasonable, tests are present for each resource." | The generated tests assert 200/404 for the caller's **own** tenant only. None asserts tenant A is **denied** tenant B's invoice — so the suite is green *and blind* to GT-001. Changed-line coverage is actually 41%. (**GT-001** missing-test, **GT-002**) |
| "Big PR but it's mostly boilerplate — fine to approve in one pass." | A 1,612-line diff cannot be meaningfully reviewed in the ~9 minutes it took; "mostly boilerplate" is the assumption that hides the one non-boilerplate line. (**GT-002, S2**) |
| "CI is green, ship it." | CI is green partly because `.github/workflows/ci.yml:39-47` sets the coverage floor to 0 for `src/routes/**`, contradicting `CONTRIBUTING.md:52`. The gate is disabled on exactly the directory the generated code landed in. (**GT-002** doc/code contradiction) |
| (silent — no comment on the security doc) | `docs/security/authz.md:19`: "every tenant-scoped read must pass `requireTenantScope`." The reviewer never read the security policy against the diff. (**GT-001** doc/code contradiction) |

## Why the generic reviewer misses this every time

A style-and-correctness reviewer reads each file and asks *is this file
internally fine?* Every one of these 22 files **is** internally fine —
`invoices.ts` is valid, typed, and compiles. The defect is not in a file; it is
in the **difference between files that are supposed to be identical**. That is a
cross-file, pattern-level property, and a per-file reviewer has no place to
stand to see it.

The generated-surface-area lens is built for exactly this. Its core question:

> **Are there near-duplicate implementations of the same abstraction with small
> inconsistencies — different timeouts, error handling, edge cases?**

"Edge cases" here is a dropped authz middleware. The lens diffs the siblings
against each other instead of reading each in isolation, and the divergence pops
out immediately.

The review-bottleneck lens supplies the second half — *why did no gate catch
it?* Its question:

> **Which deterministic gates guard every merge, and which merge paths bypass
> them?**

The coverage gate is bypassed on `src/routes/**`, and there is no
arch-conformance test asserting that tenant-scoped routes carry
`requireTenantScope`. So the one deterministic check that could have caught a
divergence a human can't see is either disabled or absent.

## The fix the lens implies (and the reviewer never asked for)

1. Restore `requireTenantScope("invoices:read")` on the invoices handler.
2. Extract the shared middleware chain into **one generated factory** so the
   authz step is structurally impossible to drop per-file.
3. Add an **arch-conformance test**: every route tagged tenant-scoped must
   include `requireTenantScope` — a machine checks the pattern so a human need
   not eyeball 22 files.
4. Restore the 80% changed-line floor on `src/routes/**`; add a
   cross-tenant-denied test per resource.
5. Split future bulk generations into stacked, individually reviewable PRs.

The generic reviewer's compliments about types and consistency all survive these
changes. What changes is that the next dropped line gets caught by a gate instead
of by a customer.
