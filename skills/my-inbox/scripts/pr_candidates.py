#!/usr/bin/env python3
"""Rank recent actionable reports (no PR yet) by how ready they are for "Create PR".

Reads the actionable-view list from inbox-reports-list (raw payload or the
[{"type": "text", "text": ...}] tool-result wrapper) plus, optionally, the
in-progress tasks list. Classifies each report from its own fields and summary
text, prints a numbered table with one verdict per row, and writes
<out>/candidates.json for follow-up. No network calls.

    python3 pr_candidates.py --reports <actionable.json> [--tasks <tasks.json>]
        [--out <dir>] [--total 138] [--stale-days 14] [--title-width 45]

Verdicts, first that applies:
  agent working    an in-progress signal_report task names this report
  digest           a scheduled scout digest or session summary; nothing to implement
  has issue #N     the summary links a GitHub issue; the issue is the handle, not Create PR
  needs decision   the summary says the fix is a human or config decision
  check PR #N      the summary cites an existing PR; verify it is not already the fix
  needs research   no code paths and no solution section; too thin for an agent run
  stale, re-verify report older than --stale-days; the diagnosis may not hold any more
  create PR        code-shaped fix with a solution section: press Create PR on the report

Rules live in references/daily-triage.md too; a change goes to both.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
ISSUE_RE = re.compile(r"github\.com/[^/\s]+/[^/\s]+/issues/(\d+)")
PR_LINK_RE = re.compile(r"github\.com/[^/\s]+/[^/\s]+/pull/(\d+)")
PR_REF_RE = re.compile(r"(?<![\w/])#(\d{3,6})\b")
PATH_RE = re.compile(r"`[\w./-]+\.(?:py|ts|tsx|js|jsx|md|yaml|yml|rs|go|sql|rb|java|kt|swift|php|cs)(?::\d+(?:-\d+)?)?`")
SOLUTION_RE = re.compile(r"## Solution|\*\*Solution\*\*|Paste-ready brief|\*\*Action\*\*|Recommended change|Recommended next step|## Proposed fix|\*\*Proposed fix\*\*")
DIGEST_RE = re.compile(r"\b(?:digest|summarizer|session summary|weekly summary)\b|^Summary for ", re.I)
DECISION_RE = re.compile(r"human (?:configuration )?decision|not a code change|configuration decision|decide whether to (?:disable|keep|retire)", re.I)


def load_payload(path: str) -> dict | list:
    data = json.loads(Path(path).read_text())
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        data = json.loads(data[0]["text"])
    return data


def results_of(payload: dict | list) -> list[dict]:
    if isinstance(payload, dict):
        if "results" in payload:
            return payload["results"]
        if "id" in payload:
            return [payload]
        return []
    return payload


def age(iso: str, now: dt.datetime) -> tuple[str, int]:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    minutes = int((now - t).total_seconds() // 60)
    days = minutes // 1440
    if minutes < 60:
        return f"{minutes}m", days
    if minutes < 2880:
        return f"{minutes // 60}h", days
    if days < 21:
        return f"{days}d", days
    return f"{days // 7}w", days


def trim(title: str, width: int) -> str:
    return title if len(title) <= width + 3 else title[:width].rstrip() + "…"


def classify(report: dict, agent_ids: set[str], days_old: int, stale_days: int) -> dict:
    summary = report.get("summary") or ""
    title = report.get("title") or ""
    issues = sorted({int(n) for n in ISSUE_RE.findall(summary)})
    pr_refs = sorted({int(n) for n in PR_LINK_RE.findall(summary)} | {int(n) for n in PR_REF_RE.findall(summary)} - set(issues))
    paths = len(PATH_RE.findall(summary))
    has_solution = bool(SOLUTION_RE.search(summary))
    shape = []
    if paths:
        shape.append(f"{paths} path{'s' if paths != 1 else ''}")
    if has_solution:
        shape.append("solution")
    if issues:
        shape.append("issue " + " ".join(f"#{n}" for n in issues[:2]))
    if pr_refs:
        shape.append("cites " + " ".join(f"#{n}" for n in pr_refs[:2]))

    if report["id"] in agent_ids:
        verdict, key = "agent working", "agent working"
    elif DIGEST_RE.search(title) or summary.startswith("Summary for "):
        verdict, key = "digest", "digest"
    elif issues:
        verdict, key = f"has issue #{issues[0]}", "has issue"
    elif DECISION_RE.search(summary):
        verdict, key = "needs decision", "needs decision"
    elif pr_refs:
        verdict, key = f"check PR #{pr_refs[0]}", "check PR"
    elif not paths and not has_solution:
        verdict, key = "needs research", "needs research"
    elif days_old >= stale_days:
        verdict, key = "stale, re-verify", "stale, re-verify"
    else:
        verdict, key = "create PR", "create PR"
    return {"verdict": verdict, "verdict_key": key, "shape": shape, "issues": issues, "pr_refs": pr_refs, "paths": paths, "has_solution": has_solution}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", required=True, help="inbox-reports-list output (actionable view, sort last_updated)")
    ap.add_argument("--tasks", help="tasks-list output (origin_product=signal_report, status=in_progress)")
    ap.add_argument("--out", default=".")
    ap.add_argument("--total", type=int, help="actionable count for the heading, if the list was capped")
    ap.add_argument("--stale-days", type=int, default=14)
    ap.add_argument("--title-width", type=int, default=45)
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    payload = load_payload(args.reports)
    reports = results_of(payload)
    total = args.total or (payload.get("count") if isinstance(payload, dict) else None) or len(reports)

    agent_ids: set[str] = set()
    if args.tasks:
        for task in results_of(load_payload(args.tasks)):
            agent_ids.update(UUID_RE.findall(task.get("description") or ""))

    rows = []
    for report in reports:
        report_age, days_old = age(report["created_at"], now)
        info = classify(report, agent_ids, days_old, args.stale_days)
        rows.append({
            "report_id": report["id"],
            "report_title": report["title"],
            "report_url": report["_posthogUrl"],
            "priority": report.get("priority"),
            "status": report["status"],
            "signal_count": report.get("signal_count") or 0,
            "source_products": report.get("source_products") or [],
            "report_age": report_age,
            "days_old": days_old,
            "created_at": report["created_at"],
            **info,
        })

    rows.sort(key=lambda r: r["created_at"], reverse=True)

    candidates = [r for r in rows if r["verdict_key"] == "create PR"]
    lines = [f"Create PR candidates ({len(candidates)} of {len(rows)} recent, {total} actionable)", "",
             "| # | Report | Age | Signals | Shape | Verdict |", "|---|---|---|---|---|---|"]
    table: dict[str, dict] = {}
    for i, r in enumerate(rows, 1):
        title = trim(r["report_title"], args.title_width)
        pri = r["priority"] or "–"
        sources = ",".join(s.replace("signals_scout", "scout").replace("replay_vision", "replay") for s in r["source_products"][:2])
        signals = f"sig{r['signal_count']} {sources}".strip()
        lines.append(f"| {i} | {pri} [{title}]({r['report_url']}) | {r['report_age']} | {signals} | {' · '.join(r['shape']) or '–'} | {r['verdict']} |")
        table[str(i)] = {**r, "row": i}
    lines.append("")
    lines.append("Legend: paths = file paths cited in the summary · solution = a Solution or Action section · issue = GitHub issue linked (the issue is the handle) · cites = an existing PR the summary names. create PR means open the report and press Create PR; everything else says why not yet.")
    if not rows:
        lines = ["No actionable reports without a PR."]

    (Path(args.out) / "candidates.json").write_text(json.dumps({"generated_at": now.isoformat(), "rows": table}, indent=1))
    print("\n".join(lines))
    print(f"\nwrote {Path(args.out) / 'candidates.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())