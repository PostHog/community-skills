# Tracking reports through the working set

Lifecycle and mechanics for entries in `working-set.md`. The working set holds only the reports you personally own or are babysitting; the in-flight table in `references/daily-triage.md` already shows everything you are a reviewer on, so do not copy it here.

## Picking up a report

1. Verify before committing. Read the report and its work log:

       call inbox-reports-retrieve {"id": "<uuid>"}
       call inbox-report-artefacts-list {"report_id": "<uuid>"}

   and confirm the diagnosis against the actual code (inbox-exploration, "act on an actionable report", step 2). If it does not hold up, it is a dismissal candidate, not a pickup.
2. Check `already_addressed`, `implementation_pr_url`, `work_state`, and `assignee`; do not duplicate work already in flight, and make a takeover deliberate when someone else owns the report. Two reports can produce two PRs for the same issue, so also check the PR's `closingIssuesReferences` against the other open PRs in the table.
3. Claim the report so teammates and agents see it is owned:

       call inbox-reports-claim {"id": "<uuid>"}

   Claims do not expire. Release with `{"id": "<uuid>", "release": true}` whenever you walk away without landing a fix, including when you dismiss the report instead.
4. Add an entry (template at the top of `working-set.md`) under the right section:
   - **Active, PR in flight** once a branch or PR exists.
   - **Active, non-PR surfaces** for work happening as a PostHog task, an agent session elsewhere, or manual investigation. Record enough of a handle in `notes` to find it again: task id and title, session or branch name.
   - **Watching** if it should stay on the radar but nothing has started.
5. When you open a PR for a report, attach it with `call inbox-reports-claim {"id": "<uuid>", "pr_url": "<pr url>"}` and reference the report's `_posthogUrl` in the PR description so the loop is traceable from both sides. A PR in a connected repository gets webhook updates and auto-resolves the report on merge; a PR in an unconnected repository is accepted with unknown state, so resolve that report by hand after the work lands.

## PR and CI check commands

       gh pr view <url> --json state,isDraft,reviewDecision,mergeable,statusCheckRollup,title
       gh pr checks <url>                      # per-check pass/fail
       gh pr list --author "@me" --state open  # sweep: anything open not in the working set?

The `--author "@me"` sweep catches PRs started from a report but never recorded here.

## Keeping entries honest

- `state` and `pr` fields carry `last checked <date>`; stamp it whenever verified live. An unstamped claim is rumor.
- `next` is always a single concrete action ("respond to review comments", "rerun flaky CI job", "wait, nothing to do"). If you cannot name one, the entry belongs in Watching or Recently closed out.
- Record the full report UUID, never a truncated prefix; `inbox-reports-retrieve` 404s on anything shorter.
- Watching entries older than about 7 days get flagged in triage: promote or drop.

## Closing out

A report leaves Active when its PR merged, the work is otherwise done, the user dropped it, or it moved permanently to someone else.

1. Set the report's end state via `inbox-reports-set-state` (user's go-ahead first, always with a `dismissal_note`). `resolved` is terminal; a recurrence starts a fresh report:
   - fix shipped as a PR in a connected repository: **do nothing on merge**, the GitHub webhook auto-resolves the report. Hand-resolve only if the report is still `ready` well after the merge, and say so in the note.
   - work done that no PR merge will cover (a PR in an unconnected repository, a skill edit, a config change, a report with no repository): `state: "resolved"`, with `dismissal_reason` recording why.
   - fixed by something else or might recur: `state: "potential"` plus `already_fixed` (snooze; resurfaces if it comes back). Never this pairing when you did the fixing.
   - report was wrong: `state: "suppressed"` plus `analysis_wrong` and an evidence note.
   - real but not worth fixing: `state: "suppressed"` plus `wontfix_intentional` or `wontfix_irrelevant`.
2. Release the claim if you still hold it and the report is not resolved.
3. Move the entry to **Recently closed out** with a one-line outcome and date.
4. Prune Recently closed out entries older than about 2 weeks; immutable skill versions keep the history.

Full decision detail lives in the inbox-exploration skill's "resolve, dismiss, or snooze" workflow.

## What the inbox tabs count

The Inbox scene's tab counts are narrower than the raw reports API and default to the "For you" scope (your user as a suggested reviewer). The `inbox-reports-list` tool exposes the same presets as `view`: `actionable` (ready, no PR, actionable), `needs_input`, `monitoring` (has a PR), `resolved`, `dismissed`, `not_actionable`, `all`. Prefer `view` plus `scope: for_me` over hand-built status filters; the `actionability`, `has_implementation_pr`, `priority`, `unclaimed`, and `assignee: me` filters exist too when a preset does not fit.

## State-machine gotchas (observed live)

- Reports in `failed` processing status accept only `suppressed`; `potential` (snooze) returns 409, and `resolved` is only allowed from ready, pending_input, or suppressed.
- Un-suppressing via `state: "potential"` restores the report's pre-suppression status rather than leaving it snoozed. There is no way to convert a failed report into a snoozed one: suppress with a clear note and rely on new signals creating a fresh report if the issue recurs.

## Task-run status is not a completion signal (observed live)

A PostHog task run can finish its work and still read `status: in_progress`, `completed_at: null`, `artifacts[]` empty, indefinitely. Never conclude "the run has not finished" from run status alone. Reconcile in this order:

1. **Report status**, the reliable signal: `inbox-reports-retrieve` per report, which also surfaces `dismissal_reason` and `dismissal_note`.
2. **The artefact trail**: `inbox-report-artefacts-list`, or for a skill fix, `skill-get` on the target skill; a version published inside the run's window is proof the work landed.
3. **Run status**, last, and only as a hint. `tasks-list` buckets by the most recent run's status, so it inherits the same lie; it is still the cheapest way to find a batch.

## Edit mechanics

`working-set.md` changes go through `skill-update` with `file_edits` (find/replace), never delete-and-recreate, never a full-file rewrite for a one-entry change. Chain `base_version` from each write's result. The `working-with-skills` skill that ships with the PostHog MCP covers what to do when a write misbehaves.