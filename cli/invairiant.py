#!/usr/bin/env python3
"""Zero-install entry point: `python3 cli/invairiant.py <command> [...]`.

The CLI now lives in the `invairiant/` package at the repo root (split for
readability — see docs/cli.md). This shim keeps the documented, install-free
path working: it puts the repo root on sys.path and delegates to the package,
so nothing that invokes `cli/invairiant.py` (the Action, CI, the demo, docs)
needs to change. Installed users get the `invairiant` command via
`[project.scripts]` -> `invairiant.cli:main`.

The CLI serves the invAIriant audit; it never runs a lens, invents a finding,
or assigns a score. All architectural judgment lives in the `/invairiant`
skill and the prompt pack.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from invairiant.cli import main  # noqa: E402  (after sys.path bootstrap)

if __name__ == "__main__":
    sys.exit(main())
