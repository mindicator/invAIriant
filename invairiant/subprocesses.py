"""Low-level subprocess / git / file-IO primitives shared by the scope
resolvers and the evidence collector. No judgment, no findings.

The CLI serves the invAIriant audit; it never runs a lens, invents a
finding, or assigns a score.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

def _repo_root() -> Path:
    """The git repo root, so audit memory resolves the same from any subdir.
    Falls back to CWD outside a git repo (e.g. a temp dir in tests)."""
    try:
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and p.stdout.strip():
            return Path(p.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


def _run(cmd: list, timeout: int = 60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "", str(exc)


def _git(args: list) -> str:
    rc, out, _ = _run(["git"] + args)
    return out.strip() if rc == 0 else ""


# Bounds so `collect` stays fast and memory-safe on very large repos.
_MAX_SCAN_FILES = 4000        # tracked files read in the no-ripgrep fallback
_MAX_FILE_BYTES = 512 * 1024  # skip files larger than this (likely data/binary)


def _is_probably_binary(path: Path, sniff: int = 1024) -> bool:
    try:
        with path.open("rb") as fh:
            return b"\x00" in fh.read(sniff)
    except OSError:
        return True


def _ls_files(path: str = None) -> list:
    """Tracked files, optionally bounded to a path (dir or file)."""
    cmd = ["git", "ls-files"]
    if path:
        cmd += ["--", path]
    _, out, _ = _run(cmd)
    return [f for f in out.splitlines() if f.strip()]
