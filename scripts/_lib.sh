#!/usr/bin/env bash
# Shared helpers. Source me; don't execute me.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "'$1' is required (see docs/development.md)"; }

# Prefer LLVM's lld for any native build (C extensions / Rust wheels).
use_lld() {
  if command -v ld.lld >/dev/null 2>&1 && command -v clang >/dev/null 2>&1; then
    export CC="${CC:-clang}" CXX="${CXX:-clang++}"
    export LDFLAGS="${LDFLAGS:--fuse-ld=lld}"
    export RUSTFLAGS="${RUSTFLAGS:--C link-arg=-fuse-ld=lld}"
  fi
}

# Load .env if present (non-fatal).
if [[ -f "$ROOT/.env" ]]; then set -a; . "$ROOT/.env"; set +a; fi
need uv
use_lld
