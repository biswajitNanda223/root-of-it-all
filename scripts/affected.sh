#!/usr/bin/env bash
# Print workspace projects affected by the current changes: affected.sh [--base REF] [--json]
source "$(dirname "$0")/_lib.sh"
exec python3 tooling/affected.py "$@"
