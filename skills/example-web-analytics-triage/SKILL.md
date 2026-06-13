---
name: Web analytics triage
description: >
  Investigate a sudden change in web traffic. Use when a user reports a spike or drop in
  pageviews, sessions, or conversion and wants to find the likely cause (channel, device,
  referrer, or release) before escalating.
trust_tier: official
tags: [web-analytics, triage, debugging]
author_handle: posthog
license: MIT
allowed_tools:
  - query
  - docs-search
---

# Web analytics triage

You are helping triage an unexpected change in web traffic. Work top-down: confirm the change is
real, then narrow to the dimension that explains most of it, then propose the likely cause.

## Steps

1. **Confirm the signal.** Query the relevant web metric (pageviews / sessions / conversion) over a
   window wide enough to show the baseline and the anomaly. State the magnitude and timing of the
   change in plain numbers before going further.
2. **Rule out instrumentation.** Check whether the change coincides with a deploy or an SDK/version
   change. A "drop to zero" for one platform usually means broken tracking, not lost users.
3. **Break down by dimension, biggest first.** Compare the anomalous window to baseline across:
   channel/referrer, device type, geography, and top paths. Find the dimension whose shift accounts
   for most of the delta — don't enumerate every breakdown.
4. **Form a hypothesis.** Tie the dominant dimension to a likely cause (e.g. "referral traffic from
   X dropped after their link changed", "mobile Safari pageviews fell after the 1.2.0 release").
5. **Report.** Give the user: the confirmed magnitude, the dominant dimension, the single most
   likely cause, and one concrete next check to confirm it.

See [references/playbook.md](references/playbook.md) for dimension-by-dimension query hints.

## Guardrails

- Prefer one well-scoped query per step over many speculative ones.
- If the data contradicts the user's framing (e.g. they say "drop" but it's flat), say so plainly.
- Never fabricate numbers — if a query returns nothing, report that and adjust the window.
