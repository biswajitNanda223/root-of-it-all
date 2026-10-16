#!/usr/bin/env bash
# Run the test-suite (pass pytest args through; COV=1 for coverage).
source "$(dirname "$0")/_lib.sh"

if [[ "${COV:-0}" == "1" ]]; then exec uv run pytest --cov --cov-report=term-missing --cov-fail-under=85 "$@"; fi
exec uv run pytest "$@"
