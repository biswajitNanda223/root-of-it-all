#!/usr/bin/env bash
# Shared helpers. Source me; don't execute me.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "'$1' is required (see docs/development.md)"; }

# Layered lld toolchain (repo -> profile -> project). See tooling/lld/README.md.
#   use_lld [project-dir] [profile]      e.g. use_lld packages/native release
use_lld() {
  # shellcheck disable=SC1091
  . "$ROOT/tooling/lld/load.sh" "${1:-}" "${2:-${LLD_PROFILE:-dev}}"
}

# Load .env if present (non-fatal).
if [[ -f "$ROOT/.env" ]]; then set -a; . "$ROOT/.env"; set +a; fi
need uv
# uv may (re)build workspace C extensions at any `uv run`/`uv sync`, so the native project's lld env is always active.
# Scripts that target another project call `use_lld <dir> [profile]` again to layer its overrides.
use_lld "${LLD_PROJECT:-packages/native}"
