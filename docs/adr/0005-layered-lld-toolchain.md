# ADR 0005 - Layered lld toolchain
Status: accepted
**Context** Native links are slow and flags drift between laptops, CI and Docker. **Decision** Compose flags from
`tooling/lld` in three layers (repo, profile, project) via one loader used by scripts, Docker and CI; pin `LDSHARED`;
verify with `lld-doctor.sh`. **Consequences** Identical flags everywhere, per-project control; uv's wheel cache ignores
flags, so profile switches need `scripts/native.sh`.
