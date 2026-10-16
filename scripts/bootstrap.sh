#!/usr/bin/env bash
# Install toolchain deps, sync the workspace, install git hooks.
source "$(dirname "$0")/_lib.sh"

log "Syncing workspace (frozen if lockfile exists)"
if [[ -f uv.lock ]]; then uv sync --frozen; else uv sync; fi
[[ -f .env ]] || { cp .env.example .env; log "Created .env from .env.example"; }
if [[ -d .git ]]; then uv run pre-commit install --install-hooks; fi
log "Done. Next: scripts/dev.sh"
