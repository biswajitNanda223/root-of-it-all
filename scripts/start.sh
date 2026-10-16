#!/usr/bin/env bash
# Run the API in production mode (no reload, multiple workers).
source "$(dirname "$0")/_lib.sh"

exec uv run --frozen --no-dev --package api uvicorn app.main:app_factory --factory \
  --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" \
  --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" "$@"
