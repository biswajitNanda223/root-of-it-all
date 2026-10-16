# Contributing
1. Branch from `main` (direct commits to `main` are blocked by a hook); keep PRs to one BMAD story.
2. `scripts/bootstrap.sh` installs hooks; `scripts/format.sh` then `scripts/check.sh` must pass.
3. **Conventional Commits** (`feat(api): ...`, `fix(db): ...`; enforced locally and in CI). See [docs/git-workflow.md](docs/git-workflow.md).
4. Update `CHANGELOG.md`, ADRs and `docs/` when behaviour changes; re-export the contract with `scripts/export-openapi.sh`.
5. Model changes need an Alembic migration (`scripts/migrate.sh revision -m "..."`).
6. Secrets: only dotenvx-**encrypted** `.env.staging|production|ci` may be committed; never `.env.keys`, `.env.local` or plaintext values (hooks + CI enforce this; see [docs/secrets.md](docs/secrets.md)).
