"""Shared fixtures for the invAIriant CLI test suite.

The CLI is a single script, not an installed package, so we load it by path
with importlib. `framework_root()` (and therefore schema/lens resolution) keys
off the module file's own location, so the imported module keeps working even
when a test chdirs into a tmp_path.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

# repo root = tests/ -> repo
ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "cli" / "invairiant.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("invairiant_under_test", CLI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def cli():
    """The imported CLI module (pure helpers + cmd_* functions)."""
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
