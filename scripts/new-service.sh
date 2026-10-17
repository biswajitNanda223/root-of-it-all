#!/usr/bin/env bash
# Scaffold a new service: new-service.sh <name> [--port N] [--title "Billing"]
#   creates apps/<name>, registers it in the workspace, writes its first Alembic migration and regenerates
#   compose*.yaml / docker-bake.services.hcl. Afterwards: scripts/dev.sh <name>
source "$(dirname "$0")/_lib.sh"
[[ $# -ge 1 ]] || die "usage: new-service.sh <name> [--port N] [--title T]"
name="$1"
python3 tooling/scaffold.py "$@"
log "locking + syncing the workspace"
uv lock >/dev/null && uv sync >/dev/null
log "generating the first migration"
env_name="$(echo "$name" | tr a-z A-Z)_DATABASE_URL"
tmpdb="$(mktemp -u)"
export "$env_name=sqlite+aiosqlite:///$tmpdb"
uv run alembic -c "apps/$name/alembic.ini" revision --autogenerate -m "initial schema" --rev-id 0001
rm -f "$tmpdb"
python3 tooling/service.py generate >/dev/null
uv run ruff check --fix -q "apps/$name" || true
uv run ruff format "apps/$name" >/dev/null
log "done: scripts/dev.sh $name   |   scripts/test.sh apps/$name/tests   |   scripts/migrate.sh $name"
