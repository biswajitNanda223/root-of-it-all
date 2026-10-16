#!/usr/bin/env bash
# pre-push: lint + types everywhere (cheap), tests only for projects affected vs origin/main.
source "$(dirname "$0")/../_lib.sh"
log "pre-push: lint, types"
scripts/lint.sh >/dev/null
scripts/typecheck.sh >/dev/null
base="origin/main"; git rev-parse --verify -q "$base" >/dev/null || base="HEAD~1"
mapfile -t projects < <(python3 tooling/affected.py --base "$base")
[[ ${#projects[@]} -gt 0 ]] || { log "pre-push: no affected projects"; exit 0; }
dirs=(); for p in "${projects[@]}"; do [[ -d "$p/tests" ]] && dirs+=("$p/tests"); done
log "pre-push: tests for ${projects[*]}"
[[ ${#dirs[@]} -eq 0 ]] || uv run pytest -q "${dirs[@]}"
