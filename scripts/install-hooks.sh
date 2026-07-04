#!/usr/bin/env bash
#
# Install the local pre-push RELEASE GATE hook.
#
# The hook refuses to push a TAG whose commit does not have green CI, delegating
# to scripts/release-gate.sh. Branch pushes pass through untouched (CI runs AFTER
# you push the branch — that is the point). Bypass, last resort: git push --no-verify
#
# Run once per clone:  bash scripts/install-hooks.sh
# Idempotent. Does not touch any other hook.

set -euo pipefail

root="$(git rev-parse --show-toplevel)"
hook="$root/.git/hooks/pre-push"

if [ -e "$hook" ] && ! grep -q "release-gate" "$hook" 2>/dev/null; then
  echo "install-hooks: $hook already exists and is not the release gate — leaving it alone." >&2
  echo "  merge the snippet from scripts/install-hooks.sh by hand if you want both." >&2
  exit 1
fi

cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
# release-gate: refuse to push a TAG unless CI is green on its commit.
# Branch pushes pass through. Bypass (last resort): git push --no-verify
gate="$(git rev-parse --show-toplevel)/scripts/release-gate.sh"
status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in refs/tags/*) ;; *) continue ;; esac
  case "$local_sha" in *[!0]*) ;; *) continue ;; esac   # skip tag deletions (all-zero sha)
  tag="${remote_ref#refs/tags/}"
  if [ -x "$gate" ] || [ -f "$gate" ]; then
    bash "$gate" "$local_sha" || {
      echo "release-gate: refusing to push tag '$tag' (see above; git push --no-verify to override)" >&2
      status=1
    }
  else
    echo "release-gate: scripts/release-gate.sh missing — refusing tag '$tag' (fail closed)" >&2
    status=1
  fi
done
exit $status
HOOK

chmod +x "$hook"
echo "install-hooks: installed release-gate pre-push hook at $hook"
