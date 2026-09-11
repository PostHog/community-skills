#!/usr/bin/env python3
"""Assemble and validate a skill-update payload from files on disk.

Every write to the skills store goes through a JSON string typed into
`call skill-update ...`. Assembling that string by hand is where brackets go
missing and long `old` strings drift from the file. This script builds the
payload from files, checks that every `old` is non-empty and distinct from its
`new`, validates the JSON, and prints the exact `call` line.

    python3 skill_payload.py --skill my-inbox --base-version 9 \
        --edit HANDOVER.md old.txt new.txt \
        --edit working-set.md ws_old.txt ws_new.txt

Each --edit takes a bundled file path plus two local files holding the exact
`old` and `new` text. Repeat --edit for several edits, on the same file or on
different files; edits on one file are grouped into one file_edits entry.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--base-version", type=int, required=True)
    ap.add_argument("--edit", nargs=3, action="append", metavar=("PATH", "OLD_FILE", "NEW_FILE"), required=True)
    ap.add_argument("--description", help="pass a shortened description if the current one exceeds 1024 chars")
    args = ap.parse_args()

    grouped: dict[str, list[dict[str, str]]] = {}
    for path, old_file, new_file in args.edit:
        old = Path(old_file).read_text()
        new = Path(new_file).read_text()
        if not old.strip():
            print(f"{path}: old text from {old_file} is empty", file=sys.stderr)
            return 1
        if old == new:
            print(f"{path}: old and new are identical ({old_file}, {new_file})", file=sys.stderr)
            return 1
        # The call parser rejects the plus-minus sign and a digit followed by "+"; the escape keeps this file clean too.
        if "\u00b1" in new or re.search(r"\d\+", new):
            print(f"{path}: new text contains a plus-minus sign or a digit followed by +, which the call parser rejects; reword it", file=sys.stderr)
            return 1
        grouped.setdefault(path, []).append({"old": old, "new": new})

    payload = {
        "skill_name": args.skill,
        "base_version": args.base_version,
        "file_edits": [{"path": path, "edits": edits} for path, edits in grouped.items()],
    }
    if args.description:
        if len(args.description) > 1024:
            print(f"description is {len(args.description)} chars; the cap is 1024", file=sys.stderr)
            return 1
        payload["description"] = args.description

    text = json.dumps(payload, ensure_ascii=False)
    json.loads(text)
    print(f"call skill-update {text}")
    print(f"payload ok: {len(text)} chars, {sum(len(e) for e in grouped.values())} edit(s) across {len(grouped)} file(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())