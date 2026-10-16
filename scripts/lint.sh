#!/usr/bin/env bash
# Ruff lint + format check.
source "$(dirname "$0")/_lib.sh"

uv run ruff check . "$@"
uv run ruff format --check .
