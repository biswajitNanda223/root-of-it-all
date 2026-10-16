#!/usr/bin/env bash
# Auto-fix lint issues and format.
source "$(dirname "$0")/_lib.sh"

uv run ruff check . --fix "$@"
uv run ruff format .
