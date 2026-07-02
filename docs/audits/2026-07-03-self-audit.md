# invAIriant Audit Report — self-audit

> The framework as its own first subject. Machine-readable form:
> [`2026-07-03-self-audit.json`](2026-07-03-self-audit.json) (schema-valid;
> `invairiant ci-gate` → pass). Every finding cites real repo evidence.

- **Date:** 2026-07-03
- **Audit type:** full-scale
- **Project / commit:** invairiant · `db64b5d`
- **Participants:** fable-agent (single-agent run: lens passes → evidence
  verification → severity → synthesis), mindicator (owner, gates)
- **Config:** [`invairiant.config.yml`](../../invairiant.config.yml)

## Scope

The invAIriant framework at `db64b5d`, audited **as a software artifact**:
docs, lens library, schemas, prompts, templates, skill, cli, examples, CI.
In scope: internal consistency, boundaries, and whether the framework upholds
its own rules. **Out of scope:** the subjective quality of individual lens
*content*, and the fictional example project (`conveyor`).

## Inputs Reviewed

- Repo at `db64b5d`
- Internal markdown link integrity: **139 relative links checked, 0 broken**
- `schemas/*.json`, `cli/invairiant.py`, `scripts/validate_framework.py`
- `examples/infra-service/{example-audit.md, example-report.json}`
- CI (`Validate Framework`, green on `db64b5d`)

## Executive Summary

The framework holds together as its own first subject. Boundaries are the
strongest dimension — the CLI genuinely *serves* the audit without performing
one, and the primary (skill) / secondary (protocol) / helper (CLI) story is
coherent. Documentation is clean: all 139 internal links resolve and no
origin-project jargon leaks in. There are **no S0 or S1 findings**. Two debt
items remain: the tooling does not verify that a config's lens ids actually
exist (INV-001, S2), and the example report JSON cites two finding ids it
never defines (INV-002, S3).

**Verdict:** `pass` — with the two items scheduled (neither blocks).

## Lens Scores

| Pack | Lens | Score | Verdict |
|---|---|---:|---|
| core | parnas | 9 | Skill/schema/CLI boundaries explicit **and upheld in code**: `cli/invairiant.py` runs no lens, emits no finding, assigns no score |
| core | mcconnell | 8 | Docs synchronized across a large surface (139/139 links resolve; CHANGELOG kept); one debt item (INV-001) |
| core | brooks | 8 | One coherent story after repositioning; the 4–6-lens anti-overengineering canon is stated and practiced |
| core | dijkstra | 8 | Negative space is explicit and enforced: "the CLI must not audit" is a stated non-goal and true in code |
| implementation | kernighan | 7 | Docs/CLI operable (`--help`, contextful `_die`); a typo'd config lens id fails late, not at validate time (INV-001) |
| security-safety | security-threat | 8 | Small controlled surface: fixed adapter registry + list-form subprocess (no shell); no secrets in repo; authorship hook local-only |

No lens scored below the 6.0 threshold, so no score-triggered findings.

## Medium Findings

### INV-001 — config lens ids are not checked against the library (S2, mcconnell, confidence: high)

- **Claim:** Nothing cross-checks that a config's `mandatory_lenses` name
  lenses that actually exist; a typo passes validation but has no lens file,
  so the audit silently cannot run that lens.
- **Evidence:**
  - `schemas/invairiant.config.schema.json:28-33` — `mandatory_lenses` items
    are constrained only by a kebab-case pattern, not by existence.
  - *missing check* — neither `scripts/validate_framework.py` nor
    `invairiant validate-config` cross-references `mandatory_lenses` /
    `critical_lenses` against `lenses/*/*.md`; a typo like `mcconel` passes
    `validate-config`.
- **Risk:** A config can reference a dead lens id and pass every check; the
  omission surfaces only mid-audit, weakening the tooling's role as a safety
  net around the agentic audit.
- **Recommendation:** Add a referential-integrity check (config lens ids ⊆
  known lens ids, sourced from `lenses/*/*.md`) to `validate_framework.py` and
  to `invairiant validate-config`.
- **Owner:** mindicator · non-blocking.

## Low Findings

### INV-002 — example report cites findings it never defines (S3, mcconnell, `DOC_CODE_DRIFT`, confidence: high)

- **Claim:** `example-report.json` references CNV-043 and CNV-044 in its lens
  verdicts and executive summary but never defines them in `findings[]`
  (only CNV-041/042), while the prose example defines CNV-041..044.
- **Evidence:**
  - `examples/infra-service/example-report.json:29-32` — lens verdicts cite
    CNV-044 (line 29) and CNV-043 (line 32), neither present in `findings[]`.
  - doc/code contradiction — `examples/infra-service/example-audit.md` defines
    CNV-041 through CNV-044 as full findings; the JSON's `findings[]` holds
    only CNV-041 and CNV-042.
- **Risk:** A reader diffing the two example artifacts sees dangling finding
  ids. Low impact — example fixtures only.
- **Recommendation:** Either add CNV-043/044 as full findings in the JSON, or
  reword the verdicts/summary to not cite ids the JSON does not define.
- **Owner:** mindicator · non-blocking.

## Notes / Observations

- **Coverage asymmetry (mcconnell):** `validate_framework.py` validates
  `example-findings.json` against the finding schema but not
  `example-report.json` against the audit-report schema; the report schema is
  only exercised by the CLI smoke test in CI. Not a defect (CI covers it), but
  the two checks cover overlapping-yet-different subsets.
- **Good-state (mcconnell):** internal link integrity is clean — 139/139
  relative markdown links resolve at `db64b5d`.
- **Good-state (parnas):** no origin-project (the origin project) jargon leaks into the
  generic framework; the only mentions are the README origins note and
  `lenses/domain/network-persistence.md`, by design.

## Unsupported Hypotheses

| Hypothesis | Verdict |
|---|---|
| Could a hostile `invairiant.config.yml` make `invairiant collect-evidence` run arbitrary commands? | **Refuted** — adapters resolve only through the fixed `_ADAPTERS` registry in `cli/invairiant.py`; unknown names are skipped and `subprocess.run` uses list form (`shell=False`). The config selects *which known tools* run, not *what command*. |

## Strongest Lens

**parnas (9).** The load-bearing boundary of the whole project — "the CLI
serves the audit, it never performs one" — is not merely documented; it is
true in `cli/invairiant.py`, which contains no lens, no finding construction,
and no scoring.

## Weakest Lens

**kernighan (7).** The one operability gap of note: a mistyped
`mandatory_lens` is not caught at `validate-config` time and fails late during
the audit (INV-001).

## Required Actions Before Next Milestone

1. **INV-001** — add a config↔lens-library referential-integrity check to
   `validate_framework.py` and `invairiant validate-config`. Owner mindicator,
   non-blocking.
2. **INV-002** — reconcile `example-report.json` with `example-audit.md`.
   Owner mindicator, non-blocking.

## Reviewer Notes

Single-agent run: one agent executed all four pipeline stages, applying the
stage boundaries by discipline (candidates were verified against the real
files, not asserted). Verification survival: 3 candidate findings proposed → 2
verified as findings (INV-001, INV-002), 1 demoted to an observation (the
validate_framework/report coverage asymmetry — real but not a defect). One
security hypothesis was investigated and refuted (kept above). A future audit
should re-run with an independent verifier agent for the S2 item, and check
the two example artifacts after INV-002 is addressed.
