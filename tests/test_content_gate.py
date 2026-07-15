"""The pre-push content-gate (scripts/content-gate.sh) blocks stray / sensitive /
binary files from reaching the remote — the seatbelt added after an invoice PDF
was committed by accident. Exercised as a subprocess against throwaway repos."""

from __future__ import annotations

import subprocess


def _init(tmp_path):
    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    g("config", "commit.gpgsign", "false")
    return g


def _gate(repo_root, tmp_path):
    gate = str(repo_root / "scripts" / "content-gate.sh")
    return subprocess.run(["bash", gate, "HEAD"], cwd=tmp_path, capture_output=True, text=True)


class TestContentGate:
    def test_clean_source_tree_passes(self, repo_root, tmp_path):
        g = _init(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "README.md").write_text("# hi\n")
        (tmp_path / "c.json").write_text("{}\n")
        g("add", "-A"); g("commit", "-qm", "clean")
        assert _gate(repo_root, tmp_path).returncode == 0

    def test_stray_pdf_is_blocked(self, repo_root, tmp_path):
        g = _init(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        (tmp_path / "Invoice_9.pdf").write_bytes(b"%PDF-1.4\nstuff\x00\n")
        g("add", "-A"); g("commit", "-qm", "pdf")
        r = _gate(repo_root, tmp_path)
        assert r.returncode == 1 and "Invoice_9.pdf" in r.stderr

    def test_unknown_binary_is_blocked(self, repo_root, tmp_path):
        g = _init(tmp_path)
        (tmp_path / "mystery.dat").write_bytes(b"\x00\x01\x02 binary blob")
        g("add", "-A"); g("commit", "-qm", "bin")
        r = _gate(repo_root, tmp_path)
        assert r.returncode == 1 and "mystery.dat" in r.stderr

    def test_allowlisted_assets_and_banner_pass(self, repo_root, tmp_path):
        g = _init(tmp_path)
        (tmp_path / "assets").mkdir()
        (tmp_path / "assets" / "demo.gif").write_bytes(b"GIF89a\x00\x01 binary")
        (tmp_path / "thumbnail.jpg").write_bytes(b"\xff\xd8\xff\xe0 banner\x00")
        g("add", "-A"); g("commit", "-qm", "assets")
        assert _gate(repo_root, tmp_path).returncode == 0

    def test_history_csv_allowed_stray_csv_blocked(self, repo_root, tmp_path):
        g = _init(tmp_path)
        hist = tmp_path / ".invairiant" / "history"
        hist.mkdir(parents=True)
        (hist / "lens-score-history.csv").write_text("date,audit,lens,score\n")
        (tmp_path / "export.csv").write_text("a,b\n1,2\n")     # stray csv elsewhere
        g("add", "-A"); g("commit", "-qm", "csvs")
        r = _gate(repo_root, tmp_path)
        assert r.returncode == 1
        assert "export.csv" in r.stderr
        assert "lens-score-history.csv" not in r.stderr        # allowlisted → not flagged
