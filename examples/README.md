# Examples

Ready-to-copy **`invairiant.config.yml` templates**, one per project shape.
Copy the closest to your repo root and adjust `canonical_docs`, `risk_assets`,
and the mandatory lenses.

| Example | Project type | Mandatory lenses |
|---|---|---|
| [`minimal-webapp/`](minimal-webapp/) | small webapp | mcconnell · parnas · security-threat · kernighan |
| [`infra-service/`](infra-service/) | multi-tenant infra service | security-threat · parnas · mcconnell · turing |
| [`ai-agent-system/`](ai-agent-system/) | LLM agent system | turing · oracle-boundary · security-threat · leveson · mcconnell |

`infra-service/` also ships a **worked audit** you can read end to end —
[`example-audit.md`](infra-service/example-audit.md) with its machine-readable
[`example-report.json`](infra-service/example-report.json).

**Want more worked audits?** The [`../case-studies/`](../case-studies/) — one
**real**, three illustrative — show the full diff → lenses → findings → report
flow and *what a normal AI reviewer missed*. The complete end-to-end run
(`collect → audit-pr → report → render-comment → record`) is in
[`../docs/demo.md`](../docs/demo.md).
