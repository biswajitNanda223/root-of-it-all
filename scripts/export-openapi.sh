#!/usr/bin/env bash
# Write each service's OpenAPI schema to docs/openapi/<service>.json: export-openapi.sh [service].
source "$(dirname "$0")/_lib.sh"
export RIO_ENVIRONMENT=test
mkdir -p docs/openapi
targets=("$@"); [[ ${#targets[@]} -gt 0 ]] || mapfile -t targets < <(all_services)
for s in "${targets[@]}"; do
  # shellcheck disable=SC2034  # SERVICE is read by svc()
  SERVICE="$s"; module="$(svc module)"
  uv run python - "$module" > "docs/openapi/$s.json" <<'PY'
import importlib, json, sys
mod, attr = sys.argv[1].split(":")
print(json.dumps(getattr(importlib.import_module(mod), attr)().openapi(), indent=2))
PY
  log "wrote docs/openapi/$s.json"
done
