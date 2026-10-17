#!/usr/bin/env bash
# Strict mypy over all workspace sources.
source "$(dirname "$0")/_lib.sh"

exec uv run mypy apps/*/src packages/*/src "$@"
