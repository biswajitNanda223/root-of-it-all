#!/usr/bin/env bash
# Write the OpenAPI schema to docs/openapi.json (contract artifact).
source "$(dirname "$0")/_lib.sh"

RIO_ENVIRONMENT=test uv run python - <<'PY' > docs/openapi.json
import json
from rio_core.config import Settings
from app.main import create_app
print(json.dumps(create_app(Settings(environment="test")).openapi(), indent=2))
PY
log "wrote docs/openapi.json"
