#!/usr/bin/env bash
# Docker front-end: docker.sh <dev|staging|prod> <up|down|build|logs|ps|config> [args]
source "$(dirname "$0")/_lib.sh"
need docker
ENV_NAME="${1:-}"; ACTION="${2:-up}"; shift $(( $# > 1 ? 2 : $# )) || true
case "$ENV_NAME" in dev|staging|prod) ;; *) die "usage: docker.sh <dev|staging|prod> <up|down|build|logs|ps|config>";; esac
export DOCKER_BUILDKIT=1 COMPOSE_BAKE=true
C=(docker compose -p "rio-$ENV_NAME" -f compose.yaml -f "compose.$ENV_NAME.yaml")
case "$ACTION" in
  up)    exec "${C[@]}" up --build -d --wait "$@" ;;
  down)  exec "${C[@]}" down "$@" ;;
  build) exec "${C[@]}" build "$@" ;;
  logs)  exec "${C[@]}" logs -f "$@" ;;
  ps)    exec "${C[@]}" ps "$@" ;;
  config) exec "${C[@]}" config "$@" ;;
  *) die "unknown action $ACTION" ;;
esac
