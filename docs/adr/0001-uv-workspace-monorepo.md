# ADR 0001 – uv workspace monorepo
Status: accepted
**Context** Multiple services share code and must evolve together. **Decision** One repo, uv workspace
(`apps/*`, `packages/*`), single lockfile, root dev group. **Consequences** Atomic cross-package changes, fast
resolver, simple CI; need discipline on the apps→packages dependency direction.
