# Official spec checklist

The statically-verifiable rules from the official Agent Skills spec and published authoring best practices. This is the **compliance floor** — check these before the house patterns in `patterns.md`. Every rule here can be anchored to an exact line or field; if a check needs a judgment call, it belongs in the house patterns, not here.

## Canonical sources (re-fetch when refreshing this file)

- <https://agentskills.io/specification> — the official Agent Skills spec.
- <https://agentskills.io/skill-creation/best-practices> — agentskills.io best practices.
- <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> — Anthropic's authoring best practices.
- <https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md> — the reference skill-creator skill (raw, most machine-readable — anchor on this one).

Note: the agentskills.io pages may render as a JS shell over `curl`; fall back to the raw skill-creator SKILL.md and the platform.claude.com docs (both static). Record the refresh date at the bottom of this file when you update it.

## The checklist

| Rule | What to check (statically) |
| ---- | -------------------------- |
| Required frontmatter | `name` and `description` present and non-empty; valid YAML. (Store skills: the `name`/`description` fields on the skill record.) |
| `name` format | lowercase letters / numbers / hyphens only, ≤ 64 chars; for in-repo skills, matches the skill's directory name. |
| `description` quality | third person; states both **what it does** and **when to use it** (trigger conditions); not a bare title; 1024 chars or fewer (the store accepts more, but community publishing and the spec do not). |
| Body size / progressive disclosure | body is lean (hard budget ~500 lines; aim far under); heavy depth pushed into bundled/reference files read on demand, not inlined. |
| Single responsibility | one coherent capability, not a kitchen-sink of unrelated jobs. If the description needs "and also…", consider splitting. |
| Reference hygiene | every bundled-file / relative link the body points at **exists**; no dead links. For store skills: every file named in the body appears in the `files` manifest, and vice versa (no orphan files the body never mentions). |
| Instruction style | imperative / second-person steps; no time-sensitive or soon-stale content baked in ("as of last week…", hardcoded dates that will rot). |
| No secrets | no API keys, tokens, or credentials in the body or any bundled file. |

## Severity guide

- **Fails to load / parse** (missing required fields, malformed YAML, unresolvable name) — fix before anything else.
- **Everything else** — batch into the refactor; one pass per skill, not one nit at a time.

---

Ruleset seeded 2026-07-01 from the sources above. Re-fetch the sources above when auditing if this is more than a few weeks old.