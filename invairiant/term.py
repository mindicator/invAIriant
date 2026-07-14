"""Terminal helpers: human-facing ANSI color (only on a real TTY, never
piped/CI) and the `_die` exit helper. Machine output stays plain.

The CLI serves the invAIriant audit; it never runs a lens, invents a
finding, or assigns a score.
"""
from __future__ import annotations

import os
import sys

def _die(msg: str, code: int = 1) -> None:
    print(f"invairiant: {msg}", file=sys.stderr)
    sys.exit(code)


# Human-facing color — only on a real terminal (a dev shell or a recording),
# never when piped or in CI, and honoring NO_COLOR. Machine output stays plain,
# so exit codes / pipes are unaffected.
def _tty() -> bool:
    return (sys.stdout.isatty() and not os.environ.get("NO_COLOR")
            and os.environ.get("TERM") != "dumb")


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _tty() else s


def _ok(s):   return _c("32", s)         # green
def _bad(s):  return _c("31", s)         # red
def _warn(s): return _c("33", s)         # amber
def _dim(s):  return _c("2", s)          # dim


def _sev(sev: str) -> str:
    return {"S0": _c("1;31", "S0"), "S1": _c("33", "S1"), "S2": _c("36", "S2"),
            "S3": _c("2", "S3"), "NOTE": _c("2", "NOTE")}.get(sev, sev or "?")
