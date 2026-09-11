# Changelog

Rolling window, last 30 days, newest first. When you add an entry, delete anything older than the window in the same edit. Older history survives in earlier immutable skill versions; do not create an archive file.

- 2026-09-10: created as the shareable version of a personal inbox skill. Signals and next actions are limited to what any GitHub repository carries (human reviews, CI, conflicts, PostHog Review must-fixes); repository-specific review bots and merge-queue tokens are gone. PostHog Review is read from its status comment as well as from PR reviews. `inbox-reports-claim` is the way to claim a report and attach its PR. The issue-gaps step is optional and takes the scout name as an argument. `HANDOVER.md` and `working-set.md` ship as empty templates.