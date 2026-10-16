# ADR 0007 - Commit checks and affected-project CI
Status: accepted
**Decision** Conventional Commits + secret scan + shellcheck + drift check as hooks (mirrored in CI), and a
dependency-aware `affected.py` to scope pre-push tests and the Docker job. **Consequences** Faster feedback in a growing
monorepo; hooks can be bypassed locally, so CI is the source of truth.
