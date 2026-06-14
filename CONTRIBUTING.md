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

## Safety

Skills are agent instructions. PRs are reviewed for prompt-injection and data-exfiltration patterns.
Do not include instructions that try to get an agent to leak credentials, call destructive tools
without confirmation, or bypass a user's intent. See [.github/workflows/validate.yml](.github/workflows/validate.yml)
for the automated checks.

## Review

A maintainer (see [CODEOWNERS](.github/CODEOWNERS)) reviews every PR. Once merged, CI regenerates
`registry.json` and PostHog picks up the change on its next sync.
