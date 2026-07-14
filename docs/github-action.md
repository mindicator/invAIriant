# GitHub Action — invAIriant audit gate

Fail CI on open **S0/S1** findings, validate the report against the schemas +
protocol rules, and render it into the job summary. The reusable action is
[`action.yml`](../action.yml) at the repo root.

## Usage

```yaml
# .github/workflows/audit-gate.yml
name: invAIriant gate
on: [pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: mindicator/invairiant@v0.3.0
        with:
          report: docs/audits/latest.json   # the report your /invairiant audit wrote
          max-severity: S1                   # S1 (default) blocks S0+S1; S0 blocks only S0
```

The job **fails** if the report has any open S0/S1 finding, and the rendered
PR-comment view appears in the Actions **job summary**. `validate-report` runs
too (schema + semantic), so a malformed or self-inconsistent report also fails
the gate.

## Inputs

| Input | Default | Description |
|---|---|---|
| `report` | — | Path to the audit report JSON to validate + gate on |
| `max-severity` | `S1` | `S1` blocks S0+S1; `S0` blocks only S0 |
| `collect` | `false` | Also generate `invairiant-bundle.json` (an evidence bundle for an agent step or artifact) |
| `scope` | working | bounded scope for `collect`: `working` / `range` / `commit` / `module` / `adr` / `rp` / `pr` / `repo` |
| `range` | — | git range for `collect --scope range`, e.g. `origin/main...HEAD` |
| `commit` | — | commit sha for `--scope commit` |
| `pr` | — | PR number for `--scope pr` (needs a GitHub remote + `gh`/token or the pull ref; check the PR out for full signal fidelity) |
| `path` | — | dir/file for `--scope module`, or the ADR / proposal file for `--scope adr` / `rp` |
| `narrow` | — | restrict an `adr`/`rp` scope's code to this subtree |
| `invairiant-ref` | `v0.3.0` | framework ref to run (tag / branch / sha) |

The `collect` step passes only the scope flags you set, so it stays a **bounded**
gather. Example — bundle a PR by number for an agent step:

```yaml
- uses: mindicator/invairiant@v0.3.0
  with:
    collect: true
    scope: pr
    pr: "123"
```

## How it works

The action clones the pinned `mindicator/invairiant` framework, installs the
CLI's two deps (`jsonschema`, `pyyaml`), then runs
`validate-report → render-comment (→ job summary) → ci-gate` against the report
in your checkout. It is the same judgment-free CLI as everywhere: it validates
and gates; it does **not** run lenses or produce findings. Producing the report
is the [`/invairiant` skill's](../skill/SKILL.md) job.

## Notes

- The report is typically written by your audit step — the agent runs
  `/invairiant audit-pr` (or `full-audit`) and commits/emits `report.json` —
  and this action gates on it.
- Until the CLI is on PyPI, the action fetches the framework by shallow
  `git clone`; pin `invairiant-ref` to a tag for reproducible runs.
