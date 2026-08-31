# Set up this hub (first session only)

Work through this list, then delete this file with `skill-file-delete` and add a `CHANGELOG.md` line saying the hub is set up. Chain `base_version` between writes.

1. **Name.** If the skill was installed under a name you do not like, rename it now, before anything links to it. A hub is usually named `<area>-work`.
2. **Pull command.** In the body, replace `<this skill's name>` with the installed name, so agents can copy the `skill-file-get` line as it stands.
3. **Description.** The installed description is the generic template one. Rewrite it for retrieval: what {{ project }} covers, what it does not, the surfaces it owns, and five to ten phrases people actually say when they want this skill (`log a {{ project }} issue`, `resume {{ project }}`, `what is in flight for {{ project }}`). Keep it under 1024 characters. A perfect skill with a vague description never gets loaded.
4. **Scope line.** Edit the first paragraph of the body to say what is in scope and, more importantly, what is not. Name the sibling hub or system that owns the rest.
5. **Seed the backlog.** Open an issue file for each thing already in flight and an idea file for each thing you keep meaning to do. Number from 01.
6. **Seed `environment-notes.md`.** Write down the three gotchas a new agent would trip over on day one: where the code is, which dashboard is the source of truth, which query pattern silently lies.
7. **`open-prs.md`.** Put your repo and search term into the `gh` commands at the top of the file.
8. **`roadmap.md`.** Two or three themes and why they are ordered that way. Leave status out.
9. **Metadata and owners.** Set `metadata` (`owner`, `product`, `category: tracking`) and the skill's owners, so questions about it route to a person.
10. **First handover.** Replace the example section in `HANDOVER.md` with a real one for whatever you are about to do next.

Then delete this file. A hub that still has `SETUP.md` a week later was never set up.