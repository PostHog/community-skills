# Daily triage runbook

The session loop: pull the live picture, render the table, reconcile what you track, tell the user what needs them, close the loop. The calls below are the schema; skip `info` for them. Load the `inbox-exploration` skill only when a step needs report mechanics beyond listing (drill-in, claim, resolve, dismiss, snooze), or when the pull comes back empty and the source-config check is needed.

## 1. Load state

Read `HANDOVER.md`.

## 2. Pull the live picture

All calls use `scope: for_me`, which selects the reports where you are a suggested reviewer (the reports whose relevant commits are yours).

    call inbox-reports-list {"scope": "for_me", "view": "monitoring", "sort": "last_updated", "limit": 25}
    call inbox-reports-list {"scope": "for_me", "view": "actionable", "sort": "last_updated", "limit": 25}
    call inbox-reports-list {"scope": "for_me", "view": "monitoring", "count_only": true}
    call inbox-reports-list {"scope": "for_me", "view": "actionable", "count_only": true}
    call inbox-reports-list {"scope": "for_me", "view": "needs_input", "count_only": true}

Run all five in one batch with `--json`. The monitoring and actionable lists can be large and may land in persisted tool-result files; note both paths, `render_table.py` and `pr_candidates.py` read them directly (raw payload or the `[{"type": "text", "text": ...}]` wrapper). Save small inline outputs the scripts need (the tasks list, retrieved reports) to the scratchpad with a heredoc.

`monitoring` is reports with an implementation PR. `actionable` is ready reports with no PR yet. `needs_input` is reports waiting on a human. Each row carries `title`, `status`, `priority`, `implementation_pr_url`, `created_at`, `updated_at`, and `_posthogUrl` (the link to use). The counts go in the section headings.

When every count is zero, run inbox-exploration's empty-inbox check before saying the inbox is empty: the right reply depends on whether signal sources are configured. When `for_me` is empty but the project is not, say that nothing is tied to code you authored recently; search the project only when the user asks.

Reports an agent is still working on with no PR yet:

    call tasks-list {"origin_product": "signal_report", "status": "in_progress"}

The script reads the report id out of each task's description and lists the ones it cannot place; `inbox-reports-retrieve` those, save the outputs, and re-run with `--agent-reports` so the ones with `is_suggested_reviewer: true` become rows.

`scripts/render_table.py` does the PR enrichment and everything in step 3. Do not redo it by hand:

    python3 scripts/render_table.py --reports <monitoring json> --tasks <tasks json> --out <scratch>/my-inbox [--pr-override <report_uuid>=<pr_url>] [--agent-reports <retrieve json> ...]

It fans out `gh pr view` and `gh issue view` in parallel (the issue call because `closingIssuesReferences` carries no state), caches both under `<out>/prs/` for ten minutes so a re-run is free, prints the table with its legend, the rows whose Next is agent work, and the agent tasks still to verify, and writes `table.json` for `draft_task.py`. `--pr-override` renders a monitoring row whose `implementation_pr_url` is empty; the durable fix is to attach the PR to the report (step 6). A cold run over 25 PRs takes about 15 seconds.

The signals come from what `gh pr view` returns:

- **PostHog Review** (the Review Hog, when it runs on the repository): its status comment on the PR, headed "PostHog Review reviewed this pull request", says `Found **N Must fix**, ...`. The script reads the latest such comment or review. An open must-fix means not ready, whatever the approvals say. Repositories without PostHog Review simply carry no `hogN` token.
- **Human**: `reviewDecision`, and whether your login appears in `reviews`.
- **CI**: failing, pending, and passing counts from `statusCheckRollup`.
- **Conflict**: `mergeable` is `CONFLICTING`.

Pull `inbox-report-artefacts-list` only for a row that needs explaining (commits, task runs, judgments, and the `suggested_reviewers` artefact whose `relevant_commits` say which of your commits put you on the report).

## 3. Render the in-flight table

`render_table.py` renders this section; the spec below is what it encodes, and a change to the rules goes in both places.

One row per report, six columns, one line per row, short tokens rather than sentences. Heading "In flight with a PR (N of M)" when the list is capped.

| # | Report | Age | PR · Issue | Signals | Next |

- **#**: the row number, 1 upward in table order. It is the handle for everything that follows in the session ("make tasks for 1, 5 and 9", "tell me about 3"), so keep the numbering fixed until the table is re-rendered, and say when it has been.
- **Report**: priority, then the title linked to `_posthogUrl`, trimmed to about 45 characters. Append the inbox status only when it is not `ready` (for example `· needs input`).
- **Age**: `report / PR` since created, compact units m, h, d, w, for example `2h / 52m`. Bold an age over 14d.
- **PR · Issue**: the linked PR number with a state token only when not plain open (`draft`, `merged`, `closed`), the author only when it is not the PostHog bot, the repository name in brackets only when the table spans more than one repository, then `·` and each closing issue as a linked number with `✓` when closed. `agent working` with a task link when there is no PR yet.
- **Signals**: space-separated tokens, present only when they carry information: `you✓` (your approval) or `you💬`, `appr` (someone else approved), `hogN` (N open PostHog Review must-fixes), `CI✓` or `CIN✗` (N failing checks) or `CIN⏳` (N running), `conflict`, `dup` (shares a closing issue with another open PR).
- **Next**: one action of three words or fewer, the first that applies: `rebase`, `fix N must-fix`, `fix CI`, `review`, `mark ready`, `merge (your go)`, `resolve report` (PR merged, report still open), `re-scope` (PR closed, report still open), `close duplicate` (two PRs close the same issue), `rerun CI` (the head commit's checks were cancelled and nothing failed), `CI running`, `find PR` (monitoring row with no linked PR), `wait on agent` (agent-working row). For a duplicate pair the PR with fewer blockers (must-fixes, failing checks, draft, conflict) keeps its own Next and the other gets `close duplicate`; ties go to the older PR.

Order: newest report first, whatever the PR state; merged and closed rows sit wherever their report age puts them. Every report link is the full `_posthogUrl`, never the inbox root. Add a one-line legend under the table. When there are no rows, say so in one line.

## 3b. Rank the Create PR candidates

`pr_candidates.py` renders this section from the 25-row actionable pull; the rules below are what it encodes, and a change goes to both places. No network calls, so it runs in under a second.

    python3 scripts/pr_candidates.py --reports <actionable json> --tasks <tasks json> --out <scratch>/my-inbox

One row per report, six columns: `#`, Report (priority, title linked to `_posthogUrl`), Age (since created), Signals (`sigN` plus the first two source products), Shape (what the summary carries: `N paths` for file paths in backticks, `solution` for a Solution, Action, or Recommended section, `issue #N` for a linked GitHub issue, `cites #N` for an existing PR the summary names), and Verdict. Heading "Create PR candidates (N of 25 recent, M actionable)".

Verdict is the first that applies:

- `agent working`: an in-progress `signal_report` task names the report. Two agents on one report collide.
- `digest`: the title says digest, summarizer, or session summary, or the summary opens "Summary for". A scheduled scout roll-up has nothing to implement.
- `has issue #N`: the summary links a GitHub issue. The issue is the handle; work it from the issue, not from Create PR.
- `needs decision`: the summary says the fix is a human or configuration decision, not a code change.
- `check PR #N`: the summary cites an existing PR. Read that PR first; it may already be the fix, or the report may say to build on it.
- `needs research`: no file paths and no solution section. Too thin to hand an agent; a Create PR run would start by re-researching.
- `stale, re-verify`: older than 14 days. The cited code may have moved; re-read the report before pressing anything.
- `create PR`: everything else, meaning a code-shaped fix with a solution section, no competing handle, recent. Open the report and press Create PR.

Order: newest report first; the Verdict column says which rows are ready, so scan it rather than the position. The script writes `candidates.json` keyed by row number so a later step can pick rows by number. The verdict is a reading of the summary, not a verification: rule 2 in the skill body still applies before anyone presses the button, and this skill never presses it.

## 3c. List your issues that have no report (optional)

Run this step when you file GitHub issues that the inbox is expected to pick up, through the GitHub signal source or a scout that reads issues. `issue_gaps.py` renders it; the rules below are what it encodes, and a change goes to both places. It matches issue numbers, never titles.

    call inbox-reports-list {"scope": "entire_project", "view": "all", "include_all_statuses": true, "source_product": "github", "ordering": "-created_at", "limit": 100}
    python3 scripts/issue_gaps.py --repo <owner/repo> --reports <github-source json> <actionable json> <monitoring json> --table <out>/table.json --out <scratch>/my-inbox [--issues <saved gh output>] [--scout <scout skill_name> --note]

Add a scout-filtered pull (`"scout": "<skill_name>"` in place of `source_product`) to `--reports` when a scout of yours files issue reports. The script runs `gh api repos/<owner>/<repo>/issues?creator=<you>` itself when `--issues` is not passed.

One row per issue you created, newest 25, five columns: `#`, Issue (number linked, `closed` when closed, title), Age, Report (the covering report linked, when there is one), Verdict. Heading "Your recent issues without a report (N of 25 in owner/repo)".

Verdict is the first that applies:

- `report <status>`: a report's title or summary names the issue, by link or `#number`. The newest such report is linked; `+N` counts the others.
- `covered by PR #N`: an in-flight PR closes the issue (from `table.json`), so that PR's report is the handle even though it never named the issue.
- `closed, no report`: the issue is already closed. Nothing for the inbox to do.
- `too new`: younger than six hours (`--fresh-hours`, tune it to how often your source or scout runs). It may not have been seen yet.
- `no report`: open, old enough, nothing found. A scout-note candidate.

Order: newest issue first; the Verdict column carries the classification. The script writes `issue_gaps.json` and lists the `no report` rows.

Before offering a note, do two checks the script cannot: run `call inbox-reports-list {"scope": "entire_project", "include_all_statuses": true, "search": "<number>", "limit": 3}` for each `no report` row (a report can name the issue only in artefacts, and a bare number can also match unrelated text, so read the hit), and scan the in-flight table for a PR whose title matches the issue but does not close it. Either finding moves the row out of the note; say so in the briefing.

The note is one `scout-notes-create` addressed to the scout named with `--scout`, listing the remaining issues and asking the scout to file a report or record why each does not qualify. `--note` prints the payload with a 14-day `expires_at`. Notes are advisory input the scout weighs, not commands; keep the prose to facts about the issues.

## 4. Reconcile the working set

Read `working-set.md`. For each entry:

- If its report is a row in the table, copy the row's PR state, signals, and Next into the entry. No second fetch.
- Otherwise `call inbox-reports-retrieve {"id": "<report_uuid>"}` and, for a linked PR, `gh pr view`. Watch for: `status` changed (especially suppressed or resolved), `already_addressed: true`, `implementation_pr_url` newly set by someone else, `assignee` changed, `signal_count` grown since pickup.
- Non-PR surfaces: the `tasks-*` tools for a task; otherwise the handle recorded in the entry (session name, branch, doc). Task run status is not a completion signal; see `references/tracking-reports.md`.

Stamp `last checked <date>` on each entry. Never skip one; an unreconciled entry is rumor, not status.

## 5. Brief the user

Titles and links, never bare ids. Shape:

    ## Inbox briefing, <date>

    In flight with a PR (N of M)
    <the table from step 3>

    Needs you now (N)
    - the table rows whose Next is yours to do (merge, close duplicate, resolve report, review, mark ready)
    - working-set entries with changes requested or a stalled surface

    Create PR candidates (N of 25 recent, M actionable, K needing input)
    <the table from step 3b>
    - for each create PR row not already tracked, one line on why it is ready, then: open the report and press Create PR?   (propose, never auto-add, never press the button yourself)

    Your issues without a report (N of 25)   (only when step 3c ran)
    <the no-report and too-new rows from step 3c; the full table only when asked>
    - one line per no-report row that survived the two checks, then: leave one scout note covering them?   (create only on say-so)

    Stale (N)
    - bold ages from the table, and Watching entries older than 7 days: promote or drop?

    Tasks to launch (N)
    - row <#> [#<pr>](url) <action>: <task title>  (report P<n>, PR <age>)
    (the script lists the qualifying rows under the table; rank and cap them per `references/launching-tasks.md`; the user answers with table row numbers, "make tasks for 1, 5 and 9")

## 6. Close the loop

After the user reacts:

- Pickups and close-outs: follow `references/tracking-reports.md`.
- `find PR` rows: when the user names the PR, attach it with `call inbox-reports-claim {"id": "<report_uuid>", "pr_url": "<pr url>"}`. This also claims the report for you; pass `release: true` in a later call if you do not own the work.
- Task launches: `python3 scripts/draft_task.py --row N --table <out>/table.json` prints the create and link payloads; create, link to the report, record in the working set, and hand back the task URL, per `references/launching-tasks.md`.
- Resolve, dismiss, or snooze only on explicit say-so, via `inbox-reports-set-state` with a canonical `dismissal_reason` and a real note.
- Scout notes: `python3 scripts/issue_gaps.py ... --scout <name> --note` prints the `scout-notes-create` payload. First `call scout-notes-list {"skill_name": "<name>", "include_general": false, "limit": 20, "content_max_chars": 200}` and drop any issue an active note already names; creation is not idempotent. Create on say-so, then put the note id, its expiry, and the issue numbers in `HANDOVER.md` so the next session can check whether the scout filed reports and retire the note with `scout-notes-delete` once it has.
- Update `working-set.md` and add a `CHANGELOG.md` line only if the workflow itself changed. Build every `skill-update` with `scripts/skill_payload.py`: put each `old` and `new` in a scratch file with a heredoc, run the script, paste the printed `call` line. Never hand-assemble the JSON; a missing bracket or a retyped `old` costs a round trip each.
- Overwrite `HANDOVER.md` with `skill-file-delete` then `skill-file-create` (full new text, `content_type` `text/markdown`). Two version bumps, but no `old` to mismatch. Keep its three headings so the next session can scan it.