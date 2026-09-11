#!/usr/bin/env python3
"""Render the my-inbox in-flight table from inbox list output plus gh.

Inputs are the JSON the PostHog MCP returned (either the persisted tool-result
file, which wraps the payload as [{"type": "text", "text": "<json>"}], or the raw
payload). The script maps every report to its PR, enriches it with `gh`, applies
the signal and next-action rules from references/daily-triage.md, and prints the
markdown table. It also writes <out>/table.json (rows keyed by row number, for
draft_task.py) and caches gh results under <out>/prs/.

    python3 render_table.py --reports <monitoring.json> [--tasks <tasks.json>]
        [--agent-reports <retrieve.json> ...] [--pr-override <uuid>=<pr_url> ...]
        [--me <github login>] [--out <dir>] [--cache-minutes 10] [--total 100]

Signals come only from what any GitHub repository carries: human reviews, CI
checks, mergeability, and the PostHog Review status comment when that product
runs on the repository. Needs python3 and an authenticated `gh`. No other
dependencies.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PR_FIELDS = (
    "number,url,title,state,isDraft,author,createdAt,updatedAt,baseRefName,"
    "closingIssuesReferences,labels,reviewDecision,reviews,comments,statusCheckRollup,mergeable"
)
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
PR_URL_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)")
# PostHog Review posts a status comment headed "PostHog Review reviewed this pull request"
# with a line "Found **N Must fix**, ..."; older versions posted a review headed "# PostHog Review".
REVIEW_HOG_RE = re.compile(r"PostHog Review", re.I)
REVIEW_HOG_RUNNING_RE = re.compile(r"PostHog Review is reviewing", re.I)
MUST_FIX_RE = re.compile(r"Found \*\*(\d+) must[- ]fix", re.I)
BOT_AUTHORS = {"app/posthog", "posthog"}
HUMAN_NEXT = {"review", "mark ready", "merge (your go)", "resolve report", "close duplicate", "find PR", "rerun CI", "wait on agent"}


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


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def gh_cached(cache_dir: Path, key: str, cmd: list[str], cache_minutes: int) -> dict | None:
    cache = cache_dir / f"{key}.json"
    if cache.exists():
        age = dt.datetime.now().timestamp() - cache.stat().st_mtime
        if age < cache_minutes * 60:
            return json.loads(cache.read_text())
    try:
        out = run(cmd)
    except subprocess.CalledProcessError as exc:
        print(f"warn: {' '.join(cmd)} failed: {exc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    cache.write_text(out)
    return json.loads(out)


def fetch_pr(cache_dir: Path, repo: str, number: int, cache_minutes: int) -> dict | None:
    key = f"pr_{repo.replace('/', '_')}_{number}"
    return gh_cached(cache_dir, key, ["gh", "pr", "view", str(number), "--repo", repo, "--json", PR_FIELDS], cache_minutes)


def fetch_issue(cache_dir: Path, repo: str, number: int, cache_minutes: int) -> dict | None:
    key = f"issue_{repo.replace('/', '_')}_{number}"
    return gh_cached(cache_dir, key, ["gh", "issue", "view", str(number), "--repo", repo, "--json", "number,url,state"], cache_minutes)


def age(iso: str, now: dt.datetime) -> tuple[str, bool]:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    minutes = int((now - t).total_seconds() // 60)
    if minutes < 60:
        return f"{minutes}m", False
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h", False
    days = hours // 24
    if days < 14:
        return f"{days}d", False
    return (f"{days // 7}w" if days >= 21 else f"{days}d"), True


def review_hog_must_fixes(pr: dict) -> int | None:
    """Open must-fix count from the latest PostHog Review comment or review, None when it never ran or is still running."""
    posts = []
    for post in (pr.get("comments") or []) + (pr.get("reviews") or []):
        body = post.get("body") or ""
        if REVIEW_HOG_RE.search(body):
            posts.append((post.get("createdAt") or post.get("submittedAt") or "", body))
    hog = None
    for _, body in sorted(posts):
        if REVIEW_HOG_RUNNING_RE.search(body):
            hog = None
            continue
        match = MUST_FIX_RE.search(body)
        hog = int(match.group(1)) if match else 0
    return hog


def classify_pr(pr: dict, me: str) -> dict:
    my_states = [r["state"] for r in pr["reviews"] if r["author"]["login"] == me]
    others = sorted({r["author"]["login"] for r in pr["reviews"] if r["state"] == "APPROVED" and r["author"]["login"] != me})
    fail: list[dict] = []
    running = cancelled = ok = 0
    for check in pr["statusCheckRollup"]:
        name = check.get("name") or check.get("context") or ""
        if check.get("status") and check["status"] != "COMPLETED":
            running += 1
            continue
        conclusion = check.get("conclusion") or check.get("state") or ""
        if conclusion in ("FAILURE", "ERROR", "TIMED_OUT", "STARTUP_FAILURE"):
            run_match = re.search(r"/actions/runs/(\d+)", check.get("detailsUrl") or check.get("targetUrl") or "")
            fail.append({"name": name, "run_id": run_match.group(1) if run_match else None})
        elif conclusion == "CANCELLED":
            cancelled += 1
        else:
            ok += 1
    issues = [(i["number"], f"{i['repository']['owner']['login']}/{i['repository']['name']}") for i in pr["closingIssuesReferences"]]
    return {
        "number": pr["number"],
        "url": pr["url"],
        "title": pr.get("title", ""),
        "repo": "/".join(pr["url"].split("/")[3:5]),
        "base": pr.get("baseRefName") or "main",
        "state": pr["state"],
        "draft": pr["isDraft"],
        "author": pr["author"]["login"],
        "created": pr["createdAt"],
        "updated": pr["updatedAt"],
        "hog": review_hog_must_fixes(pr),
        "me": my_states,
        "others": others,
        "fail": fail,
        "running": running,
        "cancelled": cancelled,
        "ok": ok,
        "mergeable": pr["mergeable"],
        "review_decision": pr["reviewDecision"],
        "issues": issues,
    }


def signals_of(p: dict) -> list[str]:
    sig = []
    if "APPROVED" in p["me"]:
        sig.append("you✓")
    elif p["me"]:
        sig.append("you💬")
    if p["others"]:
        sig.append("appr")
    if p["hog"]:
        sig.append(f"hog{p['hog']}")
    if p["state"] == "OPEN":
        if p["running"]:
            sig.append(f"CI{p['running']}⏳")
        elif p["fail"]:
            sig.append(f"CI{len(p['fail'])}✗")
        elif p["cancelled"]:
            sig.append(f"CI{p['cancelled']} cancelled")
        else:
            sig.append("CI✓")
    if p["mergeable"] == "CONFLICTING":
        sig.append("conflict")
    return sig


def blockers(p: dict) -> int:
    return (p["hog"] or 0) + len(p["fail"]) + int(p["draft"]) + int(p["mergeable"] == "CONFLICTING")


def next_of(p: dict, duplicate_loser: bool) -> str:
    if p["state"] == "MERGED":
        return "resolve report"
    if p["state"] == "CLOSED":
        return "re-scope"
    if duplicate_loser:
        return "close duplicate"
    if p["mergeable"] == "CONFLICTING":
        return "rebase"
    if p["hog"]:
        return f"fix {p['hog']} must-fix"
    if p["fail"] and not p["running"]:
        return "fix CI"
    if p["running"]:
        return "CI running"
    if p["cancelled"]:
        return "rerun CI"
    if p["draft"]:
        return "mark ready"
    if "APPROVED" in p["me"] or p["others"] or p["review_decision"] == "APPROVED":
        return "merge (your go)"
    return "review"


def trim(title: str, width: int) -> str:
    return title if len(title) <= width + 3 else title[:width].rstrip() + "…"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", required=True, help="inbox-reports-list output (monitoring view)")
    ap.add_argument("--tasks", help="tasks-list output (origin_product=signal_report, status=in_progress)")
    ap.add_argument("--agent-reports", nargs="*", default=[], help="inbox-reports-retrieve outputs for agent-working reports")
    ap.add_argument("--pr-override", nargs="*", default=[], help="<report_uuid>=<pr_url> for reports with no implementation_pr_url")
    ap.add_argument("--me", help="your GitHub login (default: gh api user)")
    ap.add_argument("--out", default=".", help="directory for table.json and the gh cache")
    ap.add_argument("--cache-minutes", type=int, default=10)
    ap.add_argument("--total", type=int, help="monitoring count for the heading, if the list was capped")
    ap.add_argument("--title-width", type=int, default=45)
    args = ap.parse_args()

    out = Path(args.out)
    cache_dir = out / "prs"
    cache_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    me = args.me or run(["gh", "api", "user", "--jq", ".login"]).strip()
    overrides = dict(item.split("=", 1) for item in args.pr_override)

    payload = load_payload(args.reports)
    reports = results_of(payload)
    total = args.total or (payload.get("count") if isinstance(payload, dict) else None) or len(reports)

    # Map each report to a PR and fan out to gh.
    targets: list[tuple[dict, str | None]] = []
    for report in reports:
        url = report.get("implementation_pr_url") or overrides.get(report["id"])
        targets.append((report, url))

    def enrich(target: tuple[dict, str | None]) -> dict | None:
        _, url = target
        if not url:
            return None
        match = PR_URL_RE.match(url)
        if not match:
            return None
        repo = f"{match.group(1)}/{match.group(2)}"
        pr = fetch_pr(cache_dir, repo, int(match.group(3)), args.cache_minutes)
        return classify_pr(pr, me) if pr else None

    with ThreadPoolExecutor(max_workers=8) as pool:
        enriched = list(pool.map(enrich, targets))

    issue_keys = {(repo, number) for p in enriched if p for number, repo in p["issues"]}
    with ThreadPoolExecutor(max_workers=8) as pool:
        issue_states = dict(zip(issue_keys, pool.map(lambda k: fetch_issue(cache_dir, k[0], k[1], args.cache_minutes), issue_keys)))

    # Duplicate detection: two open PRs closing the same issue. The one with fewer
    # blockers keeps its own next action; ties go to the older PR.
    by_issue: dict[tuple[str, int], list[dict]] = {}
    for p in enriched:
        if p and p["state"] == "OPEN":
            for number, repo in p["issues"]:
                by_issue.setdefault((repo, number), []).append(p)
    losers: set[str] = set()
    for group in by_issue.values():
        if len(group) < 2:
            continue
        ranked = sorted(group, key=lambda p: (blockers(p), p["created"]))
        for p in ranked[1:]:
            losers.add(p["url"])

    # The repository name only earns a place in the cell when the table spans more than one.
    repos = {p["repo"].lower() for p in enriched if p}
    show_repo = len(repos) > 1

    rows: list[dict] = []
    for (report, url), p in zip(targets, enriched):
        report_age, report_old = age(report["created_at"], now)
        base = {
            "report_id": report["id"],
            "report_title": report["title"],
            "report_url": report["_posthogUrl"],
            "priority": report.get("priority"),
            "status": report["status"],
            "report_age": report_age,
            "report_old": report_old,
            "created_at": report["created_at"],
        }
        if not p:
            rows.append({**base, "group": 0, "pr": None, "pr_cell": "none linked" if not url else f"[{url}]({url}) (gh failed)", "signals": [], "next": "find PR"})
            continue
        pr_age, pr_old = age(p["created"], now)
        state_tokens = []
        if p["state"] == "MERGED":
            state_tokens.append("merged")
        elif p["state"] == "CLOSED":
            state_tokens.append("closed")
        elif p["draft"]:
            state_tokens.append("draft")
        if p["author"] not in BOT_AUTHORS:
            state_tokens.append(p["author"])
        cell = f"[#{p['number']}]({p['url']})" + (" " + " ".join(state_tokens) if state_tokens else "")
        if show_repo:
            cell += f" ({p['repo'].split('/')[1]})"
        issue_cells = []
        for number, repo in p["issues"]:
            state = (issue_states.get((repo, number)) or {}).get("state")
            issue_cells.append(f"[#{number}](https://github.com/{repo}/issues/{number}){'✓' if state == 'CLOSED' else ''}")
        if issue_cells:
            cell += " · " + " ".join(issue_cells)
        dup = p["url"] in losers
        rows.append({
            **base,
            "group": 0 if p["state"] == "OPEN" else 2,
            "pr": p,
            "pr_age": pr_age,
            "pr_old": pr_old,
            "pr_cell": cell,
            "signals": signals_of(p) + (["dup"] if dup else []),
            "next": next_of(p, dup),
        })

    # Agent-working rows: in-progress signal_report tasks whose report is for_me and not already in the table.
    agent_candidates: list[dict] = []
    if args.tasks:
        table_ids = {r["report_id"] for r in rows}
        agent_reports = {}
        for path in args.agent_reports:
            for r in results_of(load_payload(path)):
                agent_reports[r["id"]] = r
        for task in results_of(load_payload(args.tasks)):
            found = UUID_RE.findall(task.get("description") or "")
            report_id = found[0] if found else None
            if not report_id or report_id in table_ids:
                continue
            task_url = task.get("_posthogUrl") or ""
            report = agent_reports.get(report_id)
            if report is None:
                agent_candidates.append({"report_id": report_id, "task_number": task.get("task_number"), "task_url": task_url, "title": task.get("title")})
                continue
            if not report.get("is_suggested_reviewer"):
                continue
            report_age, report_old = age(report["created_at"], now)
            rows.append({
                "report_id": report_id,
                "report_title": report["title"],
                "report_url": report["_posthogUrl"],
                "priority": report.get("priority"),
                "status": report["status"],
                "report_age": report_age,
                "report_old": report_old,
                "created_at": report["created_at"],
                "group": 1,
                "pr": None,
                "pr_age": "–",
                "pr_old": False,
                "pr_cell": f"agent working · [task {task.get('task_number')}]({task_url})",
                "signals": [],
                "next": "wait on agent",
                "task_url": task_url,
            })

    # Newest report first, whatever the PR state.
    rows.sort(key=lambda r: r["created_at"], reverse=True)

    lines = [f"In flight with a PR ({len(rows)} of {total})", "", "| # | Report | Age | PR · Issue | Signals | Next |", "|---|---|---|---|---|---|"]
    table: dict[str, dict] = {}
    for i, r in enumerate(rows, 1):
        title = trim(r["report_title"], args.title_width)
        status = "" if r["status"] == "ready" else f" · {r['status'].replace('_', ' ')}"
        pri = r["priority"] or "–"
        ra = f"**{r['report_age']}**" if r["report_old"] else r["report_age"]
        pa = f"**{r.get('pr_age', '–')}**" if r.get("pr_old") else r.get("pr_age", "–")
        lines.append(f"| {i} | {pri} [{title}]({r['report_url']}){status} | {ra} / {pa} | {r['pr_cell']} | {' '.join(r['signals'])} | {r['next']} |")
        table[str(i)] = {**r, "row": i}
    lines.append("")
    lines.append("Legend: you✓ your approval · you💬 you commented · appr someone else approved · hogN open PostHog Review must-fixes · CIN✗ failing · ⏳ running · cancelled means the head commit's checks never finished · conflict needs a rebase · dup shares a closing issue with another open PR.")
    if not rows:
        lines = ["No reports in flight with a PR."]
    if agent_candidates:
        lines.append("")
        lines.append("Agent tasks to verify (retrieve each report, then re-run with --agent-reports <file> ...):")
        for c in agent_candidates:
            lines.append(f"- report {c['report_id']} · task {c['task_number']} {c['task_url']} · {c['title']}")

    task_rows = [f"- row {r['row']} [#{r['pr']['number']}]({r['pr']['url']}) {r['next']}" for r in table.values() if r["pr"] and r["next"] not in HUMAN_NEXT and r["next"] != "CI running"]
    if task_rows:
        lines.append("")
        lines.append("Rows whose Next is agent work (draft with draft_task.py --row N):")
        lines.extend(task_rows[:12])

    (out / "table.json").write_text(json.dumps({"generated_at": now.isoformat(), "me": me, "rows": table}, indent=1))
    print("\n".join(lines))
    print(f"\nwrote {out / 'table.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())