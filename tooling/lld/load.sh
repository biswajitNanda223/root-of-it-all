#!/usr/bin/env bash
# Source me: . tooling/lld/load.sh <project-dir> [profile]
# Works inside Docker too (ROOT defaults to the directory three levels up from this file).
_lld_root="${ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
_lld_project="${1:-}"; _lld_profile="${2:-${LLD_PROFILE:-dev}}"
if command -v ld.lld >/dev/null 2>&1 && command -v "${CC:-clang}" >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  . "$_lld_root/tooling/lld/base.env"
  # shellcheck disable=SC1090
  [ -f "$_lld_root/tooling/lld/profiles/$_lld_profile.env" ] && . "$_lld_root/tooling/lld/profiles/$_lld_profile.env"
  # shellcheck disable=SC1090
  [ -n "$_lld_project" ] && [ -f "$_lld_root/$_lld_project/lld.env" ] && . "$_lld_root/$_lld_project/lld.env"
  export LLD_ACTIVE="$_lld_project@$_lld_profile"
else
  echo "lld/clang not found - falling back to the system linker" >&2
fi
unset _lld_root _lld_project _lld_profile
