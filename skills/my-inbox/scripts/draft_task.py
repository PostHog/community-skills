#!/usr/bin/env python3
"""Draft the tasks-create payload for one in-flight table row.

Reads table.json written by render_table.py, picks the action block from
references/launching-tasks.md that matches the row's Next, and prints the two
`call` payloads: tasks-create, then the task_run artefact that links the task to
the report. Nothing is sent; paste the printed lines into the PostHog MCP.

    python3 draft_task.py --row 4 [--table table.json] [--action fix-ci|must-fix|rebase|re-scope]

Exit code 1 with a one-line reason when the row's Next is human work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HEADER = (
    'Continue the work for PostHog inbox report "{title}" (id {report_id}, {report_url}).\n'
    "The implementation PR is {pr_url} on {repo}. Check it out with `gh pr checkout {pr_url}`, work on that branch, "
    "and push commits to the same PR. Do not open a second PR. If you must open a new PR, reference {report_url} "
    "in its description so the report links to it.\n"
    "Read the report's work log first: `inbox-report-artefacts-list` with report_id {report_id}.\n\n"
)

BLOCKS = {
    "must-fix": (
        "Goal: address PostHog Review's must-fix items.\n\n"
        "The latest PostHog Review comment on the PR lists {hog} must-fix item(s). Address each one, push, then reply on each "
        "review thread saying what changed. Do not silence a finding by deleting the code it points at unless the finding "
        "asks for that. Leave should-fix and consider items alone unless they are one-line changes."
    ),
    "fix-ci": (
        "Goal: get CI green on this PR.\n\n"
        "These checks are failing: {checks}. Read their logs with `gh run view <run id> --log-failed`{run_hint}, fix the "
        "cause, and push. If a failure is a known flake unrelated to the diff, say so in a PR comment with the evidence "
        "instead of retrying blindly. Do not skip or disable a check. After pushing, run `gh pr checks {number} --watch` "
        "and confirm every check passes; if new failures appear, fix those too.\n\n"
        "Leave the PostHog Review must-fix items and other review comments alone unless one of them is the direct cause of a failing check."
    ),
    "rebase": (
        "Goal: resolve the merge conflict.\n\n"
        "The PR conflicts with {base}. Merge {base} into the branch (or rebase if the repository prefers it), resolve "
        "conflicts so the PR keeps its stated intent, run the tests that cover the touched files, and push. Summarize the "
        "conflict resolution in a PR comment."
    ),
    "re-scope": (
        "Goal: decide what happens to this report now that its PR is closed.\n\n"
        "The previous PR {pr_url} was closed without merging. Read why from its comments and the report's work log. Either "
        "open a fresh PR that addresses the report with what was learned, or, if the report no longer holds, write a short "
        "dismissal recommendation as a `note` artefact on the report and stop."
    ),
}

ACTION_TITLE = {"must-fix": "fix {hog} must-fix", "fix-ci": "fix CI", "rebase": "rebase", "re-scope": "re-scope"}


def action_for(next_action: str) -> str | None:
    if next_action.startswith("fix ") and next_action.endswith("must-fix"):
        return "must-fix"
    return {"fix CI": "fix-ci", "rebase": "rebase", "re-scope": "re-scope"}.get(next_action)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", required=True)
    ap.add_argument("--table", default="table.json")
    ap.add_argument("--action", choices=sorted(BLOCKS), help="override the action inferred from Next")
    args = ap.parse_args()

    table = json.loads(Path(args.table).read_text())
    row = table["rows"].get(str(args.row))
    if row is None:
        print(f"no row {args.row} in {args.table}", file=sys.stderr)
        return 1
    pr = row.get("pr")
    if not pr:
        print(f"row {args.row} has no PR; nothing for an agent to continue", file=sys.stderr)
        return 1
    action = args.action or action_for(row["next"])
    if action is None:
        print(f"row {args.row} Next is '{row['next']}', which is human work; no task fits. Pass --action to draft one anyway.", file=sys.stderr)
        return 1

    fields = {
        "title": row["report_title"],
        "report_id": row["report_id"],
        "report_url": row["report_url"],
        "pr_url": pr["url"],
        "repo": pr["repo"],
        "number": pr["number"],
        "base": pr.get("base") or "main",
        "hog": pr.get("hog") or 0,
    }
    checks = pr.get("fail") or []
    fields["checks"] = ", ".join(f"`{c['name']}`" for c in checks) or "(see gh pr checks)"
    run_ids = sorted({c["run_id"] for c in checks if c.get("run_id")})
    fields["run_hint"] = f" (run id{'s' if len(run_ids) > 1 else ''} {', '.join(run_ids)})" if run_ids else ""

    description = HEADER.format(**fields) + BLOCKS[action].format(**fields)
    title = f"{ACTION_TITLE[action].format(**fields)}: {row['report_title']}"
    create = {"title": title, "description": description, "repository": pr["repo"]}
    print("# 1. create the task")
    print(f"call tasks-create {json.dumps(create, ensure_ascii=False)}")
    print()
    print("# 2. link it to the report (fill in the task id from step 1)")
    artefact = {"report_id": row["report_id"], "artefact_type": "task_run", "content": {"task_id": "<task id>", "product": "tasks", "type": "agent_run"}}
    print(f"call inbox-report-artefacts-create {json.dumps(artefact, ensure_ascii=False)}")
    print()
    print(f"# working-set line: surface: task · {title}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())