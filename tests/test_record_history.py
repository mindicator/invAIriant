"""Tests for `record` (committed sanitized memory) and `history` (trend view).

These drive the cmd_* functions directly via argparse.Namespace, writing into a
tmp_path memory dir. cmd_record reads/writes only under --dir, so no chdir is
needed here.
"""

from __future__ import annotations

import argparse
import json


def _record_ns(report, histdir, force=False, audit_id=None):
    return argparse.Namespace(
        report=str(report), dir=str(histdir), force=force, audit_id=audit_id
    )


def _history_ns(histdir, lens=None):
    return argparse.Namespace(dir=str(histdir), lens=lens)


def _write_report(path, findings, hypotheses=None, scores=None, verdict="pass",
                  title="test-audit-A", date="2026-07-03"):
    payload = {
        "title": title,
        "date": date,
        "audit_type": "pr",
        "scope": "fixture",
        "findings": findings,
        "lens_scores": scores or [],
        "hypotheses": hypotheses or [],
        "summary": {"verdict": verdict, "executive_summary": "x", "required_actions": []},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _count_lines(path):
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


class TestRecordIdempotency:
    def test_second_record_skips_without_force(self, cli, tmp_path):
        report = _write_report(
            tmp_path / "r.json",
            findings=[{"id": "A-001", "severity": "S2", "lens": "parnas",
                       "claim": "boundary bypass", "confidence": "high", "status": "verified"}],
            scores=[{"pack": "core", "lens": "parnas", "score": 8}],
        )
        histdir = tmp_path / "hist"
        freg = histdir / "finding-registry.jsonl"
        csvp = histdir / "lens-score-history.csv"

        assert cli.cmd_record(_record_ns(report, histdir)) == 0
        reg_after_first = _count_lines(freg)
        csv_after_first = _count_lines(csvp)
        assert reg_after_first == 1

        # Second run with the same audit label: should skip, counts unchanged.
        assert cli.cmd_record(_record_ns(report, histdir)) == 0
        assert _count_lines(freg) == reg_after_first
        assert _count_lines(csvp) == csv_after_first

    def test_force_appends_again(self, cli, tmp_path):
        report = _write_report(
            tmp_path / "r.json",
            findings=[{"id": "A-001", "severity": "S2", "lens": "parnas",
                       "claim": "boundary bypass", "confidence": "high", "status": "verified"}],
        )
        histdir = tmp_path / "hist"
        freg = histdir / "finding-registry.jsonl"

        cli.cmd_record(_record_ns(report, histdir))
        assert _count_lines(freg) == 1
        cli.cmd_record(_record_ns(report, histdir, force=True))
        assert _count_lines(freg) == 2


class TestRecordSanitization:
    def test_secret_in_claim_is_redacted(self, cli, tmp_path):
        report = _write_report(
            tmp_path / "r.json",
            findings=[{"id": "A-001", "severity": "S2", "lens": "security-threat",
                       "claim": "leaks api_key=SECRET123 into logs",
                       "confidence": "high", "status": "verified"}],
        )
        histdir = tmp_path / "hist"
        cli.cmd_record(_record_ns(report, histdir))
        text = (histdir / "finding-registry.jsonl").read_text(encoding="utf-8")
        assert "SECRET123" not in text
        assert "[REDACTED]" in text


class TestHistoryTrend:
    def _write_csv(self, csvp, rows):
        lines = ["date,audit,lens,score"]
        for date, audit, lens, score in rows:
            lines.append(f"{date},{audit},{lens},{score}")
        csvp.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_two_consecutive_drops_flagged(self, cli, tmp_path, capsys):
        histdir = tmp_path / "hist"
        histdir.mkdir()
        self._write_csv(
            histdir / "lens-score-history.csv",
            [
                ("2026-01-01", "a1", "turing", 9),
                ("2026-02-01", "a2", "turing", 8),
                ("2026-03-01", "a3", "turing", 7),
                # a stable lens across three dates
                ("2026-01-01", "a1", "parnas", 8),
                ("2026-02-01", "a2", "parnas", 8),
                ("2026-03-01", "a3", "parnas", 8),
            ],
        )
        assert cli.cmd_history(_history_ns(histdir)) == 0
        out = capsys.readouterr().out
        assert "turing" in out
        # the drop flag sits on the turing line only
        turing_line = next(ln for ln in out.splitlines() if "turing" in ln)
        parnas_line = next(ln for ln in out.splitlines() if "parnas" in ln)
        assert "two consecutive drops" in turing_line
        assert "two consecutive drops" not in parnas_line

    def test_stable_lens_not_flagged(self, cli, tmp_path, capsys):
        histdir = tmp_path / "hist"
        histdir.mkdir()
        self._write_csv(
            histdir / "lens-score-history.csv",
            [
                ("2026-01-01", "a1", "parnas", 7),
                ("2026-02-01", "a2", "parnas", 8),
                ("2026-03-01", "a3", "parnas", 9),  # improving, not dropping
            ],
        )
        cli.cmd_history(_history_ns(histdir))
        out = capsys.readouterr().out
        assert "two consecutive drops" not in out
