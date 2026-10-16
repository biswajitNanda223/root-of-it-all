# ADR 0008 - dotenvx for configuration and secrets
Status: accepted
**Context** Plain `.env` files cannot be committed; copying secrets by hand drifts between environments.
**Decision** Commit per-environment env files with encrypted values (dotenvx), keep private keys out of git and
images, decrypt on the host via `dotenvx run` (scripts, compose), enforce with a hook and CI. Already-exported
variables always win. **Consequences** Secrets are versioned and reviewable; losing a private key loses the file's
contents (back it up); one extra tool (pinned via mise/npx) on developer and CI machines, none in the image.
