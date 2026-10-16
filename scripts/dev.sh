#!/usr/bin/env bash
# Run the API with auto-reload.
source "$(dirname "$0")/_lib.sh"

export RIO_ENVIRONMENT="${RIO_ENVIRONMENT:-development}" RIO_AUTO_CREATE_TABLES="${RIO_AUTO_CREATE_TABLES:-true}"
exec uv run --package api uvicorn app.main:app_factory --factory \
  --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --reload \
  --reload-dir apps/api/src --reload-dir packages "$@"
