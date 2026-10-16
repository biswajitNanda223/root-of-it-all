#!/usr/bin/env bash
# Remove caches and build output (keeps .venv unless --all).
source "$(dirname "$0")/_lib.sh"

find . -name __pycache__ -not -path "./.venv/*" -prune -exec rm -rf {} +
rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dev.db
[[ "${1:-}" == "--all" ]] && rm -rf .venv || true
