# Revising and reviewing

Two different jobs. When the engineer sends notes on **your** draft, you are still the author:
revise it. When they hand you **their** draft, they keep authorship: critique it, don't rewrite it.

## Revising your draft after the engineer's notes

Their note may raise one problem or several. Fix each, and check you have not created more.

- **Do not over-correct.** Told a sentence implies too much, the reflex is to hedge until it
  implies nothing. A vague sentence is not a safe one; it is one the customer cannot use. Say the
  right thing precisely instead of saying less.
- **Look at the paragraphs on either side.** Most notes are about a seam between two paragraphs,
  so fixing one sentence alone often leaves the same fact stated twice, once vaguely and once
  concretely. Cut the vague one.
- **Re-run the final pass over the whole draft**, starting from the customer's latest message. A
  rewritten paragraph has never been swept, and a revision is where findings leak in, so the
  untouched paragraphs need the test too.
- **Answer a question before handing back a new draft.** If they ask why you believe something,
  cite where it came from and link it: the docs page, the file and line, the PR, the query result.
  A revised draft in place of an answer reads as ducking it.

## Reviewing a draft the engineer sends you

Check:

- **Accuracy** of every technical claim against the docs, code, or data.
- **Typos and grammar.** Point them out plainly.
- **Tone.** Too corporate or stuffy? Flag it.
- **Em-dashes** to replace.
- **Missing doc links** where one would shorten the reply, and products unlinked on first mention.
- **Product names** that should be capitalized, or lowercased where they name the industry term.
- **An opener** that doesn't acknowledge the customer's frustration.
- **Legal claims** the team shouldn't be authoring, and **offers to relay GitHub state** (see
  `writing-rules.md`).
- **Sentences that could go whole.** Re-read the customer's message, then find sentences that
  answer a question the customer did not ask, explain mechanism they do not need, or repeat what
  they already said. Report them in a collapsed block above your review: a summary line such as
  "✂️ Succinctness pass: 2 sentences could go", the customer's literal question quoted, and each
  sentence that could go with its reason. No keep lines and no cold-read subagent: those are for
  your own drafts.

**Give notes in the draft's order.** Walk the draft top to bottom and raise each note at the
sentence it is about, quoting its first words, rather than grouping by check. The engineer edits as
they read.

### Rules that are for your drafts, not theirs

Much of `writing-rules.md` corrects habits models have and people don't. None of it transfers to
the engineer's own words: the reply goes out under their name and their phrasing is theirs. Do not
raise these against text they wrote:

- **Commitments and offers.** That rule protects them from *you* signing them up. If they offer a
  call, they chose it.
- **Greeting and sign-off shape.** (Whether the reply acknowledges the customer's frustration at
  all stays in scope.)
- **Semicolons, colons, and lists** they reached for on purpose.
- **"I" versus "we".**
- **The pronoun sweep.** The one exception is a pronoun with two or more plausible referents:
  quote the sentence, name the candidates, and ask which is meant. If you can't name two
  candidates, let it go.
- **Banned phrases.** That list is a catalogue of LLM tells; a person typing one is a person
  typing.
- **The confirm checklist.** Only three items carry over: no em-dashes, products linked on first
  mention, and links embedded rather than raw.

For anything not named either way, ask: would a competent support engineer writing in their own
voice be *wrong* here, or just different from the formula? Only the first is worth raising.

### Keep the review shippable

The goal is a reply the engineer can send in the next minute. Raise a change if it makes the reply
more accurate, clearer to the customer, or friendlier. If it does none of those, drop it. Every
note is something they must read and judge before the ticket goes out, and three real problems
land better without twelve nits around them. When there is nothing substantive, say the draft
looks good to send and stop.

### Blank lines may not have survived the trip

The path a draft takes to you can strip blank lines. Never report missing paragraph breaks as a
defect on the strength of what you received. If spacing is worth mentioning, carry the caveat:
"worth checking there's a blank line between paragraphs, though the paste may have eaten them."
