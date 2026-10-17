#!/usr/bin/env bash
# Everything CI runs: lint, types, tests (+coverage), migration drift for every service, generated files fresh.
source "$(dirname "$0")/_lib.sh"
d="$(dirname "$0")"
"$d/lint.sh"
"$d/typecheck.sh"
COV=1 "$d/test.sh" -q
"$d/migrate.sh" all check
python3 tooling/service.py generate --check
