# How PostHog uses this layout

This template is lifted from two hubs PostHog runs on its own skills store: one for the Signals scouts product (scheduled agents that scan a project and file reports) and one for the self-driving inbox (the loop from signals to report to reviewer to implementation PR). Both are worked by several agent sessions a day, from a laptop, from cloud agents, and from scheduled runs, and by the people on the team. The skill is the shared memory between all of them. One hub passed 500 versions and 50 issues in its first five weeks; the layout below is what survived that.

## The shape

- The **body** is a thin index: what the hub is, the logging rules, a file map, companions, and a maintenance contract. It barely changes across hundreds of versions. Everything that moves lives in a bundled file.
- **`issues/`** is the backlog. One numbered file per issue, and `issues/README.md` as the index with a one-line status per row. Numbers are the handles people and agents use ("issue 20"), so they never get reused, and the index always shows the title next to the number.
- **`ideas/`** is the someday list, same shape. An idea becomes an issue when someone picks it up; both indexes say so.
- **`open-prs.md`** lists PRs in flight with title and number. Sessions re-audit it against GitHub because PRs get opened from several surfaces and the file drifts both ways.
- **`HANDOVER.md`** is the in-flight state, one section per workstream. A session reads the table, then only its own section, and overwrites that section at the end. When the work lands the section is deleted.
- **`environment-notes.md`** holds the durable gotchas: where the code is, which dashboard is the source of truth, which query silently lies, which tool cannot do what its name says. It is the file that saves the most time per byte.
- **`field-feedback.md`** holds what users said, one dated block per conversation, linking the source rather than quoting it.
- **`roadmap.md`** holds ordering and rationale only. Status is never duplicated here.
- **`CHANGELOG.md`** is a rolling window, one line per change, trimmed on every append.

## A session, start to finish

A synthetic example on a hub named `billing-work`, installed from this template with `project` bound to `billing`.

1. Someone in a support channel asks why an annual-plan invoice PDF is blank. An engineer opens a Claude Code session and says "resume billing work, look at the blank invoice question".
2. The agent loads the skill, reads `HANDOVER.md` (nothing about invoices in the table) and `issues/README.md` (no matching issue), then `environment-notes.md`, which says the invoice renderer lives in one module and that the PDF cache is keyed on plan id, a gotcha a previous session recorded.
3. The agent reproduces the bug, finds the cache key collision, and opens a PR.
4. Before ending, it logs the work: `issues/04-annual-invoice-pdf-blank.md` (status pr-open, evidence, next step), a row in `issues/README.md`, the PR in `open-prs.md` with its title, one line in `CHANGELOG.md` under today's date, and a new `## Annual invoice PDF` section in `HANDOVER.md` saying the PR is up and what to verify after merge.
5. The next day a different session, from a cloud agent, is asked to "check what is in flight for billing". It reads the handover table, sees the invoice PR, checks GitHub, finds it merged, removes the PR line, sets issue 04 to done, deletes the handover section, and adds the changelog line. Nothing about the fix was lost, and nobody had to re-diagnose it.

The whole record of that bug is three files that each say one thing: the issue file (what and why), the changelog line (that it happened), and, while it was in flight, the handover section (what to do next).

## Two hubs, not one

Scout-specific work and cross-cutting pipeline work started in one hub. It split when the second area grew its own backlog and its own set of people. The rule that made the split cheap: cross-cutting items already numbered in the first hub stay there and are cited by hub and number from the second ("scouts-work issue 27"), never renumbered. Each hub's body names the other under Companions and says which work goes where.

## What broke before these rules existed

Every rule in the template is a fix for something that happened.

- **The changelog became the record.** With "one terse line each" as the only rule, the changelog reached 66 KB in eight days: 75 entries at a median of 760 characters, because writing detail into the file you already have open is easier than opening the issue file. The fix is a stated window in the file header, trimming as part of every append, and the rule that a second sentence belongs in the owning issue.
- **The handover was one file that each session overwrote.** That worked with one session at a time. With several workstreams in flight, the second session appended instead of overwriting and the file turned into a second changelog. The fix is one section per workstream plus the table at the top, and deleting a section when its work lands.
- **Durable facts lived in the handover.** Tidy-ups deleted them, because nothing owned them. The fix is `environment-notes.md`, which is never clobbered, and the "where does this fact go" table in the body.
- **PR numbers without titles.** A list of bare numbers is unreadable to anyone but the session that wrote it. Every reference now carries the title.
- **The body grew.** Each new convention got a paragraph until the body needed scrolling. The fix is the explicit "don't grow it" line and the habit of adding a file plus a pointer instead.
- **Full-body rewrites drop content.** Ask for a one-line change, get back a rewritten body with a section quietly missing. The fix is the smallest-edit-primitive rule: find/replace edits, chained on `base_version`.

## Adapting it

- **Slower workstream:** bind `window_days` to 30 or more. The window is a cap on size, not a rhythm.
- **One person, one session at a time:** the sectioned handover still works; you will just have one section.
- **A team:** set owners on the skill so questions route to someone, and put the hub name in your project's agent instructions so every session knows to load it.
- **Debugging-heavy areas:** add an `investigations/` folder with one dated file per notable debug session, and fold the reusable lessons back into `environment-notes.md`. The investigation is the record; the notes are the memory.
- **Heavy queries or scripts:** put them in `recipes/` as real files, formatted for people, and reference them from the issue that uses them. Never inline them into prose.

## Invoking it

In Claude Code, PostHog engineers reach the store through a small bridge skill that turns `/phs <name>` into a `skill-get` call and follows the body as instructions, pulling bundled files on demand with `skill-file-get`. Any agent with the PostHog MCP can do the same with the `skill-*` tools, and `skill-store-install-command` prints the command that installs the store into other agent harnesses. Scheduled agents load the hub the same way, which is how a report written overnight can cite the issue number a person opened that afternoon.