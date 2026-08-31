# Issues: {{ project }}

Status-at-a-glance index. One file per issue, `issues/NN-short-slug.md`, next free NN. Add a line here on every change and keep statuses honest. Always show the title next to the number when you reference an issue: `issue 07 (digest email sends twice)`, never `issue 07` alone. Bare identifiers are opaque to everyone but the session that wrote them.

| # | Issue | Status |
|---|---|---|
| | | |

Statuses: open / in-progress / pr-open (#N) / blocked / done. Keep done rows briefly, then prune with a `CHANGELOG.md` line.

## Issue file template

```markdown
# NN: <title>

- **Status:** open
- **Opened:** YYYY-MM-DD
- **Surface:** <where it bites: which part of the system, UI, pipeline, docs>

## What

One paragraph. What is wrong or what needs doing, in terms a person with no context can follow.

## Evidence

Numbers, links, queries, the reproduction. Enough that the next session does not redo the diagnosis.

## Next

The concrete next action, and who or what it waits on.
```