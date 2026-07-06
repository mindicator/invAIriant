<div align="center">

<a href="./thumbnail.jpg"><img src="./thumbnail.jpg" alt="invAIriant — evidence-based architecture audits for AI-era codebases" width="100%"></a>

<br/>

[![CI](https://github.com/mindicator/invairiant/actions/workflows/validate.yml/badge.svg)](https://github.com/mindicator/invairiant/actions/workflows/validate.yml)
[![pip](https://img.shields.io/pypi/v/invairiant?style=flat-square&label=pip%20install)](https://pypi.org/project/invairiant/)
[![Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-informational?style=flat-square)](LICENSE)

**invAIriant keeps architectural invariants from drifting under AI-assisted change.**

Your coding agent runs the audit and gates the merge on real findings. Claude Code · Codex · Cursor.

**No evidence. No finding.**

</div>

<div align="center">
<img src="assets/invairiant-demo.gif" alt="Real terminal recording: invairiant collect, then validate-report (OK), then ci-gate — FAILED, RFP-001 [S1], exit 1 blocking the merge" width="94%">
</div>

An LLM can propose anything; only cited, verified findings count. invAIriant runs a
named set of review lenses over a bounded change, then makes every candidate survive
adversarial evidence checks before it becomes a finding. Lenses discover, evidence
verifies, severity gates. A high average score never cancels a critical finding.

## Start

**1. Add the skill to your agent** — this is the audit:

```bash
mkdir -p .claude/skills && ln -s "$PWD/skill" .claude/skills/invairiant
# Codex / Cursor: see skill/README.md
```

**2. Run it** in the agent: `/invairiant audit-pr` → a paste-ready PR comment.

**3. Gate CI** (optional — the deterministic CLI seatbelt):

```bash
pip install invairiant
invairiant ci-gate report.json      # exits 1 on an open S0/S1 finding
```

## See it catch what a reviewer missed

[**low-latency-runtime**](case-studies/low-latency-runtime/): average lens score ~7,
verdict *pass* — yet one lens files a real correctness finding the reviewer never saw.
Five more worked audits in [case-studies/](case-studies/), and a runnable demo in
[examples/refundpilot-demo/](examples/refundpilot-demo/).

## Learn more

- **How it works** — the pipeline and the evidence rules: [docs/methodology.md](docs/methodology.md)
- **The skill** — every command and scope: [skill/SKILL.md](skill/SKILL.md)
- **Lenses** — 28 across 7 packs, pick 4–6 by risk: [docs/lens-taxonomy.md](docs/lens-taxonomy.md)
- **The CLI**: [docs/cli.md](docs/cli.md) · **Gate PRs in CI**: [docs/github-action.md](docs/github-action.md)
- **Walkthrough** — a full run with real output: [docs/demo.md](docs/demo.md)

## Not this

Not a linter, scanner, or proof of correctness; it turns their output into evidence and
gates on verified findings. Not "AI, wander the repo and tell me what you think": it
audits a bounded scope (a PR, a range, a module, an ADR) and refuses one it can't bound.

---

Apache-2.0 · © 2026 mindicator · [Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md)
