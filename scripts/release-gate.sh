#!/usr/bin/env bash
#
# release-gate — refuse to release a commit whose CI is not green.
#
# Exit 0 ONLY when the "check runs" for the given commit/ref are all present and
# all 'success'. Anything else fails closed:
#   - gh missing / not authenticated        -> exit 3
#   - no CI runs yet (nothing ran)          -> exit 1  (push the branch, WAIT)
#   - any check not 'success' (incl. pending)-> exit 1  (wait for green)
#
# Used two ways:
#   1. Automatically by the local pre-push hook, per tag being pushed.
#   2. By hand before cutting a release:   scripts/release-gate.sh v0.2.3
#
# The rule this enforces: push -> wait for CI green -> only THEN tag / release.
# It exists so the rule is mechanical, not a thing to remember.

set -uo pipefail

ref="${1:-HEAD}"

commit="$(git rev-parse "${ref}^{commit}" 2>/dev/null)" || {
  echo "release-gate: cannot resolve '$ref' to a commit" >&2
  exit 2
}
short="${commit:0:7}"

if ! command -v gh >/dev/null 2>&1; then
  echo "release-gate: 'gh' not found — cannot verify CI for $short (fail closed)" >&2
  exit 3
fi

slug="${INVAIRIANT_SLUG:-}"
if [ -z "$slug" ]; then
  url="$(git remote get-url origin 2>/dev/null || true)"
  slug="$(printf '%s' "$url" | sed -E 's#^.*github\.com[:/]+##; s/\.git$//')"
fi
if [ -z "$slug" ]; then
  echo "release-gate: no GitHub remote (set INVAIRIANT_SLUG=owner/repo) — fail closed" >&2
  exit 3
fi

counts="$(gh api "repos/$slug/commits/$commit/check-runs" \
  --jq '"\(.total_count) \([.check_runs[] | select(.conclusion != "success")] | length)"' 2>/dev/null)" || {
  echo "release-gate: could not query CI for $short via gh (fail closed)" >&2
  exit 3
}
total="${counts%% *}"
nonsuccess="${counts##* }"

if [ "${total:-0}" -eq 0 ] 2>/dev/null; then
  echo "release-gate: no CI runs on $short yet — push the branch and WAIT for CI, then retry" >&2
  exit 1
fi
if [ "${nonsuccess:-1}" -ne 0 ] 2>/dev/null; then
  echo "release-gate: CI NOT green on $short ($nonsuccess of $total checks not 'success') — wait for green" >&2
  exit 1
fi

echo "release-gate: CI green on $short ($total checks) — OK to tag / release."
exit 0
