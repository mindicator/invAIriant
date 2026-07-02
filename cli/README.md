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

## Quick use

```bash
invairiant init --type infra-service
invairiant validate-config
invairiant collect-evidence --out evidence.json
invairiant validate-report docs/audits/2026-06-19.json
invairiant render-report docs/audits/2026-06-19.json --out report.md
invairiant ci-gate docs/audits/2026-06-19.json   # exits 1 on open S0/S1
```

Resolves the framework via `$INVAIRIANT_HOME`, the repo layout, or by searching
upward from the current directory.
