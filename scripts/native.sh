#!/usr/bin/env bash
# (Re)build workspace C extensions with the layered lld profile: native.sh [dev|release]
# uv's wheel cache is keyed by source, not by compiler flags, so force a rebuild when the profile changes.
source "$(dirname "$0")/_lib.sh"
PROFILE="${1:-${LLD_PROFILE:-dev}}"
use_lld packages/native "$PROFILE"
log "building rio-native with ${LLD_ACTIVE:-system toolchain}"
uv sync --reinstall-package rio-native
uv run python -c "import rio_native as n; print('native extension:', n.NATIVE)"
f="$(find packages/native/src -name '_fast*.so' | head -1)"
if [[ -n "$f" ]] && command -v readelf >/dev/null; then
  readelf -p .comment "$f" | grep -Eq 'Linker:.*LLD' && log "OK: $f linked by LLD" || log "note: no LLD marker in $f"
fi
