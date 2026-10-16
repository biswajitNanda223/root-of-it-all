# Project brief
**Problem** Teams re-invent FastAPI scaffolding and drift from production practices.
**Vision** A reference monorepo that is the default starting point for any service: fast to run, safe to ship.
**Users** Backend engineers, platform/DevOps, reviewers.
**Constraints** uv + shell entry points, Docker with a light staging image, lld for native builds, strict typing.
**Success** New service from clone to green CI < 10 min; image < 150 MB; zero-surprise staging→prod promotion.
**Out of scope (v0.1)** Multi-tenancy, message broker, frontend.
