# Git workflow & commit checks

Install once with `scripts/bootstrap.sh` (sets `commit.template` and installs three hook types).

| Stage | Hook | Purpose |
|---|---|---|
| pre-commit | whitespace/EOF/line-endings, YAML/TOML/JSON, merge-conflict & case-conflict, large files (>700 KB), shebang/exec bits | hygiene |
| pre-commit | `detect-private-key` + `scripts/hooks/scan_secrets.py` | no AWS/GitHub/Slack/Anthropic-style keys or PEM blocks (`# pragma: allowlist secret` to waive) |
| pre-commit | `shellcheck`, `ruff` (fix) + `ruff format` | scripts and Python |
| pre-commit | migration drift (only if models/migrations changed) | schema and Alembic never diverge |
| pre-commit | `no-commit-to-branch main` | work on branches, merge via PR |
| commit-msg | `scripts/hooks/commit_msg.py` | **Conventional Commits**: `type(scope)?!: summary` (<=100 chars, no period, blank line before body) |
| pre-push | `scripts/hooks/pre-push.sh` | lint + `mypy --strict` + tests **only for affected projects** |

CI repeats the same checks (`commits` job on PRs: PR title + every commit + secret scan) so `--no-verify` cannot
bypass them.

## Affected projects (monorepo-aware)
`python tooling/affected.py [--base origin/main] [--json]` maps changed files to workspace members and closes over
the dependency graph read from each `pyproject.toml` (change `rio-core` -> `api` is affected too). Repo-wide files
(lockfile, root `pyproject.toml`, `tooling/`, Dockerfile, compose, CI) affect everything. It drives the pre-push hook and
the CI `changes` job (the Docker job runs only when runtime inputs changed).

## Useful commands
```bash
scripts/affected.sh                  # what would CI/pre-push test?
uv run pre-commit run --all-files    # or: mise run hooks
git commit                           # opens .gitmessage template
```
Types: `feat fix perf refactor docs test build ci chore style revert`. Suggested scopes: `api core db native docker deps docs ci`.
