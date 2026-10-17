"""Which workspace projects does a change touch (directly or via a workspace dependency)?

    python tooling/affected.py [--base origin/main] [--json] [--paths a b ...]

Reads the uv workspace from pyproject.toml, builds the reverse dependency graph from each member's
`[project].dependencies`, maps changed files to members, then closes over dependents.
Changes to repo-wide files (lockfile, toolchain, Docker, CI) affect everything.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOBAL = (
    "pyproject.toml",
    "uv.lock",
    "tooling/",
    "Dockerfile",
    "compose",
    ".github/",
    "mise.toml",
    ".cargo/",
)


def members() -> dict[str, tuple[str, set[str]]]:
    """dir -> (distribution name, names of dependencies)"""
    patterns = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["uv"]["workspace"][
        "members"
    ]
    out: dict[str, tuple[str, set[str]]] = {}
    for pattern in patterns:
        for d in sorted(glob.glob(str(ROOT / pattern))):
            pp = Path(d) / "pyproject.toml"
            if pp.exists():
                proj = tomllib.loads(pp.read_text())["project"]
                deps = {
                    re.split(r"[\[<>=!~ ;]", dep, maxsplit=1)[0].lower()
                    for dep in proj.get("dependencies", [])
                }
                out[str(Path(d).relative_to(ROOT))] = (proj["name"].lower(), deps)
    return out


def changed_files(base: str) -> list[str]:
    def git(*a: str) -> list[str]:
        r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603, S607
        return [x for x in r.stdout.splitlines() if x]

    merge_base = git("merge-base", base, "HEAD")
    ref = merge_base[0] if merge_base else base
    return sorted(
        set(git("diff", "--name-only", ref) + git("ls-files", "--others", "--exclude-standard"))
    )


def affected(files: list[str]) -> list[str]:
    ms = members()
    if any(f.startswith(GLOBAL) for f in files):
        return sorted(ms)
    hit = {d for d in ms for f in files if f.startswith(d + "/")}
    names = {d: ms[d][0] for d in ms}
    changed = True
    while changed:  # transitive closure over dependents
        changed = False
        for d, (_, deps) in ms.items():
            if d not in hit and any(names[h] in deps for h in hit):
                hit.add(d)
                changed = True
    return sorted(hit)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--paths", nargs="*")
    args = ap.parse_args()
    result = affected(args.paths if args.paths is not None else changed_files(args.base))
    print(json.dumps(result) if args.json else "\n".join(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
