#!/usr/bin/env python3
"""List your recently created GitHub issues that no inbox report covers.

Reads the issues you authored (from `gh api`, or a saved --issues file) and
matches each against every report list you pass with --reports (any
inbox-reports-list output: the source_product=github pull, a scout-filtered
pull, the actionable and monitoring pulls) and against table.json from
render_table.py, whose PRs carry closing-issue references. Prints a numbered
table with one verdict per issue and writes <out>/issue_gaps.json.

    python3 issue_gaps.py --repo <owner/repo> [--me <login>] [--issues <json>]
        --reports <list.json> ... [--table table.json] [--out <dir>] [--limit 25] [--fresh-hours 6]
        [--scout <scout skill_name> --note]

Verdicts, first that applies:
  report <status>      a report's title or summary names the issue (link and status shown)
  covered by PR #N     an in-flight PR closes the issue; its report is the handle
  closed, no report    the issue is closed already; nothing for the inbox to do
  too new              younger than --fresh-hours (default 6; match it to how often your source or scout runs)
  no report            open, old enough, nothing found: a scout-note candidate

--note appends a drafted `scout-notes-create` call for the no-report rows,
addressed to --scout (required with --note) and expiring after --note-days. Print
it, never send it without the user's go-ahead; notes are not idempotent.

Rules live in references/daily-triage.md too; a change goes to both.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path


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


def age(iso: str, now: dt.datetime) -> tuple[str, float]:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    hours = (now - t).total_seconds() / 3600
    if hours < 1:
        return f"{int(hours * 60)}m", hours
    if hours < 48:
        return f"{int(hours)}h", hours
    days = int(hours // 24)
    return (f"{days}d" if days < 21 else f"{days // 7}w"), hours


def trim(title: str, width: int) -> str:
    return title if len(title) <= width + 3 else title[:width].rstrip() + "…"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/repo whose issues you file")
    ap.add_argument("--me", help="GitHub login (default: gh api user)")
    ap.add_argument("--issues", help="saved `gh api repos/<repo>/issues?creator=...` output; fetched when absent")
    ap.add_argument("--reports", nargs="*", default=[], help="inbox-reports-list outputs to match against")
    ap.add_argument("--table", help="table.json from render_table.py, for PR closing-issue references")
    ap.add_argument("--out", default=".")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--fresh-hours", type=float, default=6, help="issues younger than this are 'too new'")
    ap.add_argument("--title-width", type=int, default=50)
    ap.add_argument("--note", action="store_true", help="also print a drafted scout-notes-create payload for the no-report rows")
    ap.add_argument("--scout", help="skill_name of the scout the note is addressed to (required with --note)")
    ap.add_argument("--note-days", type=int, default=14, help="expires_at for the drafted note, days from now")
    args = ap.parse_args()
    if args.note and not args.scout:
        ap.error("--note needs --scout <skill_name>: the scout that files reports for your issues")

    now = dt.datetime.now(dt.timezone.utc)
    owner, name = args.repo.split("/")
    if args.issues:
        raw = json.loads(Path(args.issues).read_text())
    else:
        me = args.me or subprocess.run(["gh", "api", "user", "--jq", ".login"], check=True, capture_output=True, text=True).stdout.strip()
        path = f"repos/{args.repo}/issues?creator={me}&state=all&sort=created&direction=desc&per_page={min(args.limit + 10, 100)}"
        raw = json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)
    issues = [i for i in raw if "pull_request" not in i][: args.limit]

    # Reports that name an issue in their title or summary.
    link_re = re.compile(rf"github\.com/{re.escape(owner)}/{re.escape(name)}/issues/(\d+)", re.I)
    ref_re = re.compile(r"(?<![\w/])#(\d{1,6})\b")
    by_issue: dict[int, list[dict]] = {}
    seen: set[str] = set()
    for path in args.reports:
        for r in results_of(load_payload(path)):
            if r["id"] in seen:
                continue
            seen.add(r["id"])
            text = f"{r.get('title') or ''} {r.get('summary') or ''}"
            numbers = {int(n) for n in link_re.findall(text)} | {int(n) for n in ref_re.findall(text)}
            for n in numbers:
                by_issue.setdefault(n, []).append(r)

    # PRs in the in-flight table that close an issue.
    by_pr: dict[int, dict] = {}
    if args.table:
        for row in json.loads(Path(args.table).read_text())["rows"].values():
            pr = row.get("pr")
            if not pr:
                continue
            for number, repo in pr.get("issues") or []:
                if repo.lower() == args.repo.lower():
                    by_pr[number] = row

    rows = []
    for issue in issues:
        n = issue["number"]
        issue_age, hours = age(issue["created_at"], now)
        hits = by_issue.get(n, [])
        pr_row = by_pr.get(n)
        if hits:
            best = sorted(hits, key=lambda r: r["created_at"], reverse=True)[0]
            verdict, key = f"report {best['status'].replace('_', ' ')}", "report"
            report_cell = f"[{trim(best['title'], 40)}]({best['_posthogUrl']})" + (f" +{len(hits) - 1}" if len(hits) > 1 else "")
        elif pr_row:
            verdict, key = f"covered by PR #{pr_row['pr']['number']}", "covered"
            report_cell = f"[{trim(pr_row['report_title'], 40)}]({pr_row['report_url']})"
        elif issue["state"] == "closed":
            verdict, key, report_cell = "closed, no report", "closed", "–"
        elif hours < args.fresh_hours:
            verdict, key, report_cell = "too new", "too new", "–"
        else:
            verdict, key, report_cell = "no report", "no report", "–"
        labels = [l["name"] for l in issue.get("labels") or []]
        rows.append({
            "number": n, "title": issue["title"], "url": issue["html_url"], "state": issue["state"],
            "created_at": issue["created_at"], "age": issue_age, "labels": labels,
            "verdict": verdict, "verdict_key": key, "report_cell": report_cell,
            "report_ids": [r["id"] for r in hits], "pr_row": pr_row["row"] if pr_row else None,
        })

    rows.sort(key=lambda r: r["created_at"], reverse=True)

    gaps = [r for r in rows if r["verdict_key"] == "no report"]
    lines = [f"Your recent issues without a report ({len(gaps)} of {len(rows)} in {args.repo})", "",
             "| # | Issue | Age | Report | Verdict |", "|---|---|---|---|---|"]
    table: dict[str, dict] = {}
    for i, r in enumerate(rows, 1):
        state = "" if r["state"] == "open" else " closed"
        lines.append(f"| {i} | [#{r['number']}]({r['url']}){state} {trim(r['title'], args.title_width)} | {r['age']} | {r['report_cell']} | {r['verdict']} |")
        table[str(i)] = {**r, "row": i}
    lines.append("")
    lines.append("Legend: report = a report names the issue · covered by PR = an in-flight PR closes it · too new = younger than the source's likely last run · no report = open, old enough, nothing found: verify with `inbox-reports-list {\"search\": \"<number>\"}`, then offer a scout note.")
    if gaps:
        lines.append("")
        lines.append("Scout-note candidates (draft with --scout <name> --note; create only on say-so):")
        for r in gaps:
            lines.append(f"- [#{r['number']}]({r['url']}) {r['title']}")
    if args.note and gaps:
        bullets = "\n".join(f"- [#{r['number']}]({r['url']}) {r['title']} (opened {r['created_at'][:10]}, {r['age']} ago)" for r in gaps)
        content = (
            f"**{len(gaps)} open issue{'s' if len(gaps) != 1 else ''} by {issues[0]['user']['login']} in {args.repo} "
            f"had no inbox report as of {now:%Y-%m-%d}.** Each is open, older than {args.fresh_hours:g} hours, and no report names it or closes it through a PR. "
            "On your next run, read each one and either file a report or record in your scratchpad why it does not qualify, so the gap is explained rather than silent.\n\n"
            f"{bullets}\n\nChecked against every report that names the issue in its title or summary and every in-flight PR's closing issues; "
            "a report that mentions the issue only in its artefacts would not have been seen."
        )
        payload = {"skill_name": args.scout, "content": content, "expires_at": (now + dt.timedelta(days=args.note_days)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        lines.append("")
        lines.append("Drafted note (paste on the user's go-ahead; creation is not idempotent):")
        lines.append(f"call scout-notes-create {json.dumps(payload, ensure_ascii=False)}")
    if not rows:
        lines = [f"No issues authored by you found in {args.repo}."]

    (Path(args.out) / "issue_gaps.json").write_text(json.dumps({"generated_at": now.isoformat(), "repo": args.repo, "rows": table}, indent=1))
    print("\n".join(lines))
    print(f"\nwrote {Path(args.out) / 'issue_gaps.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())