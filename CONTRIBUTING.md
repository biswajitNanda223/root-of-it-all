# Contributing
1. Branch from `main`; keep PRs to one BMAD story.
2. `scripts/bootstrap.sh`, change, `scripts/format.sh`, `scripts/check.sh` must pass.
3. Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`); update `CHANGELOG.md` and ADRs when relevant.
4. Never commit `.env` or secrets; hooks run `detect-private-key`.
