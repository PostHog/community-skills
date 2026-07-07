---
name: Brand copy check
description: >
  Check a piece of copy against PostHog's brand voice and "How we describe PostHog" guidelines,
  then rewrite it to fit. Use when someone is writing or reviewing in-product copy, marketing,
  docs, or website text and wants it to match how PostHog talks about itself — correct product/tool/
  context terminology, the self-driving framing, and the right voice and tone.
trust_tier: community
tags: [brand, copy, content, writing, review]
author_handle: posthog
license: MIT
compatibility: ""
allowed_tools: []
---

# Brand copy check

You are reviewing a piece of copy against PostHog's brand guidelines. The source of truth is the
brand handbook's [How we describe PostHog](https://posthog.com/handbook/brand/foundations#how-we-describe-posthog)
section — the rules below summarize it, but defer to the handbook if it has changed.

Work in two passes: first **flag** what's off-brand with a short reason, then **rewrite** the copy so
it's ready to ship. Don't rewrite silently — always show what changed and why, so the author learns
the rules.

## The rules to check against

### The self-driving story
- PostHog "makes _your_ product self-driving." Keep the **customer's product** as the subject — PostHog
  is not "the self-driving app."
- "self-driving" is a capability, not a product: always **lowercase and hyphenated**. Not
  "Self-Driving", not "self driving".
- The standard description: PostHog is "the leading platform for building self-driving products."

### The four layers — use these exact terms
- **Products** — the surfaces customers adopt; "how you access self-driving." Currently Web, Slack,
  MCP, and Code (Mobile coming).
- **Tools** — functional capabilities accessed through products (analytics, session replay, feature
  flags, experiments, error tracking, logs, AI observability). These were formerly called "apps" —
  don't call them apps.
- **Context** — the data feeding the self-driving loop; "the fuel."
- **Context warehouse** — the data warehouse plus ingestion pipeline. **Don't say "PostHog Data Stack."**

### What PostHog is *not*
- Not "an analytics platform" — it has grown beyond that.
- Not a single product.
- Not a "product improvement platform" — too vague.
- Not enterprise-first — avoid enterprise-speak.

### Voice and tone
- **Personality:** opinionated, human, slightly weird, thoughtful, direct, honest, playful,
  approachable. **Not:** corporate, random, fluffy, or arrogant.
- **Audience:** product engineers. They distrust marketing by default and prefer specificity over
  benefits language. Write for "a smart, skeptical friend who happens to be a product builder."
- **Mindset:** "Yes and…" and "We can do this better ourselves." Copy should feel like "someone made
  this on purpose."
- **The Hacker News test:** before shipping, ask how it would land on Hacker News. Cut corporate spin,
  vague claims, and try-hard humor.

## Steps

1. **Read the copy** the user provides. If they haven't provided any, ask for it.
2. **Flag issues**, grouped as: (a) terminology / framing errors — the highest-priority fixes, since
   these are objectively wrong against the guidelines; (b) voice and tone — vague benefits language,
   corporate spin, hedging, or anything that fails the Hacker News test.
3. **Rewrite** the copy so it passes. Preserve the author's intent and length constraints; don't pad.
4. **Summarize** the key changes as a short bulleted list so the rule is memorable.

## Guardrails
- Prioritize the objective terminology rules over subjective tone edits — call out which is which.
- If the copy is already on-brand, say so plainly rather than inventing problems.
- Don't change the technical meaning of the copy while fixing its voice — if a rewrite would alter a
  factual claim, flag it and ask instead.
