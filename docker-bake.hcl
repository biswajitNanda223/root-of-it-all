# docker buildx bake <group|target>      groups: dev  test  staging  prod  release
# One target per service per environment, generated from the SERVICES map in docker-bake.services.hcl
# (itself generated from apps/*/pyproject.toml - run scripts/generate.sh after adding a service).
variable "VERSION"   { default = "0.0.0" }
variable "GIT_SHA"   { default = "unknown" }
variable "REGISTRY"  { default = "ghcr.io/biswajitnanda223/root-of-it-all" }
variable "CACHE_REF" { default = "" }   # e.g. a registry ref for cross-runner cache; empty -> GitHub Actions cache

group "default" { targets = ["staging"] }
group "dev"     { targets = [for s, _ in SERVICES : "dev-${s}"] }
group "staging" { targets = [for s, _ in SERVICES : "staging-${s}"] }
group "prod"    { targets = [for s, _ in SERVICES : "prod-${s}"] }
group "release" { targets = ["staging", "prod"] }
group "test"    { targets = ["gate"] }

target "_common" {
  context    = "."
  cache-from = CACHE_REF != "" ? ["type=registry,ref=${CACHE_REF}"] : ["type=gha"]
  cache-to   = CACHE_REF != "" ? ["type=registry,ref=${CACHE_REF},mode=max"] : ["type=gha,mode=max"]
}

# Lint + types + ALL tests inside the image (workspace-wide, so it is not per service).
target "gate" {
  inherits = ["_common"]
  target   = "test"
  output   = ["type=cacheonly"]
  args     = { LLD_PROFILE = "dev" }
}

target "dev" {
  inherits = ["_common"]
  name     = "dev-${svc}"
  matrix   = { svc = keys(SERVICES) }
  target   = "dev"
  tags     = ["rio-${svc}:dev"]
  args     = { SERVICE = svc, SERVICE_MODULE = SERVICES[svc].module, SERVICE_PORT = SERVICES[svc].port, LLD_PROFILE = "dev" }
}

target "staging" {
  inherits  = ["_common"]
  name      = "staging-${svc}"
  matrix    = { svc = keys(SERVICES) }
  target    = "staging"
  tags      = ["${REGISTRY}/${svc}:staging", "${REGISTRY}/${svc}:staging-${GIT_SHA}"]
  platforms = ["linux/amd64", "linux/arm64"]
  attest    = ["type=provenance,mode=max", "type=sbom"]
  args      = { SERVICE = svc, SERVICE_MODULE = SERVICES[svc].module, SERVICE_PORT = SERVICES[svc].port, VERSION = VERSION, GIT_SHA = GIT_SHA }
}

target "prod" {
  inherits  = ["_common"]
  name      = "prod-${svc}"
  matrix    = { svc = keys(SERVICES) }
  target    = "prod"
  tags      = ["${REGISTRY}/${svc}:${VERSION}", "${REGISTRY}/${svc}:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
  attest    = ["type=provenance,mode=max", "type=sbom"]
  args      = { SERVICE = svc, SERVICE_MODULE = SERVICES[svc].module, SERVICE_PORT = SERVICES[svc].port, VERSION = VERSION, GIT_SHA = GIT_SHA }
}
