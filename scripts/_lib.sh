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

# ---------------------------------------------------------------- services (apps/*)
# pick_service "$@": SERVICE = first arg if it names an app (default $DEFAULT_SERVICE or api); REST = remaining args.
SERVICE="" ; REST=()
pick_service() {
  SERVICE="${DEFAULT_SERVICE:-api}"
  if [[ -n "${1:-}" && -f "apps/$1/pyproject.toml" ]]; then SERVICE="$1"; shift; fi
  REST=("$@")
}
svc() { python3 "$ROOT/tooling/service.py" get "$SERVICE" "$1"; }   # svc module | port | database_env | ...
all_services() { python3 "$ROOT/tooling/service.py" list; }

# ---------------------------------------------------------------- dotenvx (encrypted env files)
# Layering (first file wins; already-exported variables always win, so CI/prod overrides work):
#   .env.local (untracked overrides)  >  .env.$APP_ENV (committed; staging/production are *encrypted*)
# Private keys: DOTENV_PRIVATE_KEY_<ENV> in the environment (CI / secret manager) or the untracked .env.keys.
DOTENVX_VERSION="${DOTENVX_VERSION:-2.37.0}"
DXBIN=()
dx_bin() {
  [[ ${#DXBIN[@]} -gt 0 ]] && return 0
  if command -v dotenvx >/dev/null 2>&1; then DXBIN=(dotenvx)
  elif command -v npx >/dev/null 2>&1; then DXBIN=(npx --yes "@dotenvx/dotenvx@${DOTENVX_VERSION}")
  else die "dotenvx not found: 'mise install' or 'npm i -g @dotenvx/dotenvx@${DOTENVX_VERSION}'"; fi
}

# dx_prefix <env-name>: sets DX=(...) so that `"${DX[@]}" cmd` runs cmd with decrypted variables (or plain cmd).
# shellcheck disable=SC2034  # DX is consumed by the scripts that source this file
DX=()
dx_prefix() {
  APP_ENV="${1:-${APP_ENV:-development}}"
  DX=()
  local args=() f
  for f in .env.local ".env.${APP_ENV}"; do [[ -f "$f" ]] && args+=(-f "$f"); done
  [[ ${#args[@]} -gt 0 ]] || return 0
  dx_bin
  # shellcheck disable=SC2034
  DX=("${DXBIN[@]}" run "${args[@]}" --no-native --no-armor --log-level error --)
}
need uv
# uv may (re)build workspace C extensions at any `uv run`/`uv sync`, so the native project's lld env is always active.
# Scripts that target another project call `use_lld <dir> [profile]` again to layer its overrides.
use_lld "${LLD_PROJECT:-packages/native}"
