---
name: My Inbox
description: 'Daily driver for the PostHog Self-driving Inbox: a live in-flight table
  of the reports you are a suggested reviewer on, each mapped to its GitHub PR and
  issues with age, review and CI signals, and one next action; a ranked list of reports
  ready for Create PR; and a small working set of the reports you own. Covers picking
  up a report (claiming it, attaching its PR), checking a linked PR, drafting PostHog
  tasks that push a stalled PR over the line, closing reports out, and keeping HANDOVER.md
  current between sessions. Use when someone says "my inbox", "inbox triage", "what
  inbox reports need me", "check my inbox PRs", "pick up this report", or at the start
  of a session touching in-flight inbox reports. Companion: the inbox-exploration
  skill that ships with the PostHog MCP (report mechanics; load it when acting on
  a report).'
trust_tier: community
tags:
- self-driving
- inbox
author_handle: andrewm4894
license: MIT
compatibility: PostHog MCP with the inbox-*, tasks-*, and scout-notes-* tools; gh
  CLI authenticated against the repositories the reports target; python3 for the bundled
  scripts.
---

# My inbox

Daily driver for the PostHog Self-driving Inbox. The inbox itself (reports, their statuses, the PRs agents opened for them) lives in PostHog. This skill owns what the inbox cannot see: which reports you are personally working on, on which surface, and what happened last session. The live picture is pulled from the API every session; `working-set.md` only records your own commitments.

This body is a thin index. Detail lives in the bundled files, and new detail goes in a reference file, not here.

## Environment

Run the inbox tools against the project whose inbox you use (the PostHog MCP `inbox-*` and `tasks-*` tools). `scope: for_me` resolves to the identity behind the MCP connection, so no user id is needed. GitHub state comes from `gh`, authenticated against the repositories the reports target. The triage pull needs no other skill: the exact `inbox-*` and `tasks-*` calls are written out in `references/daily-triage.md`, so skip the `info` step for them unless a call fails on schema. Load the `inbox-exploration` skill that ships with the PostHog MCP only when acting on a report (drill-in, claim, resolve, dismiss, snooze) or when the pull comes back empty and the source-config check is needed; it owns those mechanics and this skill does not repeat them.

If you installed this skill under a different name, use that name wherever a command below says `my-inbox`.

## Start here each session

1. After `skill-get`, fetch `HANDOVER.md`, `working-set.md`, `references/daily-triage.md`, `scripts/render_table.py`, and `scripts/pr_candidates.py` in one batch of `skill-file-get` calls. Read the handover first.
2. Pull the live picture, then run the scripts: the in-flight table and the Create PR candidates (`references/daily-triage.md`, steps 2, 3, and 3b). Step 3c (your GitHub issues with no report) is optional; run it when you file issues that the inbox should pick up.
3. Reconcile every `working-set.md` entry against the table and live report status (step 4).
4. Pull only the reference file or script the task needs.

## The three rules that bite hardest

1. **Live first, memory second.** Reports get resolved or suppressed server-side, PRs merge, CI flips, agents open PRs, all while nobody is looking. The table from the API is the truth; `working-set.md` is a list of what you chose to own. Never report status from the file alone, and never let the file try to mirror the whole inbox.
2. **A report is a diagnosis, not ground truth.** Before implementing anything from a report, verify the cited code and behavior actually hold (inbox-exploration's "act on an actionable report" workflow). A report that does not hold up is a dismissal candidate, not a fix.
3. **Close the loop before ending the session.** Update `working-set.md`, overwrite `HANDOVER.md` (a clobber file, not a log), add a `CHANGELOG.md` line only when the workflow itself changed. Use the smallest edit primitive (`file_edits`) and chain `base_version` between writes.

## Files

| File | Read it when |
|---|---|
| `HANDOVER.md` | First thing every session; overwrite last thing. |
| `working-set.md` | The reports you own, on any surface. Read every session; update on pickup, state change, or close-out. |
| `references/daily-triage.md` | The session loop: pull, table, reconcile, brief, close. |
| `references/tracking-reports.md` | Picking up a report (claiming it, attaching a PR), entry format, close-out decision table, state-machine and task-run gotchas. |
| `references/launching-tasks.md` | Turning a stalled table row (must-fix, red CI, conflict, closed PR) into a PostHog task: which rows qualify, the prompt template, and how to record the launch. |
| `scripts/render_table.py` | Every session: turns the list outputs plus `gh` into the numbered in-flight table and `table.json`. |
| `scripts/pr_candidates.py` | Every session: ranks the most recently updated actionable reports with no PR by readiness for Create PR, one verdict per row, and writes `candidates.json`. |
| `scripts/issue_gaps.py` | Optional: your recently created GitHub issues that no inbox report names or closes, one verdict per issue, and on `--note` a drafted steering note for a scout you name. |
| `scripts/draft_task.py` | Drafting a task for a table row: prints the `tasks-create` and link payloads from `table.json`. |
| `scripts/skill_payload.py` | Every close-out edit: assembles and validates the `skill-update` payload from files, so brackets and long `old` strings cannot drift. |
| `CHANGELOG.md` | Recent workflow changes, newest first, rolling window. |

Pull with `call skill-file-get {"skill_name": "my-inbox", "file_path": "<file>"}`. Scripts run from the scratchpad: write the fetched content to `<scratch>/my-inbox/scripts/` and run with `python3`. They need only python3 and an authenticated `gh`.

## Posture

Read-mostly on the inbox. The inbox writes are claiming a report or attaching its PR via `inbox-reports-claim`, resolve, dismiss, and snooze via `inbox-reports-set-state`, creating a PostHog task for a stalled PR via `tasks-create` (and linking it to the report), and a steering note to a scout via `scout-notes-create`, each only with the user's explicit go-ahead. Never open PRs, merge, request reviewers, or message anyone as a side effect of triage; surface the action in the Next column, suggest the task, and let the user decide. The routine writes are to this skill's own bundled files.

## Companions

- **inbox-exploration** (ships with the PostHog MCP and the PostHog plugin): inbox tool mechanics, list and retrieve and artefacts, the empty-inbox setup check, claim and release, dismiss and snooze semantics, the act-on-a-report discipline.
- **working-with-skills** and **skills-store** (ship with the PostHog MCP): how to read and edit this skill's own files reliably.
- Your repository's own CI-debugging skill, if it has one, when a tracked PR's CI is red and a diagnosis is wanted, not just a report.

## Maintaining this skill

Keep this body thin. Deterministic steps (classification, rendering, payload assembly) go in `scripts/`, not in prose; a rule a script encodes is stated once in the reference file and once in the script, and a change goes to both. New triage steps go in `references/daily-triage.md`, new tracking conventions in `references/tracking-reports.md`, new task prompt shapes in `references/launching-tasks.md`. `working-set.md` and `HANDOVER.md` are living state. Add a dated `CHANGELOG.md` line for changes to the skill or workflow, not for routine working-set updates, and on every append delete entries older than the 30-day window stated at the top of that file.
