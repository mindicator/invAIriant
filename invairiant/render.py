"""Deterministic JSON -> Markdown / PR-comment rendering. Formatting only;
no content is added or judged.

The CLI serves the invAIriant audit; it never runs a lens, invents a
finding, or assigns a score.
"""
from __future__ import annotations

import json
from pathlib import Path

# --------------------------------------------------------------------------- #
# render-report  (deterministic JSON -> Markdown; no judgment)
# --------------------------------------------------------------------------- #
def _sev_block(title: str, findings: list, sev: str) -> list:
    rows = [f for f in findings if f.get("severity") == sev]
    if not rows:
        return []
    out = [f"## {title}", ""]
    for f in rows:
        out.append(f"### {f.get('id','?')} — {f.get('claim','')[:80]} "
                   f"({f.get('severity')}, {f.get('lens','?')}, confidence: {f.get('confidence','?')})")
        out.append("")
        out.append(f"- **Claim:** {f.get('claim','')}")
        ev = f.get("evidence", [])
        out.append("- **Evidence:**")
        for e in ev:
            bits = [e.get("type", "?")]
            if e.get("file"):
                bits.append(f"{e['file']}:{e.get('lines','')}")
            if e.get("description"):
                bits.append(e["description"])
            out.append(f"  - {' — '.join(str(b) for b in bits if b)}")
        out.append(f"- **Risk:** {f.get('risk','')}")
        out.append(f"- **Recommendation:** {f.get('recommendation','')}")
        if f.get("category"):
            out.append(f"- **Category:** {f['category']}")
        out.append("")
    return out


def cmd_render_report(args) -> int:
    data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    L = ["# invAIriant Audit Report", ""]
    L.append(f"- **Date:** {data.get('date','')}")
    L.append(f"- **Audit type:** {data.get('audit_type','')}")
    L.append(f"- **Scope:** {data.get('scope','')}")
    L.append("")
    summary = data.get("summary", {})
    L += ["## Executive Summary", "", summary.get("executive_summary", ""), "",
          f"**Verdict:** {summary.get('verdict','')}", ""]
    scores = data.get("lens_scores", [])
    if scores:
        L += ["## Lens Scores", "", "| Pack | Lens | Score | Verdict |", "|---|---|---:|---|"]
        for s in scores:
            L.append(f"| {s.get('pack','')} | {s.get('lens','')} | {s.get('score','')} | {s.get('verdict','')} |")
        L.append("")
    findings = data.get("findings", [])
    L += _sev_block("Critical Findings (S0)", findings, "S0")
    L += _sev_block("High Findings (S1)", findings, "S1")
    L += _sev_block("Medium Findings (S2)", findings, "S2")
    hyp = data.get("hypotheses", [])
    L += ["## Unsupported Hypotheses", ""]
    if hyp:
        for h in hyp:
            L.append(f"- {h.get('text','')} — {h.get('rejected_reason', h.get('follow_up',''))}")
    else:
        L.append("- none")
    L.append("")
    payload = "\n".join(L)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"rendered {args.report} -> {args.out}")
    else:
        print(payload)
    return 0


# --------------------------------------------------------------------------- #
# render-comment  (deterministic PR-comment render; no judgment)
# --------------------------------------------------------------------------- #
_SEV_ORDER = {"S0": 0, "S1": 1, "S2": 2, "S3": 3, "NOTE": 4}


def _ev_short(e: dict) -> str:
    t = e.get("type", "")
    if e.get("file"):
        return f"`{e['file']}:{e.get('lines', '')}`"
    if t == "doc_code_contradiction":
        return f"{e.get('doc', '')} vs {e.get('code', '')}"
    if t == "diff_hunk":
        return "diff hunk"
    if t == "test_failure":
        return e.get("test", "test")
    if t == "command_output":
        return f"`{e.get('command', '')}`"
    if t in ("ci_output", "incident"):
        return e.get("reference", "")
    return e.get("description", t)


def cmd_render_comment(args) -> int:
    data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    lenses = ", ".join(dict.fromkeys(s.get("lens", "") for s in data.get("lens_scores", [])))
    proj = data.get("project", {})
    audited = proj.get("commit_range") or proj.get("branch") or (data.get("scope", "")[:60])
    title = data.get("title", "")
    header = title if "pr audit" in title.lower() else f"invAIriant PR Audit — {title}"
    L = [f"# {header}", ""]
    L.append(f"**Verdict:** {summary.get('verdict', '')}")
    L.append(f"**Audited:** {audited} · **Lenses:** {lenses}")
    L.append("")
    findings = [f for f in data.get("findings", []) if f.get("status") != "rejected"]
    findings.sort(key=lambda f: _SEV_ORDER.get(f.get("severity"), 9))
    if findings:
        L += ["## Findings", ""]
        for f in findings:
            ev = f.get("evidence", [])
            L.append(f"**{f.get('id', '?')} ({f.get('severity')}, {f.get('lens', '?')}, "
                     f"confidence {f.get('confidence', '?')})** — {f.get('claim', '')}")
            if ev:
                L.append(f"- Evidence: {_ev_short(ev[0])}"
                         + (f" — {ev[0].get('description')}" if ev[0].get("description") else ""))
            L.append(f"- Risk: {f.get('risk', '')}")
            L.append(f"- Fix: {f.get('recommendation', '')}")
            L.append("")
    conditions = [a for a in summary.get("required_actions", []) if a.get("blocking")]
    if conditions:
        L += ["## Conditions", ""]
        for i, a in enumerate(conditions, 1):
            who = f" ({a['owner']})" if a.get("owner") else ""
            L.append(f"{i}. {a.get('action', '')}{who}")
        L.append("")
    obs = data.get("observations", [])
    hyp = data.get("hypotheses", [])
    if obs or hyp:
        L += ["## Observations / Hypotheses (non-blocking)", ""]
        for o in obs:
            L.append(f"- {o.get('text', '')}")
        for h in hyp:
            reason = h.get("rejected_reason") or h.get("follow_up") or ""
            L.append(f"- Rejected hypothesis: {h.get('text', '')}" + (f" — {reason}" if reason else ""))
        L.append("")
    payload = "\n".join(L)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
        print(f"rendered PR comment: {args.report} -> {args.out}")
    else:
        print(payload)
    return 0
