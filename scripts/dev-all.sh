#!/usr/bin/env bash
# Run EVERY service with auto-reload in one terminal (Ctrl-C stops all).
source "$(dirname "$0")/_lib.sh"
pids=()
cleanup() { trap - INT TERM EXIT; for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done; wait 2>/dev/null || true; }
trap cleanup INT TERM EXIT
for s in $(all_services); do
  log "starting $s on :$(python3 tooling/service.py get "$s" port)"
  "$(dirname "$0")/dev.sh" "$s" 2>&1 | sed -u "s/^/[$s] /" &
  pids+=("$!")
done
wait
