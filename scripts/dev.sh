#!/usr/bin/env bash
# Run one service with auto-reload: dev.sh [service] [uvicorn args]   (default: api; ports come from pyproject).
source "$(dirname "$0")/_lib.sh"
pick_service "$@"
dx_prefix "${APP_ENV:-development}"
exec "${DX[@]}" uv run --package "$SERVICE" uvicorn "$(svc module)" --factory \
  --host "${HOST:-0.0.0.0}" --port "${PORT:-$(svc port)}" --reload \
  --reload-dir "apps/$SERVICE/src" --reload-dir packages "${REST[@]}"
