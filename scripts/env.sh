#!/usr/bin/env bash
# dotenvx front-end for encrypted env files.
#   env.sh init <staging|production|ci>     create + encrypt .env.<env> with generated secrets
#   env.sh set <env> KEY [VALUE]            set/replace a value (encrypted)      (no VALUE -> prompt via stdin)
#   env.sh get <env> [KEY]                  print decrypted value(s)
#   env.sh decrypt <env>                    print the decrypted file to stdout (never writes plaintext to disk)
#   env.sh encrypt <env>                    (re)encrypt any plaintext values added by hand
#   env.sh key-name <env>                   the variable that holds the private key (store it in your secret manager)
#   env.sh check                            fail if a tracked env file is not encrypted / a key file is tracked
#   env.sh run <env> -- <cmd...>            run a command with that env decrypted
source "$(dirname "$0")/_lib.sh"
usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }
ACTION="${1:-}"; [[ -n "$ACTION" ]] || usage 1; shift || true
ENVNAME="${1:-}"
file() { echo ".env.$1"; }
valid_env() { case "$1" in staging|production|ci) ;; *) die "env must be staging|production|ci (development is plaintext by design)";; esac; }
base=(--no-native --no-armor)

case "$ACTION" in
  init)
    valid_env "$ENVNAME"; f="$(file "$ENVNAME")"; need openssl; dx_bin
    [[ ! -e "$f" ]] || die "$f exists - use 'set' to change values"
    {
      echo "RIO_ENVIRONMENT=$([[ $ENVNAME == production ]] && echo production || echo staging)"
      echo "RIO_SECRET_KEY=$(openssl rand -hex 32)"
      echo "RIO_SERVICE_KEY=$(openssl rand -hex 32)"
      echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)"
      echo "RIO_PLAYGROUND_ENABLED=$([[ $ENVNAME == production ]] && echo false || echo true)"
      echo "RIO_LOG_JSON=true"
      echo "RIO_ALLOWED_HOSTS=[\"*\"]"
    } > "$f"
    "${DXBIN[@]}" encrypt -f "$f" "${base[@]}" >/dev/null
    log "created and encrypted $f  (commit it)"
    log "private key is in .env.keys (git-ignored). Store DOTENV_PRIVATE_KEY_$(echo "$ENVNAME" | tr a-z A-Z) in your secret manager/CI, then back it up."
    ;;
  set)
    valid_env "$ENVNAME"; key="${2:?KEY required}"; dx_bin
    if [[ $# -ge 3 ]]; then val="$3"; else read -rsp "value for $key: " val; echo; fi
    "${DXBIN[@]}" set "$key" "$val" -f "$(file "$ENVNAME")" "${base[@]}" >/dev/null
    log "set $key in $(file "$ENVNAME") (encrypted)" ;;
  get)     valid_env "$ENVNAME"; dx_bin; "${DXBIN[@]}" get ${2:+"$2"} -f "$(file "$ENVNAME")" "${base[@]}" ;;
  decrypt) valid_env "$ENVNAME"; dx_bin; "${DXBIN[@]}" decrypt -f "$(file "$ENVNAME")" --stdout "${base[@]}" ;;
  encrypt) valid_env "$ENVNAME"; dx_bin; "${DXBIN[@]}" encrypt -f "$(file "$ENVNAME")" "${base[@]}" >/dev/null && log "encrypted $(file "$ENVNAME")" ;;
  key-name) valid_env "$ENVNAME"; echo "DOTENV_PRIVATE_KEY_$(echo "$ENVNAME" | tr a-z A-Z)" ;;
  check)
    # tracked + untracked-but-not-ignored (what would be committed); ignored files (.env.keys/.env.local) are fine on disk
    mapfile -t candidates < <(git ls-files --cached --others --exclude-standard -- '.env*' | sort -u)
    [[ ${#candidates[@]} -gt 0 ]] || { log "no committable env files"; exit 0; }
    exec python3 scripts/hooks/check_dotenvx.py "${candidates[@]}" ;;
  run)
    valid_env "$ENVNAME"; shift; [[ "${1:-}" == "--" ]] && shift
    dx_prefix "$ENVNAME"; exec "${DX[@]}" "$@" ;;
  *) usage 1 ;;
esac
