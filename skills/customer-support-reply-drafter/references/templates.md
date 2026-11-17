# Reply templates

Starting points for the two feature-request situations that recur most. The drafting rules and the
final pass still apply to a draft built from a template. Both are shaped for chat channels (widget,
Slack, Teams); adjust the greeting for email. Replace `[roadmap URL]` with the team's public
roadmap, or drop that clause if there isn't one.

## Existing feature request found

The investigation turned up an existing GitHub feature request matching what the customer asked
for.

```markdown
Hey [name]. Thanks for the solid suggestion!

The good news is that our engineers are already thinking about this and tracking it [via this feature request]([issue URL]). You can subscribe to that GitHub issue to follow progress, and please feel free to add a comment with any further detail you think is relevant!

We can't promise that we'll build every feature request, as we have a lot on [our roadmap]([roadmap URL]), but we'll certainly give it serious thought! In the meantime I'm going to close this support ticket, since we're tracking the feature request on GitHub.
```

- Adapt the opener to the ask: "solid suggestion" fits a genuinely good idea; don't overpraise a
  routine ask.
- If a workaround exists, add it as a short paragraph before the closing one.
- "The good news is" is allowed here, because it is genuinely good news. It stays banned elsewhere.

## New feature request filed by the team

The team has just opened a new GitHub feature request in response to the customer's suggestion.

```markdown
Hey [name]. Thanks for the solid suggestion!

I have created [this feature request on GitHub]([issue URL]). You can subscribe to it to follow progress, and feel free to add a comment with any further details you think are relevant.

We can't promise that we'll build every feature request (we have a lot on [our roadmap]([roadmap URL])) but we'll certainly give it serious thought!

I'm closing this support ticket now, since we're tracking the request in the GitHub issue at the link above, but you can just reply to re-open this ticket if needed.
```

- If a workaround exists today, add it as a short paragraph before the roadmap one.
- Keep the re-open line: the ticket is being closed proactively, so the customer needs to know a
  reply re-opens it. Drop it if the team's tooling doesn't re-open tickets on reply.
- Only use this template once the issue actually exists. Don't invent an issue URL.
