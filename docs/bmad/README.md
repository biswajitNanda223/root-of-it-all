# BMAD artifacts (Breakthrough Method for Agile AI-Driven Development)

This folder holds the planning artifacts the BMAD agents (Analyst → PM → Architect → PO → SM → Dev → QA) read and
produce. Flow used here:

1. [`project-brief.md`](project-brief.md) – Analyst
2. [`prd.md`](prd.md) – PM (epics + requirements)
3. [`../architecture.md`](../architecture.md) + ADRs – Architect
4. [`stories/`](stories/) – SM-sharded stories with acceptance criteria and a Definition of Done
5. Dev implements one story at a time; QA gate = `scripts/check.sh`

To use the full agent workflow, install BMAD at the repo root (`npx bmad-method install`) and point it at
`docs/prd.md`-style locations (`docs/bmad/prd.md`, `docs/architecture.md`). Source-of-truth stays in this repo.

## Definition of Done (all stories)
- [ ] Acceptance criteria met and demonstrated by tests
- [ ] `scripts/check.sh` green (ruff, mypy --strict, pytest ≥ 85 % cov, migration drift)
- [ ] Docs/ADR updated if behaviour or architecture changed
- [ ] Staging image builds (`scripts/docker.sh staging build`)
