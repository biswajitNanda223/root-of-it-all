#!/usr/bin/env bash
# Alembic wrapper: migrate.sh [upgrade head|revision -m msg|check|downgrade -1].
source "$(dirname "$0")/_lib.sh"

[[ $# -gt 0 ]] || set -- upgrade head
if [[ "$1" == "check" ]]; then
  tmpdb="$(mktemp -u)"
  export RIO_DATABASE_URL="sqlite+aiosqlite:///$tmpdb"
  uv run alembic -c apps/api/alembic.ini upgrade head
fi
if [[ "$1" == "revision" ]]; then set -- revision --autogenerate "${@:2}"; fi
exec uv run alembic -c apps/api/alembic.ini "$@"
