#!/usr/bin/env bash
# Alembic per service: migrate.sh [service|all] [upgrade head|revision -m msg|check|downgrade -1|...]
source "$(dirname "$0")/_lib.sh"
if [[ "${1:-}" == "all" ]]; then
  shift; rc=0
  for s in $(all_services); do log "migrate $s: ${*:-upgrade head}"; "$0" "$s" "$@" || rc=1; done
  exit "$rc"
fi
pick_service "$@"
[[ ${#REST[@]} -gt 0 ]] || REST=(upgrade head)
ini="apps/$SERVICE/alembic.ini"
[[ -f "$ini" ]] || die "$SERVICE has no alembic.ini"
case "${REST[0]}" in
  check)  # schema == migrations? runs against a throw-away SQLite file
    tmpdb="$(mktemp -u)"
    export "$(svc database_env)=sqlite+aiosqlite:///$tmpdb"
    uv run alembic -c "$ini" upgrade head
    uv run alembic -c "$ini" check
    rm -f "$tmpdb"; exit 0 ;;
  revision) REST=(revision --autogenerate "${REST[@]:1}") ;;
esac
dx_prefix "${APP_ENV:-development}"
exec "${DX[@]}" uv run alembic -c "$ini" "${REST[@]}"
