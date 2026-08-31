---
name: Project Template
description: 'A starter kit for running one area of ongoing work as a living skill
  that agents and people share across sessions: a numbered issues/ backlog with an
  index, ideas/, open-prs.md, a sectioned HANDOVER.md each session overwrites, environment-notes.md
  for durable gotchas, field-feedback.md, roadmap.md, and a rolling-window CHANGELOG.md.
  It is the layout PostHog uses internally for its own scouts and self-driving backlogs,
  with a walkthrough of how those hubs are worked. Install it once per workstream
  (bind the project name and the changelog window), then use the installed skill to
  log an issue or idea, record or clear a PR, resume work in a fresh session, or triage
  the backlog. Trigger on ''log an issue for <project>'', ''what is the state of <project>'',
  ''resume <project> work'', ''track this for <project>'', ''end of session handover''.'
trust_tier: community
tags:
- project-tracking
- skills-pilled
author_handle: andrewm4894
license: MIT
compatibility: Runs over the PostHog MCP skill-* tools. Any agent that can read and
  update PostHog skills can use it.
allowed_tools:
- skill-get
- skill-list
- skill-file-get
- skill-update
- skill-file-create
- skill-file-delete
- skill-file-rename
metadata:
  variables:
  - name: project
    prompt: 'Short name of the area this hub tracks, used in headings (for example:
      scouts, billing, onboarding)'
    required: true
  - name: window_days
    prompt: How many days of changelog entries to keep before trimming
    required: false
    default: '14'
---

# {{ project }} work

The single hub for **ongoing {{ project }} work**: issues, ideas, open PRs, and session-to-session state, shared by every agent session and person that touches it. It is a memory surface, not a runbook: this skill records what is happening and what comes next; the work itself happens in your repo, your tools, and your data.

This body is a thin index. Don't grow it: new detail goes in a bundled file, and the body only gains a pointer.

**First time here?** Read `SETUP.md` and work through it. Delete it when done.

## When resuming a session

1. Read `HANDOVER.md`: scan the **Active workstreams** table, then read only the section(s) your task touches.
2. Read `issues/README.md` for the backlog at a glance.
3. Pull `ideas/README.md`, `open-prs.md`, or `roadmap.md` only if the task touches them, and `environment-notes.md` before you run or query anything.

## Logging work (the core job)

- **Issue** (bug, task, anything actionable) → new `issues/NN-short-slug.md` (next free NN) plus a line in `issues/README.md`.
- **Idea** (feature, improvement, someday/maybe) → new `ideas/NN-short-slug.md` plus a line in `ideas/README.md`. Promote to an issue when picked up.
- **Field signal** (what a user or customer actually said) → a dated block in `field-feedback.md`, newest first. Link the source; keep only the bullets that would change what you build.
- **PR** → `open-prs.md` while open (title and number, never a bare number); remove on merge with a `CHANGELOG.md` line.
- **Any meaningful change** → one line in `CHANGELOG.md` under today's date. It is a rolling {{ window_days }}-day window: trim entries older than that as you append. If a line wants a second sentence, that sentence belongs in the owning issue, idea, or notes file.
- **End of session** → overwrite **your own section** of `HANDOVER.md`. One `## ` section per active workstream; never touch another session's section; delete yours when the work lands.

## Where does this fact go?

| Still true in 30 days? | Has an owner who refreshes it? | Goes in |
|---|---|---|
| Yes | Yes, a tracked work item | `issues/NN` or `ideas/NN` |
| Yes | No, durable reference | `environment-notes.md` or a `references/` file |
| No, but in flight right now | You, this session | your `HANDOVER.md` section |
| No, it just happened | Nobody | `CHANGELOG.md`, one line |

Ask in that order. The commonest failure is durable detail written into the changelog because the changelog is the file you were already editing.

## Files

| File | Read or update when |
|---|---|
| `SETUP.md` | First session only. Delete it once the checklist is done. |
| `HANDOVER.md` | First on resume. Overwrite your workstream's section at end of session, never another's. |
| `issues/README.md` | Backlog index and issue file template. Update on every issue change. |
| `issues/NN-*.md` | One file per issue. |
| `ideas/README.md` | Ideas index and template. One file per idea, `ideas/NN-*.md`. |
| `open-prs.md` | A PR opens or merges. Re-audit against GitHub whenever a session touches PRs. |
| `environment-notes.md` | Durable gotchas: code paths, dashboards, query pitfalls, tool quirks. Never clobbered. |
| `field-feedback.md` | What users and customers say. Dated blocks, newest first. |
| `roadmap.md` | Themes, ordering, open decisions. Rationale only: status stays in `issues/README.md`. |
| `CHANGELOG.md` | One line per meaningful change; rolling {{ window_days }}-day window. |
| `references/how-posthog-uses-this.md` | You want to see the pattern in use: the two internal hubs it was lifted from, a session walkthrough, and what broke before these rules existed. |

Pull a file with `call skill-file-get {"skill_name": "<this skill's name>", "file_path": "<file>"}` over the PostHog MCP.

## Companions (link, don't duplicate)

- `skills-best-practices` (community skills store): the house patterns this layout follows, the Agent Skills spec checklist, and the write mechanics for editing store skills without losing content. Read it before restructuring this skill.
- `working-with-skills` and `skills-store` (ship with the PostHog MCP): the raw `skill-*` tool surface.
- Sibling hubs: when a second area of work needs its own hub, install `project-template` again under another name and cross-link the two here. One hub per area beats one hub that covers everything.

## Posture

Tracking and memory surface only. Change code in the repo, run queries with the query tools, change configuration where it lives. This skill records the outcome and the next step.

## Maintaining this skill

- Keep this body thin. New conventions or reference detail go in a bundled file.
- Use the smallest edit primitive (`edits` or `file_edits` on `skill-update`), chaining `base_version` between writes. A full-body rewrite for a one-line change silently drops content.
- Every meaningful edit gets a one-line `CHANGELOG.md` entry, and every changelog write also trims the window.
- Every session ends with your own `HANDOVER.md` section refreshed, or deleted if the work landed.
- Durable reference never goes in `HANDOVER.md`: nobody owns it there, so nobody prunes it. Put it in `environment-notes.md` or a new bundled file.
