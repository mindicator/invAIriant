#!/usr/bin/env bash
#
# content-gate: refuse to push a tree that carries files which do not belong in
# the framework. Runs on pre-push over the FULL tree of the commit being pushed
# (deliberately thorough — an accidental invoice PDF once reached the public
# repo; this is the seatbelt so it cannot happen again).
#
# This framework is source only: Python, Markdown, JSON/YAML/TOML, a couple of
# shell/tape scripts, and ONE intentional binary (the demo recording under
# assets/). Anything else in a commit is almost certainly a stray file.
#
# BLOCKS the push (exit 1) on:
#   - denylisted extensions: documents, office files, credentials / keys,
#     archives, executables, data dumps;
#   - any BINARY blob that is not on the allowlist (assets/ images).
# WARNS (does not block) on filenames that look like personal / financial /
# secret material, so a maintainer eyeballs them.
#
# Usage:  content-gate.sh <commit-sha>     (defaults to HEAD)
# Bypass, last resort and think first:  git push --no-verify

set -uo pipefail
sha="${1:-HEAD}"
EMPTY_TREE=4b825dc642cb6eb9a060e54bf8d69288fbee4904   # git's canonical empty tree

# Extensions that must never live in this repo (documents, office, credentials,
# archives, executables, data dumps). `csv` is here too — the one legitimate csv
# is the audit memory, allowlisted below.
DENY_EXT='pdf|docx?|xlsx?|pptx?|csv|rtf|odt|ods|pages|numbers|pem|key|p12|pfx|keystore|jks|ppk|zip|tar|gz|tgz|bz2|rar|7z|exe|dll|dmg|pkg|msi|so|dylib|class|jar|war|sqlite3?|mdb|dump|bak|ipa|apk'
# Deliberate files that ARE allowed to live in the repo (exempt from the checks
# above). Extend this consciously when you add a real asset — never to sneak a
# stray file past the gate:
#   - assets/ images  (the demo recording lives here)
#   - thumbnail.*      (the README banner, referenced in README.md)
#   - the committed audit-memory csv under .invairiant/history/
ALLOW='^assets/.*\.(gif|png|jpe?g|svg|webp)$|^thumbnail\.(gif|png|jpe?g|svg|webp)$|^\.invairiant/history/.*\.csv$'
# Filenames that smell like sensitive material regardless of extension (warn).
WARN_NAME='invoice|receipt|statement|payslip|payroll|passport|(^|/)\.env(\.|$)|id_rsa|id_ed25519|credentials?|(^|/)secret'

files="$(git ls-tree -r --name-only "$sha" 2>/dev/null)" || {
  echo "  content-gate: cannot read tree for $sha — fail closed" >&2; exit 2; }
[ -z "$files" ] && exit 0

# 1) denylisted extensions
hit_ext="$(printf '%s\n' "$files" | grep -iE "\.(${DENY_EXT})\$" || true)"

# 2) binary blobs (git marks binary diffs with '-' add/del counts).
bins="$(git diff --numstat "$EMPTY_TREE" "$sha" 2>/dev/null | awk -F'\t' '$1=="-" && $2=="-"{print $3}')"

# Union of both, minus the allowlist → what actually blocks the push.
blocked="$(printf '%s\n%s\n' "$hit_ext" "$bins" | grep -v '^$' | grep -vE "$ALLOW" | sort -u || true)"

# 3) suspicious filenames — warn only (do not block legit prose that mentions them)
warned="$(printf '%s\n' "$files" | grep -iE "$WARN_NAME" | grep -vE "$ALLOW" | grep -ivE "\.(${DENY_EXT})\$" | sort -u || true)"
if [ -n "$warned" ]; then
  echo "  content-gate: ⚠ filenames that look sensitive — eyeball before pushing:" >&2
  printf '%s\n' "$warned" | sed 's/^/      /' >&2
fi

if [ -n "$blocked" ]; then
  echo "  content-gate: ✗ refusing to push — these files do not belong in the framework" >&2
  echo "               (stray document / binary / credential). Remove them from the" >&2
  echo "               commit(s) — e.g. 'git rm --cached <file>' then amend/rebase — or, if a" >&2
  echo "               binary is deliberate, add it to ALLOW_BIN in scripts/content-gate.sh." >&2
  echo "               Last resort (be sure): git push --no-verify" >&2
  printf '%s\n' "$blocked" | sed 's/^/      /' >&2
  exit 1
fi
exit 0
