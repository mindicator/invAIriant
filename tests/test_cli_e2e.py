"""End-to-end tests that invoke the CLI as a subprocess.

Used for the commands where building an argparse.Namespace is awkward or where
process exit codes are the contract under test (ci-gate, validate-config,
top-level dispatch). Runs `python3 cli/invairiant.py ...` from the repo root so
the framework tree (schemas/lenses) resolves.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _run(cli_path, repo_root, *args):
    return subprocess.run(
        [sys.executable, str(cli_path), *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )


# --------------------------------------------------------------------------- #
# validate-config: lens-ref cross-check
# --------------------------------------------------------------------------- #
class TestValidateConfig:
    def test_bad_lens_id_reported(self, cli_path, repo_root, tmp_path):
        cfg = tmp_path / "bad.config.yml"
        cfg.write_text(
            "project:\n"
            "  name: t\n"
            "  type: infra-service\n"
            "canonical_docs:\n"
            "  - README.md\n"
            "mandatory_lenses:\n"
            "  - parnas\n"
            "  - not-a-real-lens\n"
            "risk_assets:\n"
            "  - user data\n"
            "evidence:\n"
            "  require_file_or_diff_reference: true\n"
            "  allow_observations_without_evidence: true\n"
            "  allow_findings_without_evidence: false\n"
            "severity_policy:\n"
            "  low_score_threshold: 6.0\n"
            "  critical_domain_threshold: 5.0\n"
            "  id_prefix: INV\n",
            encoding="utf-8",
        )
        proc = _run(cli_path, repo_root, "validate-config", str(cfg))
        assert proc.returncode != 0
        assert "not-a-real-lens" in proc.stdout

    def test_shipped_config_is_valid(self, cli_path, repo_root):
        proc = _run(cli_path, repo_root, "validate-config", "invairiant.config.yml")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "OK" in proc.stdout


# --------------------------------------------------------------------------- #
# ci-gate exit codes
# --------------------------------------------------------------------------- #
class TestCiGate:
    def test_open_s0_exits_nonzero(self, cli_path, repo_root, example_report_path):
        proc = _run(cli_path, repo_root, "ci-gate", str(example_report_path))
        assert proc.returncode != 0
        assert "FAILED" in proc.stdout

    def test_only_low_severity_pass_exits_zero(self, cli_path, repo_root, tmp_path):
        report = {
            "title": "clean",
            "date": "2026-07-03",
            "audit_type": "pr",
            "scope": "fixture",
            "findings": [
                {"id": "L-001", "severity": "S2", "lens": "parnas",
                 "claim": "Helper name shadows a stdlib symbol locally.",
                 "confidence": "high", "status": "verified",
                 "evidence": [{"type": "file_lines", "file": "a.py", "lines": "1"}],
                 "verification": {"verified_by": "agent-2", "method": "re-read cited lines"},
                 "risk": "Minor readability cost; no behavioral impact.",
                 "recommendation": "Rename the local to avoid the shadow."},
                {"id": "L-002", "severity": "NOTE", "lens": "mcconnell",
                 "claim": "A comment references an outdated ticket id.",
                 "confidence": "medium", "status": "verified",
                 "evidence": [{"type": "file_lines", "file": "b.py", "lines": "2"}],
                 "verification": {"verified_by": "agent-2", "method": "checked the tracker"},
                 "risk": "Documentation drift only; no runtime effect.",
                 "recommendation": "Update the comment to the current ticket."},
            ],
            "lens_scores": [],
            "hypotheses": [],
            "summary": {"verdict": "pass", "executive_summary": "clean",
                        "required_actions": []},
        }
        rp = tmp_path / "clean.json"
        rp.write_text(json.dumps(report), encoding="utf-8")
        proc = _run(cli_path, repo_root, "ci-gate", str(rp))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "no open S0/S1" in proc.stdout

    def test_invalid_report_is_refused_not_gated(self, cli_path, repo_root, tmp_path):
        # ci-gate validates the report itself before gating: a schema-invalid
        # report must be refused (exit 3), never silently passed. A malformed
        # report could otherwise hide an S0 behind a broken shape.
        report = {
            "title": "broken",
            "date": "2026-07-03",
            "audit_type": "pr",
            "scope": "fixture",
            "findings": [
                {"id": "B-001", "severity": "S0", "lens": "parnas",
                 "claim": "too short", "confidence": "high", "status": "verified"},
            ],
            "lens_scores": [],
            "hypotheses": [],
            "summary": {"verdict": "pass", "executive_summary": "wrong",
                        "required_actions": []},
        }
        rp = tmp_path / "broken.json"
        rp.write_text(json.dumps(report), encoding="utf-8")
        proc = _run(cli_path, repo_root, "ci-gate", str(rp))
        assert proc.returncode == 3, proc.stdout + proc.stderr
        assert "refusing to gate" in proc.stdout + proc.stderr

    def test_unparseable_report_is_refused(self, cli_path, repo_root, tmp_path):
        rp = tmp_path / "notjson.json"
        rp.write_text("{ this is not json", encoding="utf-8")
        proc = _run(cli_path, repo_root, "ci-gate", str(rp))
        assert proc.returncode == 3, proc.stdout + proc.stderr


# --------------------------------------------------------------------------- #
# top-level CLI dispatch
# --------------------------------------------------------------------------- #
class TestDispatch:
    def test_help_lists_subcommands(self, cli_path, repo_root):
        proc = _run(cli_path, repo_root, "--help")
        assert proc.returncode == 0
        for cmd in ("init", "collect", "validate-config", "validate-report",
                    "render-report", "render-comment", "ci-gate", "record", "history"):
            assert cmd in proc.stdout, f"'{cmd}' missing from --help output"

    def test_unknown_subcommand_exits_nonzero(self, cli_path, repo_root):
        proc = _run(cli_path, repo_root, "not-a-command")
        assert proc.returncode != 0

    def test_validate_report_on_example_says_ok(self, cli_path, repo_root, example_report_path):
        # The shipped example report must still validate (schema + semantic).
        proc = _run(cli_path, repo_root, "validate-report", str(example_report_path))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "OK" in proc.stdout
