---
name: Brand copy check
description: >
  Check user-facing copy in a PR, diff, file, or pasted text against PostHog's brand and language
  guidelines, then produce an advisory report with suggested rewrites. Use when a PR touches
  marketing copy or in-product onboarding copy and you want to keep wording consistent with the
  handbook — especially the self-driving positioning and the products/tools/Context Warehouse
  terminology. Advisory only; never a merge blocker.
trust_tier: community
tags: [brand, copy, content, marketing, docs]
license: MIT
---

# Brand copy check

Review copy against PostHog's brand and language guidelines and report what's off, with a suggested rewrite for each finding. This exists so marketing pages and in-product onboarding copy say the same thing without a human hand-reviewing every PR.

**This is advisory.** Flag and suggest — never rewrite in place, never block a merge. The author decides what to apply.

`$ARGUMENTS` can be a PR URL/number, one or more changed file paths, a raw diff, or pasted copy. Check **user-facing copy only** — headings, body text, UI strings, button labels, onboarding steps, error messages. Ignore code identifiers, variable names, and file paths even when they contain flagged words (e.g. an `app/` directory is fine; "download our app" is not).

## Step 1 – Gather the copy

- **PR:** `gh pr diff <number-or-url>` (or read the changed files), then isolate added/changed prose and strings.
- **Files:** Read them and pull the user-facing text.
- **Diff / pasted text:** use it directly.

Keep a note of where each snippet came from so the report can point back to it.

## Step 2 – Load guidelines (hybrid)

Prefer the live handbook. Try to WebFetch these pages; if a page is reachable, its wording wins over the embedded snapshot below (the handbook is the source of truth and changes over time):

- <https://posthog.com/handbook/brand/foundations> — the four layers, what PostHog is/isn't
- <https://posthog.com/handbook/brand/tone> — voice, weasel words, do/don't examples
- <https://posthog.com/handbook/content/posthog-style-guide> — writing mechanics
- <https://posthog.com/handbook/content/brand-message> — top-level messaging
- <https://posthog.com/handbook/marketing/positioning> — word usage
- <https://posthog.com/handbook/wizard-and-docs/docs-style-guide> — docs mechanics

If the pages can't be fetched (e.g. running inside the monorepo with no network), fall back to the embedded snapshot in Step 3. Note in the report which source was used.

## Step 3 – Run the checks

Check three groups. The embedded snapshot is the minimum bar; prefer live handbook wording when you have it.

### A. Terminology & naming (highest priority — this is the pivot)

- **Products** (canonical, per `brand/foundations`): **Web, Slack, MCP, Code** (Mobile coming). **PostHog AI** and **PostHog Inbox** live *inside* Web — they are not standalone products. "PostHog" on its own means the platform. Don't call a product a "tool."
- **Tools** = the functional capabilities: product analytics, session replay, feature flags, experiments, error tracking, surveys, web analytics, the CDP, and so on. These are **Tools, not products** (this reverses the old naming). Flag anything calling a tool a "product" (e.g. "our session replay product").
- **Context** = the data itself: events, recordings, errors, logs.
- **Context Warehouse** = the data warehouse plus the ingestion pipeline. The CDP, Connectors, and the Data Warehouse are tools *within* it. **Never** "PostHog Data Stack."
- **Avoid the word "app"** for now (both "the app" for PostHog and "download our app"). Suggest "PostHog," the specific product, or "tool" instead.
- **"self-driving"** — always lowercase and hyphenated. It's a capability, not a product or tool. Keep the *customer's* product as the subject: "make your product self-driving," not "PostHog is self-driving software."
- **Capitalize** PostHog product and tool names as proper nouns (Session Replay, Feature Flags); lowercase generic industry terms ("companies that offer product analytics").
- If copy conflicts with the canonical product/tool/layer list above (for example, treating Inbox, PostHog AI, or the Context Warehouse as a standalone "product"), flag it and note the handbook is the source of truth — the canonical list may differ from older internal briefs.

### B. Tone & voice (`brand/tone`)

- Target voice: write like you're explaining something to a smart friend — clear, specific, direct, honest, opinionated, playful. Not corporate, fluffy, weaselly, or try-hard funny.
- **Hacker News test:** would a skeptical developer roast this for corporate spin, vague claims, or forced humor? If yes, flag it.
- Cut weasel/hedge words and suggest a concrete replacement: `leverage`→use, `utilize`→use, `streamline`→speed up/simplify, `robust`→describe it, `seamless`→say why it's easy, `best-in-class`/`holistic`/`synergy`→drop or describe, "empowers teams to"/"enables you to unlock"→say what they can now do.
- Prefer specificity over benefit-speak: "It does X" beats "It empowers you to unlock X."

### C. Mechanics

- **enable** (provide the means), not **allow** (permit).
- **Active voice**, not passive.
- No trivializing words: `simply`, `just`, `easily`, `obviously`, `of course`, `clearly`.
- **Present tense**; use **contractions**.
- **Sentence case** for headings and titles (proper nouns excepted).
- **Oxford comma**, always.
- **En dash with spaces** ` – ` for asides — not an em dash `—` or a hyphen `-`.
- **Straight quotes** `'` `"`, not curly.
- **American English** (color, analyze, behavior).
- Spell out numbers zero to nine; numerals for 10+, percentages, and technical values.

### D. Docs-only extras (apply when the copy is documentation)

- Address the reader directly ("you"), or use the imperative for steps.
- Define jargon on first use; link to the relevant doc.
- Precise verbs (call the API, query data) over vague ones (use, work with).
- Inclusive language: allowlist/denylist, primary/secondary, validation (not sanity check).
- Bold for UI elements and callout labels, not for general emphasis.
- Definition lists use a dash, not a colon: `**Product analytics** - Track behavior`.

## Step 4 – Report

Output this format. Order findings by severity. For each, quote the exact offending text, name the rule, link the handbook page, and give a rewrite.

```markdown
# Brand copy check: {PR / file / snippet}
Source of rules: {live handbook | embedded snapshot}

## :red_circle: Terminology & positioning
**"{exact quote}"** — {what's wrong, e.g. "session replay is a Tool, not a product"}
Rule: {handbook link} · Suggested: "{rewrite}"

## :large_yellow_circle: Tone & voice
**"{exact quote}"** — {e.g. "weasel word 'leverage'"}
Rule: {handbook link} · Suggested: "{rewrite}"

## :large_blue_circle: Mechanics
**"{exact quote}"** — {e.g. "'simply' trivializes the step"}
Rule: {handbook link} · Suggested: "{rewrite}"

## Summary
{N} findings ({x} terminology, {y} tone, {z} mechanics). {One-line read on whether it's broadly on-brand.}

_Advisory only — not a merge blocker. Apply what makes sense._
```

If nothing's off, say so plainly and note the copy reads on-brand — don't invent findings to look thorough.

## Notes

- **Terminology beats mechanics.** A misused "product/tool/app" during the self-driving pivot matters more than a stray em dash. Lead with those.
- **Don't over-flag.** One instance of a pattern, noted once, is enough — don't list every hyphen.
- **Stay in your lane:** this checks language, not facts, layout, or code. Don't comment on whether a claim is true, only on how it's worded.
