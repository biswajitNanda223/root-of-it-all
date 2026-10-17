# ADR 0010 - Generate container infrastructure from `[tool.rio.service]`
Status: accepted
**Context** Adding a service meant hand-editing compose files, bake targets and Dockerfile mounts - easy to forget.
**Decision** `apps/<name>/pyproject.toml [tool.rio.service]` is the single registry (module, port, DB, dependencies, env).
`tooling/service.py generate` writes `compose*.yaml`, `docker-bake.services.hcl` and the Dockerfile manifest region; a
pre-commit hook and CI run `--check`. A scaffolder creates the app and runs the generator. **Consequences** One place to
change; generated files must never be edited by hand (headers say so).
