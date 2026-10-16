# Development

## Prerequisites
- [mise](https://mise.jdx.dev) (pins Python 3.13 + uv) **or** `uv` ≥ 0.11 and Python ≥ 3.12
- Optional, for native builds: `clang` and `lld` (`apt install clang lld` / `brew install llvm lld`)
- Docker with Compose v2 for the container workflows

## Daily loop
```bash
scripts/bootstrap.sh     # once
scripts/dev.sh           # run
scripts/format.sh && scripts/check.sh
```
Everything runs through `uv run`, so there is no venv to activate. Run ad-hoc commands with
`uv run --package api python -m app` or `uv run pytest apps/api/tests/unit -k auth`.

## Dependencies
```bash
uv add --package api httpx            # runtime dep of one app
uv add --dev pytest-xdist             # workspace-wide dev dep
uv add --package rio-core pydantic    # shared library
scripts/lock.sh --upgrade             # bump everything
```
Commit `uv.lock`. Docker and CI use `--frozen`.

## Adding a feature (vertical slice)
1. Entity/port in `domain/`; rule in `services/`.
2. Adapter in `infrastructure/`; model change → `scripts/migrate.sh revision -m "add x"`.
3. DTO in `api/schemas.py`, router in `api/v1/`, register in `api/router.py`.
4. Unit test with fakes; integration test with `TestClient`.

## Database
`scripts/migrate.sh` (default `upgrade head`). Point at Postgres with `RIO_DATABASE_URL=postgresql+asyncpg://…`.

## Testing
`scripts/test.sh` · `COV=1 scripts/test.sh` enforces ≥ 85 % coverage. Tests use a per-test SQLite file.
