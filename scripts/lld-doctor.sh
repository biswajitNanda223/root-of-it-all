#!/usr/bin/env bash
# Prove lld is the linker: lld-doctor.sh [project-dir] [profile]. Exits non-zero if it isn't.
source "$(dirname "$0")/_lib.sh"
PROJECT="${1:-packages/native}"; PROFILE="${2:-${LLD_PROFILE:-dev}}"
need clang; need ld.lld; need readelf
use_lld "$PROJECT" "$PROFILE"
log "lld $(ld.lld --version | head -1)"
log "active: ${LLD_ACTIVE:-none}  LDFLAGS=$LDFLAGS"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
printf 'int main(void){return 0;}\n' > "$tmp/t.c"
# shellcheck disable=SC2086
$CC $CFLAGS $LDFLAGS "$tmp/t.c" -o "$tmp/t"
if readelf -p .comment "$tmp/t" | grep -Eq "Linker:.*LLD"; then log "OK: binary was linked by LLD"
else die "binary was NOT linked by lld"; fi
