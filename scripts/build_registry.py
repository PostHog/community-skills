#!/usr/bin/env python3
"""Generate registry.json from the skills/ directory.

The registry embeds each skill's full content so PostHog can reconcile its catalog with a single
fetch. Run in CI on every push to main; the output is committed/published alongside the repo.

Usage: python scripts/build_registry.py [--check]
  --check  Fail (exit 1) if the committed registry.json is stale, instead of writing it.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = os.environ.get("GITHUB_REPOSITORY", "PostHog/community-skills")
# Branch used to build the canonical github_url. Deliberately NOT derived from GITHUB_REF_NAME:
# on a pull_request event that is the merge ref ("<n>/merge"), which would make the generated
# registry.json differ from the committed one and fail --check. The registry is published from main.
BRANCH = os.environ.get("REGISTRY_BRANCH", "main")
ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REGISTRY_PATH = ROOT / "registry.json"

SLUG_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
VALID_TRUST_TIERS = {"official", "verified", "community"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)

# Size caps. The whole catalog is shipped as a single registry.json that PostHog fetches hourly, so
# keep individual skills small. These are intentionally generous for text instructions.
MAX_FILE_BYTES = 256 * 1024  # 256 KiB per bundled file (incl. SKILL.md)
MAX_SKILL_BYTES = 1024 * 1024  # 1 MiB total embedded content per skill

# What an entry becomes when it is used in PostHog. A `skill` installs as a skill. A `scout` opens the
# scout-create form prefilled, where a person reviews its schedule before it runs.
KIND_SKILL = "skill"
KIND_SCOUT = "scout"
VALID_KINDS = {KIND_SKILL, KIND_SCOUT}

# Local copies of the bounds PostHog applies to a published scout's settings when it syncs this
# registry. An entry that breaks them is dropped at sync, so CI rejects it here, where the author sees
# why. PostHog stays the authority: it checks again at sync and when the create form is submitted.
MIN_RUN_INTERVAL_MINUTES = 30
MAX_RUN_INTERVAL_MINUTES = 43200  # 30 days
MAX_CRON_SCHEDULE_LENGTH = 100
CRON_FIELD_COUNT = 5
MAX_SCOUT_TAGS = 10
MAX_SCOUT_TAG_LENGTH = 50
# `network_access`, `model` and `mcp_gateway_server_ids` are absent on purpose: they give a scout
# reach into a project's data and services, so a shared scout never preselects them.
SHAREABLE_SCOUT_CONFIG_KEYS = {"run_interval_minutes", "run_cron_schedule", "emit", "tags"}

_TAG_SEPARATORS = re.compile(r"[\s_]+")
_TAG_INVALID_CHARS = re.compile(r"[^a-z0-9-]+")
_TAG_HYPHEN_RUNS = re.compile(r"-{2,}")


def _list_of_str(frontmatter: dict[str, Any], slug: str, field: str) -> list[str]:
    """Coerce a frontmatter field to a list of strings, rejecting scalars.

    `yaml.safe_load` turns a bare `field: query` into the string "query"; passing that to `list()`
    would silently explode it into individual characters, so require an explicit YAML sequence.
    """
    value = frontmatter.get(field)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{slug}: '{field}' must be a YAML list of strings")
    return value


def _slugify_tag(raw: str) -> str:
    """Normalize a tag the way PostHog stores it on a scout: a lowercase kebab-case slug."""
    slug = _TAG_SEPARATORS.sub("-", raw.strip().lower())
    slug = _TAG_INVALID_CHARS.sub("", slug)
    return _TAG_HYPHEN_RUNS.sub("-", slug).strip("-")


def _validate_scout_config(raw: Any, slug: str) -> dict[str, Any]:
    """Reject scout settings that PostHog would drop at sync, and return them unchanged otherwise."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"{slug}: 'scout_config' must be a mapping")

    # Reject an unknown key rather than skip it, so an author who set `network_access` learns that it
    # does not travel with the scout.
    unknown = sorted(set(raw) - SHAREABLE_SCOUT_CONFIG_KEYS)
    if unknown:
        raise ValueError(
            f"{slug}: 'scout_config' cannot carry {', '.join(unknown)}; only "
            f"{', '.join(sorted(SHAREABLE_SCOUT_CONFIG_KEYS))} travel with a shared scout"
        )

    if "run_interval_minutes" in raw:
        interval = raw["run_interval_minutes"]
        # bool is an int subclass, and `true` would otherwise pass as a 1-minute cadence.
        if isinstance(interval, bool) or not isinstance(interval, int):
            raise ValueError(f"{slug}: 'scout_config.run_interval_minutes' must be an integer")
        if not MIN_RUN_INTERVAL_MINUTES <= interval <= MAX_RUN_INTERVAL_MINUTES:
            raise ValueError(
                f"{slug}: 'scout_config.run_interval_minutes' must be between "
                f"{MIN_RUN_INTERVAL_MINUTES} and {MAX_RUN_INTERVAL_MINUTES}"
            )

    # Only the shape is checked here. PostHog also checks that the cron matches a real date and runs
    # at most every 30 minutes, which needs a cron parser this script does not depend on.
    cron = raw.get("run_cron_schedule")
    if cron is not None:
        if not isinstance(cron, str):
            raise ValueError(f"{slug}: 'scout_config.run_cron_schedule' must be a string")
        if len(cron.strip()) > MAX_CRON_SCHEDULE_LENGTH:
            raise ValueError(
                f"{slug}: 'scout_config.run_cron_schedule' must be {MAX_CRON_SCHEDULE_LENGTH} characters or fewer"
            )
        if cron.strip() and len(cron.split()) != CRON_FIELD_COUNT:
            raise ValueError(f"{slug}: 'scout_config.run_cron_schedule' must have {CRON_FIELD_COUNT} fields")

    if "emit" in raw and not isinstance(raw["emit"], bool):
        raise ValueError(f"{slug}: 'scout_config.emit' must be true or false")

    if "tags" in raw:
        tags = raw["tags"]
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError(f"{slug}: 'scout_config.tags' must be a YAML list of strings")
        normalized: set[str] = set()
        for tag in tags:
            tag_slug = _slugify_tag(tag)
            if not tag_slug:
                raise ValueError(f"{slug}: scout tag {tag!r} is empty once normalized to a lowercase slug")
            if len(tag_slug) > MAX_SCOUT_TAG_LENGTH:
                raise ValueError(f"{slug}: each scout tag must be {MAX_SCOUT_TAG_LENGTH} characters or fewer")
            normalized.add(tag_slug)
        if len(normalized) > MAX_SCOUT_TAGS:
            raise ValueError(f"{slug}: 'scout_config.tags' must have {MAX_SCOUT_TAGS} tags or fewer")

    return raw


def _parse_skill(skill_dir: Path) -> dict[str, Any]:
    slug = skill_dir.name
    if not SLUG_PATTERN.match(slug) or "--" in slug or len(slug) > 64:
        raise ValueError(f"Invalid skill slug '{slug}' — lowercase letters, numbers, single hyphens only.")

    # Reject a symlinked skill root too: iterdir()/is_dir() would follow it and embed an out-of-tree
    # directory the per-file symlink check and safety scan (which doesn't descend into symlinks)
    # never see.
    if skill_dir.is_symlink():
        raise ValueError(f"{slug}: skill directories must not be symlinks")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"{slug}: missing SKILL.md")

    match = FRONTMATTER_RE.match(skill_md.read_text())
    if not match:
        raise ValueError(f"{slug}: SKILL.md must start with a YAML frontmatter block")
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    for required in ("name", "description"):
        if not frontmatter.get(required):
            raise ValueError(f"{slug}: frontmatter is missing required field '{required}'")

    trust_tier = frontmatter.get("trust_tier", "community")
    if trust_tier not in VALID_TRUST_TIERS:
        raise ValueError(f"{slug}: trust_tier must be one of {sorted(VALID_TRUST_TIERS)}")

    kind = frontmatter.get("kind", KIND_SKILL)
    if kind not in VALID_KINDS:
        raise ValueError(f"{slug}: kind must be one of {sorted(VALID_KINDS)}")
    if kind != KIND_SCOUT and frontmatter.get("scout_config"):
        # The store would list this entry as a skill while its author expected a scout.
        raise ValueError(f"{slug}: 'scout_config' is only valid with 'kind: scout'")
    scout_config = _validate_scout_config(frontmatter.get("scout_config"), slug) if kind == KIND_SCOUT else {}

    skill_root = skill_dir.resolve()
    files: list[dict[str, str]] = []
    total_bytes = len(body.encode())
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir).as_posix()
        # Reject symlinks outright: read_text() would follow them and embed out-of-tree content
        # (e.g. a link to .git/config, which checkout populates with the runner's auth token) into
        # the public registry.
        if path.is_symlink():
            raise ValueError(f"{slug}: symlinks are not allowed ('{rel}')")
        if path.is_dir() or path.name == "SKILL.md":
            continue
        if not path.resolve().is_relative_to(skill_root):
            raise ValueError(f"{slug}: '{rel}' resolves outside the skill directory")
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"{slug}: '{rel}' is {size} bytes, over the {MAX_FILE_BYTES}-byte per-file limit")
        try:
            content = path.read_text()
        except UnicodeDecodeError as exc:
            raise ValueError(f"{slug}: '{rel}' is not UTF-8 text; only text files may be bundled") from exc
        total_bytes += size
        content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
        files.append({"path": rel, "content": content, "content_type": content_type})

    if total_bytes > MAX_SKILL_BYTES:
        raise ValueError(f"{slug}: embedded content is {total_bytes} bytes, over the {MAX_SKILL_BYTES}-byte limit")

    # The scout-create form takes instructions but no files, so a scout would arrive without the
    # references its body cites.
    if kind == KIND_SCOUT and files:
        raise ValueError(f"{slug}: a scout cannot bundle files; put everything it needs in SKILL.md")

    entry: dict[str, Any] = {
        "slug": slug,
        "name": str(frontmatter["name"]),
        "description": str(frontmatter["description"]).strip(),
        "body": body,
        "license": str(frontmatter.get("license", "")),
        "compatibility": str(frontmatter.get("compatibility", "")),
        "allowed_tools": _list_of_str(frontmatter, slug, "allowed_tools"),
        "metadata": dict(frontmatter.get("metadata", {}) or {}),
        "tags": _list_of_str(frontmatter, slug, "tags"),
        "trust_tier": trust_tier,
        "author_handle": str(frontmatter.get("author_handle", "")),
        "github_url": f"https://github.com/{REPO}/tree/{BRANCH}/skills/{slug}",
        # Provenance is the commit that PostHog fetches registry.json at, plus github_url. We do NOT
        # embed the live build commit here: it would change every commit and make the checked-in
        # registry.json perpetually stale against itself (and against CI's merge GITHUB_SHA).
        "source_sha": "",
        "files": files,
    }
    # Left off a plain skill, which PostHog reads as the default kind, so skill entries stay unchanged.
    if kind == KIND_SCOUT:
        entry["kind"] = kind
        entry["scout_config"] = scout_config
    return entry


def build_registry() -> dict[str, Any]:
    skills = [
        _parse_skill(d)
        for d in sorted(SKILLS_DIR.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]
    slugs = [s["slug"] for s in skills]
    duplicates = {s for s in slugs if slugs.count(s) > 1}
    if duplicates:
        raise ValueError(f"Duplicate skill slugs: {sorted(duplicates)}")
    return {"version": 1, "skills": skills}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if registry.json is stale.")
    args = parser.parse_args()

    registry = build_registry()
    serialized = json.dumps(registry, indent=2, sort_keys=True) + "\n"

    if args.check:
        current = REGISTRY_PATH.read_text() if REGISTRY_PATH.exists() else ""
        if current != serialized:
            print("registry.json is out of date — run: python scripts/build_registry.py", file=sys.stderr)
            return 1
        print("registry.json is up to date.")
        return 0

    REGISTRY_PATH.write_text(serialized)
    print(f"Wrote {REGISTRY_PATH} with {len(registry['skills'])} skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
