"""pre-commit: block obvious secrets in staged files (high-signal patterns only)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "anthropic/openai key": re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{32,}\b"),
}
ALLOW = "pragma: allowlist secret"
SKIP_SUFFIX = {".lock", ".png", ".jpg", ".so", ".db"}


def main(paths: list[str]) -> int:
    bad = 0
    for p in paths:
        path = Path(p)
        if path.suffix in SKIP_SUFFIX or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
            if ALLOW in line:
                continue
            for name, rx in PATTERNS.items():
                if rx.search(line):
                    print(f"{p}:{n}: possible {name}", file=sys.stderr)
                    bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
