# PostHog community skills

A community marketplace of **agent skills** for PostHog — reusable instruction packs that any
MCP-connected agent (Max, Claude, etc.) can discover, install, and use against your PostHog data.

This repository is the **source of truth** for community skill content. PostHog syncs it into an
in-app marketplace (under **Skills → Community**) where you can browse, search, vote, and install
skills into your project with one click. An installed skill becomes a regular project skill you can
edit and version like any other.

> Think Grafana community plugins, but for PostHog agent skills.

## What is a skill?

A skill is a directory containing a `SKILL.md` file — markdown instructions with YAML frontmatter
following the [Agent Skills spec](https://agentskills.io/specification) — plus optional bundled
reference files. See [`skills/example-web-analytics-triage/`](skills/example-web-analytics-triage)
for a complete example.

## Contributing a skill

1. Read [CONTRIBUTING.md](CONTRIBUTING.md).
2. Add a directory under `skills/<your-skill-slug>/` with a `SKILL.md`.
3. Open a PR. CI validates frontmatter, size, and runs safety checks; a maintainer reviews it.
4. Once merged, the skill appears in every PostHog project's community marketplace within the hour.

## Trust tiers

Skills carry a trust tier, shown as a badge in the marketplace:

| Tier        | Meaning                                                   |
| ----------- | -------------------------------------------------------- |
| `official`  | Authored and maintained by the PostHog team.            |
| `verified`  | Community-authored, reviewed in depth by a maintainer.  |
| `community` | Community-authored, passed automated checks + PR review. |

> ⚠️ **Skills are agent instructions.** Installing a skill lets it steer an agent that has access to
> your PostHog data. Review a skill's instructions and its declared `allowed_tools` before installing,
> the same way you'd review a browser extension's permissions.

## How the catalog is built

`registry.json` is generated in CI from the `skills/` directory (see
[`scripts/build_registry.py`](scripts/build_registry.py)) and embeds each skill's content. PostHog
fetches this single file to reconcile its local read-model. Do not edit `registry.json` by hand.
