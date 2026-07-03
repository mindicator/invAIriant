# `invairiant` CLI

Infrastructure around the agentic audit — **not an architecture auditor.** No
lenses, no findings, no scores. All judgment lives in the
[`/invairiant` skill](../skill/SKILL.md); this CLI scaffolds, validates,
collects evidence, renders, and gates.

Full spec and rationale: [`docs/cli.md`](../docs/cli.md).

## Install

```bash
pip install -e .     # or: pipx install -e .  → gives the `invairiant` command
```

(No install? Run `python3 cli/invairiant.py <command>` directly.) Python 3.9+;
`jsonschema` + `pyyaml` are pulled in as dependencies.

## Commands

| Command | Purpose |
|---|---|
| `init [--type T]` | scaffold `invairiant.config.yml` |
| `collect [--range A..B] [--out F]` | build a deterministic evidence bundle (candidate pointers only) |
| `validate-config [paths…]` | schema-check configs + cross-check lens ids |
| `validate-report <paths…> [--schema-only] [--md]` | schema **+ semantic** checks on a report |
| `render-report <report.json> [--out F]` | report JSON → Markdown |
| `render-comment <report.json> [--out F]` | report JSON → paste-ready PR comment |
| `ci-gate <report.json> [--max-severity S0\|S1]` | exit non-zero on open S0/S1 |
| `record <report.json> [--force]` | append distilled, **sanitized** memory to `.invairiant/history/` |
| `history [--lens L]` | lens-score trends + recurring findings |

`collect-evidence` is a thin alias for the adapter-only subset of `collect`.

Full spec: [`docs/cli.md`](../docs/cli.md). Worked flow:
[`docs/demo.md`](../docs/demo.md). Resolves the framework via
`$INVAIRIANT_HOME`, the repo layout, or by searching upward from the current
directory.
