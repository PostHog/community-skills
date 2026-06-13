#!/usr/bin/env python3
"""Lightweight prompt-injection / data-exfiltration heuristic scan for community skills.

This is a first-pass safety net, NOT a substitute for human PR review. It flags instruction patterns
that commonly indicate an attempt to make an agent leak data or act against the user's intent.
Exits 1 if any skill trips a heuristic.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

# (pattern, human-readable reason). Patterns are intentionally conservative to keep false positives low.
HEURISTICS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"ignore (all |any |previous |prior )+(instructions|prompts)", re.I), "instruction-override phrasing"),
    (re.compile(r"\b(exfiltrate|leak|send).{0,40}(api[_ ]?key|secret|token|credential|password)", re.I), "credential exfiltration"),
    (re.compile(r"(curl|wget|fetch|http)\b.{0,80}(POST|--data|api[_ ]?key|token)", re.I), "data sent to external endpoint"),
    (re.compile(r"\bbase64\b.{0,40}(decode|encode).{0,40}(exec|eval|run)", re.I), "obfuscated execution"),
    (re.compile(r"do not (tell|inform|mention).{0,30}(user|human)", re.I), "instruction to hide actions from the user"),
]


def main() -> int:
    findings: list[str] = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        text = skill_md.read_text()
        for pattern, reason in HEURISTICS:
            if pattern.search(text):
                findings.append(f"{skill_md.relative_to(ROOT)}: possible {reason}")

    if findings:
        print("Safety scan flagged the following — a maintainer must review before merge:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1

    print("Safety scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
