#!/usr/bin/env bash
# invAIriant demo — an autonomous refund agent whose $50 cap is checked but
# never enforced. A normal review passes it; invAIriant catches it as an S1
# and blocks CI.
#
# Two halves, kept honest:
#   • the AGENT step (/invairiant audit-adr, run by your coding agent) does the
#     lens pipeline and writes report.json — PRECOMPUTED and shipped here.
#   • the DETERMINISTIC CLI SEATBELT below is live: collect → validate → render
#     → gate. Its output is real; it does not itself run a lens or find anything.
#
#   pip install invairiant        # then, in this repo:
#   ./run-demo.sh
set -euo pipefail
# invAIriant scopes are git-aware. If this folder isn't already inside a git
# tree (e.g. the standalone archive), make it one — no commit needed, since
# `git ls-files` sees staged files, which is all the adr scope reads. Inside a
# checkout it's already tracked, so we skip (and never nest a repo).
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { git init -q -b main . >/dev/null 2>&1 && git add -A; }
inv() { command invairiant "$@"; }        # uses the pip-installed CLI
sep() { printf '\n\033[2m%s\033[0m\n\n' "────────────────────────────────────────"; }

sep
echo "# 1 · the guarded-looking code in refund_agent.py"
sed -n '28,33p' refund_agent.py

sep
echo "# 2 · pin the scope: the ADR + the code it references"
inv collect --scope adr --path docs/adr/0007-refund-caps.md --out bundle.json

sep
echo "# 3 · the agent ran the lens pipeline → report.json (audit-adr)."
echo "#     validate it (schema + protocol rules):"
inv validate-report report.json

sep
echo "# 4 · the finding, as a paste-ready PR comment:"
inv render-comment report.json | sed -n '/## Findings/,/## Conditions/p' | sed '$d'

sep
echo "# 5 · gate CI on open S0/S1:"
if inv ci-gate report.json; then :; else echo "  → exit $?  (merge blocked)"; fi
sep
