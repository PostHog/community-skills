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

    return {
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
