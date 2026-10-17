#!/usr/bin/env bash
# Regenerate files derived from apps/*/pyproject.toml (compose*.yaml, docker-bake.services.hcl, Dockerfile manifests).
source "$(dirname "$0")/_lib.sh"
exec python3 tooling/service.py generate "$@"
