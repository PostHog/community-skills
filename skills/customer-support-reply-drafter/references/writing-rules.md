# Writing rules

The detailed rules behind every draft. Read once per session before your first draft; the final
pass in `final-pass.md` checks the ones that slip most.

## Accuracy

- **Don't let an assumption ride as a fact.** Check every technical claim against the docs, the
  code, or the customer's data before it goes in.
- **Don't hedge a fact you positively verified.** "As far as I've been able to find" reads as
  uncertainty. If the data shows something affirmatively (a sync disabled with no sync timestamp,
  say), state it flatly. Hedge only what you could not confirm.
- **Check where the customer's content actually lives, not only the containers they named.** The
  customer names a table, a source, or a project; you verify that one; the answer is still wrong
  because their content also lives somewhere you did not check. This is most common with
  warehouse sources and anything imported from another system. Answer about the content, not the
  container.
- **Check the customer can actually reach what you recommend.** Not whether the feature exists,
  but whether *they* can reach it: on their plan, with their permissions, behind any feature flag
  or preview gate, on the screen you are sending them to. Features often reach the creation flow
  before the edit flow. Recommending a path they cannot walk is worse than saying nothing.
- **A gated feature is not always a dead end.** If the product has self-serve previews or betas,
  check whether the feature is on that list and link the setting and its docs, so the customer can
  switch it on without asking.
- **Never author contractual or legal claims.** DPAs, BAAs, subprocessors, retention commitments,
  and data-residency guarantees go in as a link to the team's maintained, authoritative page, not
  as a sentence you wrote. A support-written version goes stale, may name the wrong instrument for
  the customer's jurisdiction, and becomes the company's written position if the ticket escalates.

## When the answer is "this is changing"

Migrations, deprecations, fixes in flight, plan changes: any reply where the answer differs
before and after some event.

- **Anchor every sentence to one side of the change.** Present tense does not carry the boundary:
  "your script keeps working" reads as an open-ended promise next to "this will change". Put the
  timeframe in the sentence ("until that happens", "once we migrate it"), and never let a
  paragraph straddle both sides.
- **Say what stays the same, not only what changes.** A customer told only what is changing
  assumes the change is bigger than it is. One clause fixes it: what they do today that still
  works, and who does the work.
- **Never give a date** for unreleased work ("ships next month", "sometime this quarter") unless
  the team has already made that date public. A date in a support reply is a commitment, and it
  becomes a broken promise with the engineer's name on it.
- **Check who owns a fix before calling it one.** "There's a fix in progress" is fair when someone
  on the team opened the PR, or is actively reviewing an agent-opened one. It is not fair for an
  untouched agent-opened PR or an outside contribution, which nobody has committed to. The same
  test applies to "it's on the roadmap": say it only when the item is on the public roadmap. When
  a claim fails the test, leave it out.

## Naming and linking

- **Name the specific SDK or package, not the repository it ships from.** A monorepo can hold many
  SDKs, so linking the repo name sends a mobile or server customer to the wrong docs. Work out
  which SDKs the customer uses from the package names in the ticket or their project data, and
  link that SDK's own docs page rather than a URL assembled from memory.
- **Product names are proper nouns,** so keep them capitalized as the product's own docs do.
  Lowercase the general industry term when you are not naming the product.
- **Their words, then ours.** Customers name things in their own vocabulary, often from a product
  they used before. Lead with their word, then introduce yours once, linked: "the username and
  password on your export (we call this a connection)", with *connection* linking to its doc and,
  where one exists, to that screen in their project. Keep using their word afterwards.
- **Name the actor and the verb, never a spatial metaphor.** "The credentials go onto the
  connection" describes no action. Someone does something: your automation sends them, you set
  it, we copy it. If you cannot name who acts, you do not understand the answer well enough yet.

## Pointing at a GitHub issue, feature request, or PR

Whenever a reply references a GitHub item, **invite the customer to subscribe to it** so they can
follow progress themselves, e.g. "you can subscribe to [the PR](URL) to follow progress". Do not
offer to notify them when it changes, in any wording ("I'll let you know when the fix is merged",
"I'll keep you posted"). Those promises make support the notification channel for something
GitHub already does better, and commit the sender to open-ended follow-up.

Telling them an item's current state (open, merged, closed) is fine. A bounded commitment the
team controls (replying once the owning team answers, holding a ticket open) is fine too.

## Formatting

- **Channel.** Default to the support widget unless the ticket or the engineer says email or
  another channel. Chat replies (widget, Slack, Teams) should be even shorter than email: the
  customer may be on a phone.
- **Greeting.** Chat: `Hey [name].` (period, not comma), with the first sentence on the same line,
  e.g. "Hey Jane. Thanks for letting us know about that!" Email: `Hey [name],` on its own line,
  then a blank line.
- **Blank line between paragraphs** in every draft.
- **No headers** in the reply body.
- **No em-dashes (—).** A hard rule: em-dashes are a common tell of machine-written text. Use two
  sentences, parentheses, or commas. Never swap an em-dash in for a semicolon or colon either.
- **Embed links in text.** Avoid bare URLs unless the customer needs to see the URL's structure.
  Anchor links (`#section`) are fine. Don't put backticks inside link text; use single quotes if
  the link text needs to read as code.

## Punctuation and word choice

- Oxford comma in every list. Sentence case for titles.
- Prefer two sentences (or a parenthetical) over a semicolon or colon by default. Both are
  correct and sometimes the best fit; this is a default, not a ban.
- Avoid "never" and "always" unless you hold data supporting the absolute.
- Say "I", not "we", for actions taken ("I checked that insight and found..."). "We" stays natural
  when speaking for the company or product ("our docs", "we don't support that today").

### Pronouns: name the noun

A pronoun is not a word-count tool. Repeating a noun is cheap; a reader stopping to work out what
"it" points at is expensive, and in a technical explanation they often cannot recover it. The
riskiest words are `it`, `this`, `that`, `they`, `them`, `these`, `those`, `both`, and `either`,
because they can point at a whole clause. `both` is the worst: it silently asserts which two of
several things you meant.

The test, for each of those words: say out loud the noun it replaces. If that noun is not in the
same sentence or the one before, use the noun. If you cannot state the noun at all, the sentence
is broken. Watch for a referent that was only ever described, never named ("87% of them come
from..." after several sentences about a problem).

Naming the noun also forces you to check the noun is true. Writing "the rejected merges" instead
of "them" can expose that a percentage was measured over something else entirely.

## Banned phrases

- **"The good news is"**: rarely lands with a frustrated customer. (Allowed in the
  existing-feature-request template, where it is genuinely good news.)
- **"Honestly" / "To be honest" / "The honest answer is"**: implies honesty is the exception.
- **"You're absolutely right."**: a well-known LLM tell.
- **"TL;DR"**: reads as condescending. Use a plain, unlabeled summary sentence.
- **"Thanks for flagging this"** and other flag-based openers: unclear for non-native speakers.
- **"Thanks for reaching out"**: canned support-speak. Keep the gratitude, vary the words.
- **"contract" for anything technical**: reserve it for legal agreements. Name the actual thing:
  the response shape, the expected properties, the documented behaviour.
