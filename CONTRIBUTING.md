# Contributing a skill

Thanks for sharing a skill with the PostHog community!

## Layout

Each skill is a directory under `skills/`:

```text
skills/
  my-skill-slug/
    SKILL.md            # required — frontmatter + instructions
    references/         # optional — bundled files the skill can reference
      playbook.md
```

The directory name is the skill's **slug**: lowercase letters, numbers, and single hyphens
(`^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, max 64 chars). It must be unique across the repo.

## `SKILL.md` frontmatter

```markdown
---
name: My skill                       # required — display name
description: >                       # required — what it does AND when to use it (max 4096 chars)
  One or two sentences. Lead with the job-to-be-done so agents can match it.
trust_tier: community                # set by maintainers on review; default community
tags: [web-analytics, triage]        # optional — used for filtering/discovery
author_handle: your-github-handle    # optional
license: MIT                         # optional
compatibility: ""                    # optional — environment/tool requirements
allowed_tools:                       # optional but encouraged — tools the skill may use
  - query
  - docs-search
---

# My skill

Markdown instructions for the agent go here…
```

### Field rules

- **`name`** and **`description`** are required. Write the description for matching — lead with the
  job, not the mechanism.
- **`allowed_tools`** should list every MCP tool domain the skill expects to call. This is surfaced
  to users at install time as the skill's "permissions". Keep it minimal.
- **`trust_tier`** is authoritative only when set by a maintainer during review. Default to
  `community`.

## Templated skills

A skill becomes a *template* when its frontmatter declares `metadata.variables`. Each variable is a
value the installer is asked for, and every `{{ name }}` placeholder in the body and in bundled
files is replaced with it when the skill is installed. Substitution is plain text replacement, not a
template engine, so there are no loops, conditionals, or expressions.

```markdown
---
name: Repo dashboard
description: >
  What it does and when to use it.
metadata:
  variables:
    - name: repo                     # required — the placeholder name, used as {{ repo }}
      prompt: Repository to watch, as owner/name
      required: true                 # no default, so the installer must supply a value
    - name: default_branch
      prompt: Branch that pull requests merge into
      default: main                  # having a default makes it optional
---

Report the current state of `{{ repo }}`, branch `{{ default_branch }}`.
```

Rules worth knowing:

- A variable with a `default` is optional; one without a default is required, and installing without
  it fails.
- Placeholder names must be identifier-like: letters, digits, and underscores, not starting with a
  digit. `{{ repo-name }}` is rejected rather than silently left in place.
- Every `{{ ... }}` in the body and in bundled files must match a declared variable. An undeclared
  placeholder is treated as a bug in the skill, not as literal text.
- Bind what differs per install, such as a repository or a branch. Do not bind who is running the
  skill: several people share one installed skill, so resolve the current user at run time instead.
- Avoid the GitHub CLI's `--template` flag in a templated skill. It uses Go template syntax with the
  same doubled-brace delimiters, so the two collide. Use `--json` with `--jq`.
- Values are stored in plain text on the installed skill, so never ask for a secret, a token, or a
  password.
- A value substituted into a shell command is not escaped. Substitution is plain text replacement,
  and a branch or path name may legally contain `;`, `$()`, or a backtick, so a careless default
  turns into a command the agent runs. Quote the placeholder, and have the skill check the value
  against the shape it expects before any command that contains it.

## Safety

Skills are agent instructions. PRs are reviewed for prompt-injection and data-exfiltration patterns.
Do not include instructions that try to get an agent to leak credentials, call destructive tools
without confirmation, or bypass a user's intent. See [.github/workflows/validate.yml](.github/workflows/validate.yml)
for the automated checks.

## Review

A maintainer (see [CODEOWNERS](.github/CODEOWNERS)) reviews every PR. Once merged, CI regenerates
`registry.json` and PostHog picks up the change on its next sync.
