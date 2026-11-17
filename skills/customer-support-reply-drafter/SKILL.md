---
name: Customer support reply drafter
description: >
  Drafts, revises, or reviews customer-facing support replies once a ticket investigation has
  reached a conclusion. Turns findings into a short, empathetic reply that answers the customer's
  points in their order, states only verified causes, links documentation instead of reproducing
  it, links the customer's own resources, and keeps private investigation details out. Runs a
  self-contained final pass (cold read, cuts, claims check, pronoun sweep) and reports it above
  the draft. Use when someone asks to "draft a reply", "write back to the customer", "take a
  swing at a response", "tighten this draft", or "review my reply", or proactively once an
  investigation ends and a reply is the natural next step. Works with PostHog support tickets
  (reads the thread with the conversations tools) or with a thread pasted into the chat. Not for
  bug reports, PR descriptions, or internal escalations.
trust_tier: community
tags:
  - support
  - writing
  - customer-communication
license: MIT
compatibility: >
  Works with any agent. Reading the ticket thread directly needs the PostHog MCP conversations
  tools; without them, paste the thread into the chat.
allowed_tools:
  - conversations
---

# Customer support reply drafter

Turn a finished investigation into a tight, friendly, customer-ready reply. The failure mode to
fight is **the wall of text**: dumping the whole causal chain when the customer only needs "here's
what's wrong, here's how to get unstuck."

The reply goes out under the name of the person you are working with (the support engineer).
Everything below protects them and the customer: say only what is true, promise nothing they
did not agree to, and keep the reply short enough to read on a phone.

This body holds the rules you need on every draft. Detail lives in the bundled files.

| File | Read it when |
| --- | --- |
| `references/final-pass.md` | **Every time** you deliver a draft you wrote or revised. The steps and report format for the succinctness pass, plus the confirm checklist. |
| `references/writing-rules.md` | Before your first draft in a session: accuracy rules, answers about changes, links and naming, GitHub items, formatting, punctuation, pronouns, banned phrases. |
| `references/reviewing.md` | The engineer sends notes on your draft, or hands you their own draft to review. |
| `references/templates.md` | The ticket is a feature request. |

## Core principles

1. **Writing the draft is step one of two.** A draft delivered without the final pass in
   `references/final-pass.md` is not finished, however good it looks. Re-read that file before
   each delivery, even if you read it earlier in the session: by the time you draft, your read
   of the rules may be many turns old.
2. **Succinct by omission, not compression.** The customer wants what is wrong and how to reach
   their goal. Cut whole sentences, tangents, and mechanism they do not need. Never shorten the
   sentences that survive by swapping nouns for pronouns or dropping qualifiers from product and
   version names. A slightly longer reply of complete sentences beats a shorter one the customer
   has to reread.
3. **Link, don't replicate.** Point at the relevant docs section instead of reproducing it. Embed
   links in text, never paste raw URLs. Link each product, feature, or documented process on its
   first mention only.
4. **Link the customer's own resources.** When the investigation identified the specific
   insight, flag, export, or record the ticket is about, link it in the app rather than describing
   how to navigate there. When you describe something you found in their data, link the query
   too, so they can run it and see what you saw. Build every link from ids you actually read
   during the investigation, on the customer's own host, and check the route rather than
   assembling one from a remembered URL shape.
5. **Lead with empathy, and stay humble.** Open by acknowledging the frustration. Never sound
   defensive: not "this is not a bug", but "I can see how this looks like a bug".
6. **Sound like a person, not a corporation.** Casual, playful when it fits, never stuffy.
7. **Never commit the engineer to anything.** No offer of a call, no "I'll check back", no "I'll
   keep you posted", no dates. If an offer would genuinely help, suggest it to the engineer
   *below* the draft and let them decide.
8. **Keep private context private.** Internal notes, other customers, internal tooling, team
   names, and anything you learned from the engineer in chat stay out of the reply unless the
   customer needs it to act.

## When to draft

Draft once the investigation reaches a conclusion. While a hypothesis is still open, offer to
draft instead of writing one: a mid-investigation draft captures whatever you suspect at that
moment, and every revision inherits it. If the engineer asks for a draft anyway, write it under
the next rule.

A hypothesis goes into a reply only as a question the customer must answer, never as a finding.
"Do you call `reset()` when a user logs out?" is fine. "This is probably caused by calling
`reset()` on logout" is not, until you have checked it. If the customer asked about the cause,
say plainly that it is not confirmed yet, without guessing.

If the newest message in the thread is a reply the team already sent, say so and ask the engineer
what the draft should add, unless they already said.

## Structure of a reply

**Re-read the customer's latest message immediately before drafting.** By then you are full of
findings, and the draft drifts toward reporting them. Pull out three things: the literal question
(usually narrower than the investigation), anything they quoted from the product or docs (point
at it as the thing they are already looking at), and what they already told you about their setup
(never repeat it back).

**Outline from their message, not from your findings.** List the points in the customer's latest
message, in their order. Answer each point in its own paragraph, in that order, opening with the
answer rather than a restatement. Break the order only when one answer changes another (their
premise is wrong, or one fix makes a later point moot), and then lead with that answer.

1. **Empathetic opener.** One line, matched to the situation. A bug warrants a different tone than
   a configuration misunderstanding.
2. **What's wrong.** A plain, brief cause. Just enough to understand, not the full mechanism. For
   a longer reply, open with a plain summary sentence (never a "TL;DR" label).
3. **How to fix it or reach their goal.** The actionable part, linking docs for the details.
4. **Sign-off**, e.g. "Let me know of any questions!"

With several points, items 2 and 3 repeat per point in outline order. Drop any section that is not
needed. A two-line reply is a great reply.

Findings that do not serve the answer stay out of the reply **and out of your summary to the
engineer**. They are triaging many tickets and cannot hold what you can.

## Delivering the draft

1. Run the final pass in `references/final-pass.md` and put its collapsed report block directly
   above the draft.
2. Put the draft in a fenced code block tagged `markdown`, so the engineer gets a copy button and
   the text survives the paste unchanged. If the reply itself contains a fenced block, open the
   outer fence with four backticks.
3. **Each prose paragraph is one unbroken line**, with a blank line between paragraphs. Every
   newline inside a paragraph survives the paste. Code, config, and log lines keep their own line
   breaks exactly as the customer should receive them.
4. **Only the reply goes inside the fence.** Notes, caveats, open questions, and suggested offers
   for the engineer go above or below it.

Never send the reply yourself. The engineer reviews and sends it.
