"""Shared fixtures for the invAIriant CLI test suite.

The CLI is the `invairiant/` package at the repo root. We put the repo root on
sys.path and import it, so the white-box unit tests reach helpers via the
package facade (e.g. `cli._sha256`, `cli.evidence.shutil`). `framework_root()`
keys off the package's own location, so it keeps resolving schemas/lenses even
when a test chdirs into a tmp_path. The end-to-end tests instead invoke the
`cli_path` shim as a subprocess (the documented install-free entry point).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# repo root = tests/ -> repo
ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "cli" / "invairiant.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_cli():
    import invairiant
    return invairiant


@pytest.fixture(scope="session")
def cli():
    """The imported `invairiant` package (facade over the split submodules)."""
    return _load_cli()


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def cli_path() -> Path:
    return CLI_PATH


@pytest.fixture(scope="session")
def example_report_path() -> Path:
    return ROOT / "examples" / "infra-service" / "example-report.json"


@pytest.fixture(scope="session")
def case_study_report_path() -> Path:
    return ROOT / "case-studies" / "persistent-mesh-transport" / "report.json"


@pytest.fixture
def valid_report(case_study_report_path) -> dict:
    """A real, fully-valid report (loaded fresh so tests can mutate it)."""
    return json.loads(case_study_report_path.read_text(encoding="utf-8"))


def _base_report() -> dict:
    """A tiny, internally-consistent report used as the starting point for the
    inline invalid fixtures. Passing `_semantic_report_errors` with 0 errors."""
    return {
        "title": "test report",
        "date": "2026-07-03",
        "audit_type": "pr",
        "scope": "unit-test fixture",
        "findings": [],
        "lens_scores": [],
        "observations": [],
        "hypotheses": [],
        "summary": {
            "verdict": "pass",
            "executive_summary": "nothing found",
            "required_actions": [],
        },
    }


@pytest.fixture
def base_report():
    """Factory returning a fresh minimal consistent report dict per call."""
    return _base_report
