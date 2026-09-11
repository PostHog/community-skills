# Launching tasks to get PRs over the line

Most rows in the in-flight table stall on agent-sized work: an open must-fix, a red check, a conflict. A PostHog task can pick that up. This file says which rows qualify, what to write in the prompt, and how to record the launch. Creating a task is a write, so suggest first and create only on the user's say-so. Tasks need the Tasks product enabled for the organization; when `tasks-create` is refused for that reason, offer the human action instead.

## Which rows qualify

Suggest a task when the row's Next is agent work:

| Next | Task shape |
|---|---|
| `fix N must-fix` | address PostHog Review's must-fix items on the existing branch |
| `fix CI` | diagnose the failing checks and push a fix to the existing branch |
| `rebase` | resolve the conflict against the base branch, keep the PR's intent |
| `re-scope` | PR closed, report still open: decide between a fresh PR and a dismissal recommendation |

Do not suggest a task for human actions: `review`, `mark ready`, `merge (your go)`, `resolve report`, `close duplicate`, `rerun CI`, `find PR`.

Skip a row when a task on the same report already has a run in progress; two agents on one branch collide. Check with:

    call tasks-list {"origin_product": "signal_report", "status": "in_progress", "search": "<report title or PR number>"}

Run status can read `in_progress` after the work finished (see `references/tracking-reports.md`), so if the run is older than a day and the PR has not moved, treat it as finished and suggest anyway, saying so.

Cap suggestions at five per briefing. Rank by report priority, then by the smallest gap first (one must-fix before three, one failing check before ten), so the cheapest merges come first.

## The suggestion in the briefing

Under "Tasks to launch (N)", one line per suggestion, keyed by the table's row number so the user can answer "make tasks for 1, 5 and 9":

    - row 4 [#1234](pr url) fix 2 must-fix: <task title>  (report P2, PR 2h old)

Each line names the row, the PR, the action, and the task title the prompt would carry. When the user names a row that was not suggested (its Next is human work such as `review` or `merge`), say in one line why no task fits and offer the human action instead; draft one anyway if they insist. Keep the drafted prompts out of the briefing; the user asks for one if they want to read it before launching.

## Prompt template

`scripts/draft_task.py --row N --table table.json` fills this template from the row (failing check names and run ids included) and prints the `tasks-create` and link payloads. It refuses with a one-line reason when the row's Next is human work; `--action must-fix|fix-ci|rebase|re-scope` overrides that when the user insists.

`description` is handed to the agent verbatim, so it has to stand alone. Every prompt starts with the same header, then one action block.

    Continue the work for PostHog inbox report "<title>" (id <report_uuid>, <_posthogUrl>).
    The implementation PR is <pr_url> on <owner/repo>. Check it out with `gh pr checkout <pr_url>`, work on that branch, and push commits to the same PR. Do not open a second PR. If you must open a new PR, reference <_posthogUrl> in its description so the report links to it.
    Read the report's work log first: `inbox-report-artefacts-list` with report_id <report_uuid>.

Action blocks:

- **must-fix**: "The latest PostHog Review comment on the PR lists N must-fix items. Address each one, push, then reply on each review thread saying what changed. Do not silence a finding by deleting the code it points at unless the finding asks for that. Leave should-fix and consider items alone unless they are one-line changes."
- **CI**: "These checks are failing: <check names from gh pr checks>. Read their logs with `gh run view <run id> --log-failed`, fix the cause, and push. If a failure is a known flake unrelated to the diff, say so in a PR comment with the evidence instead of retrying blindly. Do not skip or disable a check."
- **rebase**: "The PR conflicts with <base branch>. Merge <base branch> into the branch (or rebase if the repository prefers it), resolve conflicts so the PR keeps its stated intent, run the tests that cover the touched files, and push. Summarize the conflict resolution in a PR comment."
- **re-scope**: "The previous PR <pr_url> was closed without merging. Read why from its comments and the report's work log. Either open a fresh PR that addresses the report with what was learned, or, if the report no longer holds, write a short dismissal recommendation as a `note` artefact on the report and stop."

Set `repository` to the PR's `owner/repo`, and `title` to `<action>: <PR title>` so the task list reads like the table.

## Launching and recording

On the user's go-ahead, per task:

1. `call tasks-create {"title": "...", "description": "...", "repository": "owner/repo"}` and keep the returned `id` and `_posthogUrl`.
2. Associate the task with the report so its commits land on the report's work log:

       call inbox-report-artefacts-create {"report_id": "<report_uuid>", "artefact_type": "task_run", "content": {"task_id": "<task id>", "product": "tasks", "type": "agent_run"}}

   If that returns a 400 about a missing task id, the association is not available from this session; note it in the working-set entry and move on.
3. Add or update the report's `working-set.md` entry: `surface: task`, the task id and title in `notes`, `next: check the task's run, then the PR`.
4. Tell the user the task URL. The tool description says to open the URL to start the run; in practice a run has often started on its own a few minutes after creation. Check `tasks-runs-list` after about ten minutes and ask the user to open the URL only if no run appears.

Next session, the table row shows whether the PR moved. If the task ran and the PR is unchanged, read the run with `tasks-runs-list` before launching another.