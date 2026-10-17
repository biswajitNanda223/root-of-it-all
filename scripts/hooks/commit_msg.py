"""commit-msg hook: Conventional Commits. Usage: commit_msg.py <message-file> (or --text "msg")."""

from __future__ import annotations

import re
import sys

TYPES = "build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
HEADER = re.compile(rf"^(?:{TYPES})(?:\([a-z0-9._/-]+\))?!?: \S.*$")
SKIP = re.compile(r"^(Merge |Revert \"|fixup! |squash! )")
MAX_HEADER = 100


def check(message: str) -> list[str]:
    lines = [ln for ln in message.splitlines() if not ln.startswith("#")]
    header = next((ln for ln in lines if ln.strip()), "")
    if SKIP.match(header):
        return []
    errors = []
    if not HEADER.match(header):
        errors.append(
            f"header must look like 'type(scope)?: summary' with type in [{TYPES.replace('|', ', ')}]"
        )
    if len(header) > MAX_HEADER:
        errors.append(f"header is {len(header)} chars; max {MAX_HEADER}")
    if header.endswith("."):
        errors.append("header must not end with a period")
    if len(lines) > 1 and lines[1].strip():
        errors.append("leave a blank line between header and body")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) > 2 and argv[1] == "--text":
        text = argv[2]
    else:
        with open(argv[1], encoding="utf-8") as fh:
            text = fh.read()
    errors = check(text)
    for e in errors:
        print(f"commit-msg: {e}", file=sys.stderr)
    if errors:
        print("see .gitmessage / CONTRIBUTING.md (Conventional Commits)", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
