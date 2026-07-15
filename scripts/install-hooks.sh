#!/usr/bin/env bash
#
# Install the local pre-push gates.
#
#   content-gate  — refuse to push stray / sensitive / binary files that do not
#                   belong in the framework (a stray invoice PDF once reached the
#                   public repo; this is the seatbelt). Checks the FULL tree of
#                   every ref pushed — branches included. See scripts/content-gate.sh.
#   release-gate  — refuse to push a TAG whose commit does not have green CI.
#                   Branch pushes pass the release gate untouched (CI runs AFTER
#                   you push the branch — that is the point). See scripts/release-gate.sh.
#
# Both fail closed. Bypass, last resort and think first:  git push --no-verify
#
# Run once per clone:  bash scripts/install-hooks.sh
# Idempotent. Upgrades an existing gate hook; refuses to clobber a foreign one.

set -euo pipefail

root="$(git rev-parse --show-toplevel)"
hook="$root/.git/hooks/pre-push"

if [ -e "$hook" ] && ! grep -qE "release-gate|content-gate" "$hook" 2>/dev/null; then
  echo "install-hooks: $hook already exists and is not an invAIriant gate — leaving it alone." >&2
  echo "  merge the snippet from scripts/install-hooks.sh by hand if you want the gates." >&2
  exit 1
fi

cat > "$hook" <<'HOOK'
#!/usr/bin/env bash
# invAIriant local pre-push gates (fail closed; bypass, last resort: git push --no-verify):
#   content-gate — refuse stray/sensitive/binary files that don't belong (every ref).
#   release-gate — refuse to push a TAG whose commit lacks green CI.
root="$(git rev-parse --show-toplevel)"
content_gate="$root/scripts/content-gate.sh"
release_gate="$root/scripts/release-gate.sh"
status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$local_sha" in *[!0]*) ;; *) continue ;; esac   # skip deletions (all-zero sha)

  # content gate — every ref being pushed (branches too; that is where it matters)
  if [ -f "$content_gate" ]; then
    bash "$content_gate" "$local_sha" || {
      echo "content-gate: refusing to push '$remote_ref' (see above; git push --no-verify to override)" >&2
      status=1
    }
  else
    echo "content-gate: scripts/content-gate.sh missing — refusing '$remote_ref' (fail closed)" >&2
    status=1
  fi

  # release gate — tags only
  case "$remote_ref" in
    refs/tags/*)
      tag="${remote_ref#refs/tags/}"
      if [ -f "$release_gate" ]; then
        bash "$release_gate" "$local_sha" || {
          echo "release-gate: refusing to push tag '$tag' (see above; git push --no-verify to override)" >&2
          status=1
        }
      else
        echo "release-gate: scripts/release-gate.sh missing — refusing tag '$tag' (fail closed)" >&2
        status=1
      fi
      ;;
  esac
done
exit $status
HOOK

chmod +x "$hook"
echo "install-hooks: installed pre-push gates (content-gate + release-gate) at $hook"
