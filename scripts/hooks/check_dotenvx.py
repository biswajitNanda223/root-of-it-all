"""Guard dotenvx hygiene: no private keys / local files committed, and committed secret env files are encrypted.

usage: check_dotenvx.py <files...>     (pre-commit passes staged .env* files; CI passes `git ls-files '.env*'`)
"""

from __future__ import annotations

import sys
from pathlib import Path

PLAIN_OK = {".env.example", ".env.development"}  # non-secret by contract
MUST_ENCRYPT = {".env.staging", ".env.production", ".env.ci"}
NEVER = {".env.keys", ".env.local", ".env"}


def check(path: Path) -> list[str]:
    name = path.name
    if name in NEVER or name.startswith(".env.keys"):
        return [f"{path}: must never be committed (private keys / local overrides)"]
    if name in PLAIN_OK:
        return []
    if name not in MUST_ENCRYPT:
        return [
            f"{path}: unknown env file; allowed plaintext: {sorted(PLAIN_OK)}, encrypted: {sorted(MUST_ENCRYPT)}"
        ]
    errors = []
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.startswith("DOTENV_PUBLIC_KEY"):
            continue
        if not value.strip().strip("\"'").startswith("encrypted:"):
            errors.append(f"{path}:{n}: {key} is NOT encrypted - run scripts/env.sh encrypt <env>")
    if not any(ln.startswith("DOTENV_PUBLIC_KEY") for ln in path.read_text().splitlines()):
        errors.append(f"{path}: no DOTENV_PUBLIC_KEY header - file was never encrypted")
    return errors


def main(argv: list[str]) -> int:
    errors = [e for a in argv if Path(a).exists() for e in check(Path(a))]
    errors += [
        f"{a}: must never be committed"
        for a in argv
        if Path(a).name in NEVER and not Path(a).exists()
    ]
    for e in errors:
        print(f"dotenvx: {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
