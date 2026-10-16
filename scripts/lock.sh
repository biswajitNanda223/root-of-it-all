#!/usr/bin/env bash
# Refresh uv.lock; --upgrade to bump versions.
source "$(dirname "$0")/_lib.sh"

exec uv lock "$@"
