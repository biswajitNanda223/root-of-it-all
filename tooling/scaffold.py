"""Create a new service from tooling/templates/service and register it in the workspace.

    python tooling/scaffold.py <name> [--port N] [--title "Billing"]

Steps: copy template -> register in root pyproject (deps, sources, ruff/mypy/pytest/coverage paths) -> add its DB env
to .env.development -> (caller) uv lock/sync, first Alembic revision, `service.py generate`. See scripts/new-service.sh.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tooling" / "templates" / "service"
RESERVED = {"api", "catalog", "orders", "app", "test", "tests", "tooling", "scripts", "docs"}


def next_free_port() -> int:
    used = {
        int(m)
        for pp in (ROOT / "apps").glob("*/pyproject.toml")
        for m in re.findall(r"^port = (\d+)", pp.read_text(), re.M)
    }
    return next(p for p in range(8000, 8100) if p not in used)


def render(text: str, ctx: dict[str, str]) -> str:
    for key, value in ctx.items():
        text = text.replace(f"__{key}__", value)
    return text


def copy_template(dest: Path, ctx: dict[str, str]) -> None:
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        rel = Path(render(str(src.relative_to(TEMPLATE)), ctx))
        if rel.suffix == ".tmpl":  # keeps template manifests out of TOML/ruff discovery
            rel = rel.with_suffix("")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(render(src.read_text(), ctx).encode() if src.stat().st_size else b"")


def _insert_after(text: str, anchor: str, addition: str) -> str:
    if addition in text:
        return text
    if anchor not in text:
        raise SystemExit(f"cannot register: anchor {anchor!r} not found in pyproject.toml")
    return text.replace(anchor, anchor + addition, 1)


def register(name: str, pkg: str) -> None:
    p = ROOT / "pyproject.toml"
    s = p.read_text()
    s = re.sub(
        r'(dependencies = \[[^\]]*?)"\]',
        lambda m: m.group(0) if f'"{name}"' in m.group(0) else f'{m.group(1)}", "{name}"]',
        s,
        count=1,
    )
    s = _insert_after(s, "[tool.uv.sources]\n", f"{name} = {{ workspace = true }}\n")
    s = (
        s.replace('known-first-party = ["app",', f'known-first-party = ["app", "{pkg}",', 1)
        if f'"{pkg}"' not in s
        else s
    )
    s = (
        s.replace('src = ["apps/api/src",', f'src = ["apps/api/src", "apps/{name}/src",', 1)
        if f"apps/{name}/src" not in s
        else s
    )
    s = (
        s.replace(
            'mypy_path = ["apps/api/src",', f'mypy_path = ["apps/api/src", "apps/{name}/src",', 1
        )
        if f'"apps/{name}/src", "apps' not in s.split("mypy_path")[1].split("\n")[0]
        else s
    )
    s = (
        s.replace('testpaths = ["tests",', f'testpaths = ["tests", "apps/{name}/tests",', 1)
        if f"apps/{name}/tests" not in s
        else s
    )
    s = (
        s.replace('source = ["apps/api/src",', f'source = ["apps/api/src", "apps/{name}/src",', 1)
        if f"apps/{name}/src" not in s.split("[tool.coverage.run]")[1]
        else s
    )
    p.write_text(s)
    env = ROOT / ".env.development"
    line = f"{name.upper()}_DATABASE_URL=sqlite+aiosqlite:///./{name}.db\n"
    if env.exists() and line not in env.read_text():
        env.write_text(env.read_text().rstrip("\n") + "\n" + line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--port", type=int)
    ap.add_argument("--title")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9]{1,23}", a.name) or a.name in RESERVED:
        print(
            f"invalid or reserved name '{a.name}' (lowercase letters/digits, 2-24 chars)",
            file=sys.stderr,
        )
        return 2
    dest = ROOT / "apps" / a.name
    if dest.exists():
        print(f"{dest} already exists", file=sys.stderr)
        return 2
    pkg = f"{a.name}_service"
    ctx = {
        "name": a.name,
        "pkg": pkg,
        "ENV": a.name.upper(),
        "title": a.title or a.name.capitalize(),
        "port": str(a.port or next_free_port()),
    }
    try:
        copy_template(dest, ctx)
        register(a.name, pkg)
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    print(f"created apps/{a.name} (package {pkg}, port {ctx['port']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
