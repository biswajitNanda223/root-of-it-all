# docker buildx bake [dev|staging|prod|test|release]   (see docs/deployment.md)
variable "VERSION"  { default = "0.0.0" }
variable "GIT_SHA"  { default = "unknown" }
variable "REGISTRY" { default = "ghcr.io/biswajitnanda223/root-of-it-all" }
variable "CACHE_REF" { default = "" }   # e.g. registry ref for cross-runner cache

group "default" { targets = ["staging"] }
group "release" { targets = ["staging", "prod"] }

target "_common" {
  context  = "."
  args     = { VERSION = VERSION, GIT_SHA = GIT_SHA }
  cache-from = CACHE_REF != "" ? ["type=registry,ref=${CACHE_REF}"] : ["type=gha"]
  cache-to   = CACHE_REF != "" ? ["type=registry,ref=${CACHE_REF},mode=max"] : ["type=gha,mode=max"]
}

target "dev"     { inherits = ["_common"]  target = "dev"     tags = ["rio-api:dev"]   args = { LLD_PROFILE = "dev" } }
target "test"    { inherits = ["_common"]  target = "test"    output = ["type=cacheonly"] args = { LLD_PROFILE = "dev" } }
target "staging" {
  inherits = ["_common"]
  target   = "staging"
  tags     = ["${REGISTRY}/api:staging", "${REGISTRY}/api:staging-${GIT_SHA}"]
  platforms = ["linux/amd64", "linux/arm64"]
  attest   = ["type=provenance,mode=max", "type=sbom"]
}
target "prod" {
  inherits = ["_common"]
  target   = "prod"
  tags     = ["${REGISTRY}/api:${VERSION}", "${REGISTRY}/api:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
  attest   = ["type=provenance,mode=max", "type=sbom"]
}
