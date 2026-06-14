---
name: Make PR
description: >
  Create a GitHub pull request for the current branch using the gh CLI. Use when a user wants to
  open a PR and have the title, body, template, and assignee handled for them, following the repo's
  conventions and keeping public PRs free of PII.
trust_tier: community
tags: [github, pull-request, workflow]
author_handle: andymaguire
license: MIT
compatibility: Requires git and the GitHub CLI (gh) authenticated to the repo.
---

# Make PR

Create a GitHub pull request for the current branch using the `gh` CLI.

## Steps

1. Check for a PR template at `.github/PULL_REQUEST_TEMPLATE.md` or `.github/pull_request_template.md`. If found, follow its structure.
2. Run `git log` and `git diff` against the base branch to understand all changes.
3. Write a concise PR title (under 70 chars) and body. No emojis. Follow the repo template.
4. Discover the current user with `gh api user --jq '.login'` and assign them as the PR assignee.
5. Create the PR using `gh pr create` with `--assignee`.
6. Return the PR URL.

## Rules

- No filler, no emojis.
- Push the branch first if not pushed: `git push -u origin HEAD`.
- Use a HEREDOC for the PR body.
- No PII or sensitive data — PRs are public.
