#!/usr/bin/env bash
# Docker front-end: docker.sh <dev|staging|prod> <up|down|build|logs|ps|config|size> [compose args / service names]
# e.g. docker.sh dev up catalog orders   (compose starts their dependencies automatically)
source "$(dirname "$0")/_lib.sh"
need docker
ENV_NAME="${1:-}"; ACTION="${2:-up}"; shift $(( $# > 1 ? 2 : $# )) || true
case "$ENV_NAME" in dev|staging|prod) ;; *) die "usage: docker.sh <dev|staging|prod> <up|down|build|logs|ps|config>";; esac
case "$ENV_NAME" in dev) dx_prefix development;; staging) dx_prefix staging;; prod) dx_prefix production;; esac
case "$ENV_NAME" in dev) export RIO_TARGET=dev;; staging) export RIO_TARGET=staging;; prod) export RIO_TARGET=prod;; esac
export DOCKER_BUILDKIT=1 COMPOSE_BAKE=true
C=(docker compose -p "rio-$ENV_NAME" -f compose.yaml -f "compose.$ENV_NAME.yaml")
case "$ACTION" in
  up)    exec "${DX[@]}" "${C[@]}" up --build -d --wait "$@" ;;
  down)  exec "${DX[@]}" "${C[@]}" down "$@" ;;
  build) exec "${DX[@]}" "${C[@]}" build "$@" ;;
  logs)  exec "${DX[@]}" "${C[@]}" logs -f "$@" ;;
  ps)    exec "${DX[@]}" "${C[@]}" ps "$@" ;;
  config) exec "${DX[@]}" "${C[@]}" config "$@" ;;
  size)  docker image ls --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E '^rio' || true ;;
  *) die "unknown action $ACTION" ;;
esac
