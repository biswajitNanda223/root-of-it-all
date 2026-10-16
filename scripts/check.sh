#!/usr/bin/env bash
# Everything CI runs: lint, types, tests, migration drift.
source "$(dirname "$0")/_lib.sh"

"$(dirname "$0")/lint.sh"
"$(dirname "$0")/typecheck.sh"
COV=1 "$(dirname "$0")/test.sh" -q
"$(dirname "$0")/migrate.sh" check
