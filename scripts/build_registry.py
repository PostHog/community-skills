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
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = os.environ.get("GITHUB_REPOSITORY", "PostHog/community-skills")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REGISTRY_PATH = ROOT / "registry.json"

SLUG_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
VALID_TRUST_TIERS = {"official", "verified", "community"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _git_sha() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return ""


def _parse_skill(skill_dir: Path, repo_sha: str) -> dict[str, Any]:
    slug = skill_dir.name
    if not SLUG_PATTERN.match(slug) or "--" in slug or len(slug) > 64:
        raise ValueError(f"Invalid skill slug '{slug}' — lowercase letters, numbers, single hyphens only.")

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

    files: list[dict[str, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if path.is_dir() or path.name == "SKILL.md":
            continue
        rel = path.relative_to(skill_dir).as_posix()
        content_type = mimetypes.guess_type(path.name)[0] or "text/plain"
        files.append({"path": rel, "content": path.read_text(), "content_type": content_type})

    return {
        "slug": slug,
        "name": str(frontmatter["name"]),
        "description": str(frontmatter["description"]).strip(),
        "body": body,
        "license": str(frontmatter.get("license", "")),
        "compatibility": str(frontmatter.get("compatibility", "")),
        "allowed_tools": list(frontmatter.get("allowed_tools", []) or []),
        "metadata": dict(frontmatter.get("metadata", {}) or {}),
        "tags": list(frontmatter.get("tags", []) or []),
        "trust_tier": trust_tier,
        "author_handle": str(frontmatter.get("author_handle", "")),
        "github_url": f"https://github.com/{REPO}/tree/{BRANCH}/skills/{slug}",
        "source_sha": repo_sha,
        "files": files,
    }


def build_registry() -> dict[str, Any]:
    repo_sha = _git_sha()
    skills = [
        _parse_skill(d, repo_sha)
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
