#!/usr/bin/env bash
# Run one service in production mode: start.sh [service] [uvicorn args] (workers, proxy headers).
source "$(dirname "$0")/_lib.sh"
pick_service "$@"
dx_prefix "${APP_ENV:-production}"
exec "${DX[@]}" uv run --frozen --no-dev --package "$SERVICE" uvicorn "$(svc module)" --factory \
  --host "${HOST:-0.0.0.0}" --port "${PORT:-$(svc port)}" --workers "${WEB_CONCURRENCY:-2}" \
  --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" "${REST[@]}"
