"""Audit memory: the sanitize / claim-key primitives and the `record` and
`history` commands. Only distilled, secret-redacted fields are stored.

The CLI serves the invAIriant audit; it never runs a lens, invents a
finding, or assigns a score.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .subprocesses import _repo_root
from .term import _die

def _history_dir() -> Path:
    return _repo_root() / ".invairiant" / "history"


def _claim_key(text: str) -> str:
    """A normalized key for matching a claim/hypothesis across audits."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())[:80]


# Applied in order before any value enters committed memory.
_SECRET_SUBS = [
    (re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----[\s\S]*?-----END[^-]*PRIVATE KEY-----"), "[REDACTED KEY]"),
    (re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----"), "[REDACTED KEY]"),
    (re.compile(r"(?i)\b(authorization)\b\s*[:=]\s*(?:bearer\s+)?\S+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}"), "bearer [REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED AWS KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[=:]\s*\S+"), r"\1=[REDACTED]"),
]


def _sanitize(s):
    """Redact secret-like substrings before a value enters committed memory.
    Audit memory never stores raw evidence blobs — only distilled fields — so
    this is a second line of defense on the text it does store."""
    if not isinstance(s, str):
        return s
    for rx, repl in _SECRET_SUBS:
        s = rx.sub(repl, s)
    return s[:600]


# --------------------------------------------------------------------------- #
# record / history  (committed, sanitized audit memory)
# --------------------------------------------------------------------------- #
def cmd_record(args) -> int:
    data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    date = data.get("date", "")
    audit = args.audit_id or data.get("title", "")[:80] or date
    audit_csv = audit.replace(",", ";").replace("\n", " ")
    hist = Path(args.dir) if args.dir else _history_dir()
    hist.mkdir(parents=True, exist_ok=True)

    # Idempotent by audit label: re-recording the same audit would duplicate
    # rows and skew `history` trends. Skip unless --force.
    freg = hist / "finding-registry.jsonl"
    if freg.exists() and not args.force:
        seen = set()
        for line in freg.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    seen.add(json.loads(line).get("audit"))
                except (json.JSONDecodeError, AttributeError):
                    pass
        if audit in seen:
            print(f"audit '{audit}' is already in memory — skipping (use --force to re-record).")
            return 0

    rejected = [h for h in data.get("hypotheses", []) if h.get("rejected_reason")]
    with (hist / "rejected-hypotheses.jsonl").open("a", encoding="utf-8") as f:
        for h in rejected:
            f.write(json.dumps({
                "date": date, "audit": audit, "lens": h.get("lens"),
                "text": _sanitize(h.get("text", "")),
                "rejected_reason": _sanitize(h.get("rejected_reason", "")),
                "claim_key": _claim_key(h.get("text", "")),
            }, ensure_ascii=False) + "\n")

    findings = data.get("findings", [])
    with freg.open("a", encoding="utf-8") as f:
        for fd in findings:
            f.write(json.dumps({
                "date": date, "audit": audit, "id": fd.get("id"),
                "severity": fd.get("severity"), "lens": fd.get("lens"),
                "category": fd.get("category"), "claim": _sanitize(fd.get("claim", "")),
                "status": fd.get("status", "verified"),
                "claim_key": _claim_key(fd.get("claim", "")),
            }, ensure_ascii=False) + "\n")

    scores = data.get("lens_scores", [])
    csvp = hist / "lens-score-history.csv"
    new = not csvp.exists()
    with csvp.open("a", encoding="utf-8") as f:
        if new:
            f.write("date,audit,lens,score\n")
        for s in scores:
            f.write(f"{date},{audit_csv},{s.get('lens')},{s.get('score')}\n")

    print(f"recorded into {hist}/ — {len(findings)} finding(s), "
          f"{len(rejected)} rejected hypothes(e)s, {len(scores)} lens score(s). "
          f"Sanitized; commit history/, keep cache/ local.")
    return 0


def cmd_history(args) -> int:
    import csv as _csv
    from collections import Counter, defaultdict
    hist = Path(args.dir) if args.dir else _history_dir()
    csvp = hist / "lens-score-history.csv"
    if not csvp.exists():
        _die(f"no audit memory at {csvp} — run `invairiant record` first", 1)
    by_lens = defaultdict(list)
    for r in _csv.DictReader(csvp.open(encoding="utf-8")):
        if args.lens and r["lens"] != args.lens:
            continue
        try:
            by_lens[r["lens"]].append((r["date"], float(r["score"])))
        except (KeyError, ValueError):
            pass
    print("lens score history (oldest → newest):")
    for lens, seq in sorted(by_lens.items()):
        seq.sort()
        scores = [s for _, s in seq]
        trend = " → ".join(f"{s:g}" for s in scores)
        flag = "   ⚠ two consecutive drops" if len(scores) >= 3 and scores[-1] < scores[-2] < scores[-3] else ""
        print(f"  {lens:26} {trend}{flag}")
    freg = hist / "finding-registry.jsonl"
    if freg.exists():
        keys = Counter()
        labels = {}
        for line in freg.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            k = rec.get("claim_key")
            if k:
                keys[k] += 1
                labels[k] = rec.get("claim", "")[:60]
        recurring = [(k, c) for k, c in keys.items() if c > 1]
        if recurring:
            print("recurring findings (seen in >1 audit):")
            for k, c in sorted(recurring, key=lambda x: -x[1]):
                print(f"  {c}×  {labels.get(k, k)}")
    return 0
