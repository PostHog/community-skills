# Open PRs: {{ project }}

Always title and number, never a bare number. A PR line lives here while the PR is open; on merge, remove it and add a `CHANGELOG.md` line.

Re-audit against GitHub whenever a session touches PRs. PRs get opened from several surfaces and this file drifts both ways. Replace `<owner/repo>` and `<search term>` with yours:

```
gh pr list --repo <owner/repo> --search "<search term> in:title" --state open --json number,title,isDraft,url
gh pr view <n> --repo <owner/repo> --json state,title,isDraft,url
```

- (none yet)