# Configuration & secrets (dotenvx)

[dotenvx](https://dotenvx.com) encrypts values *inside* the `.env` file (ECIES: public key in the file, private key
elsewhere), so encrypted env files are safe to commit and diff, and secrets travel with the code they configure.

## Files
| File | Committed? | Content |
|---|---|---|
| `.env.example` | yes | reference of every variable (not loaded) |
| `.env.development` | yes, **plaintext** | non-secret dev defaults (`scripts/dev.sh` loads it) |
| `.env.staging`, `.env.production`, `.env.ci` | yes, **encrypted** | real values; every value is `encrypted:...` |
| `.env.local` | **never** | personal overrides, highest priority |
| `.env.keys` | **never** | private keys `DOTENV_PRIVATE_KEY_<ENV>` (gitignored, excluded from Docker context) |

**Precedence** (highest first): variables already in the process environment (CI, orchestrator) > `.env.local` >
`.env.<environment>` > pydantic defaults. dotenvx never overwrites an exported variable, so any value can be overridden
at deploy time without touching files.

## Workflow
```bash
scripts/env.sh init staging                 # generates RIO_SECRET_KEY + RIO_SERVICE_KEY + POSTGRES_PASSWORD, encrypts, writes .env.keys
git add .env.staging && git commit -m "chore(env): add encrypted staging config"
scripts/env.sh set staging RIO_DATABASE_URL 'postgresql+asyncpg://...'   # value is encrypted on write
scripts/env.sh get staging RIO_LOG_LEVEL    # decrypt one value
scripts/env.sh decrypt staging              # whole file to stdout (never to disk)
scripts/env.sh run staging -- scripts/migrate.sh
scripts/env.sh check                        # hygiene gate (also a pre-commit hook and a CI step)
```
Every run script picks the right file via `APP_ENV` (`dev.sh` -> development, `start.sh` -> production,
`docker.sh staging|prod` -> staging|production; override with `APP_ENV=staging scripts/start.sh`).

## Keys
* `scripts/env.sh key-name <env>` prints the variable to store: `DOTENV_PRIVATE_KEY_STAGING` / `_PRODUCTION`.
* **Back the private key up in your secret manager** - without it the encrypted file cannot be read. Losing it means
  re-running `init` and re-entering the secrets.
* CI: add the key as a repository/environment secret and expose it only to the deploy job:
  ```yaml
  - run: scripts/docker.sh staging up
    env: { DOTENV_PRIVATE_KEY_STAGING: "${{ secrets.DOTENV_PRIVATE_KEY_STAGING }}" }
  ```
* Rotating: `scripts/env.sh init` a fresh file (or `dotenvx rotate`), update the secret, redeploy.

## Why the container does not contain dotenvx
Decryption happens on the *host/CI runner* (`dotenvx run -- docker compose ...`), and compose passes plain variables to
the container. The image stays light (no Node/binary), holds no encrypted file and no private key. Orchestrators that
don't use compose should inject the same variables from their secret store; if you ever want in-container decryption,
add the single-binary dotenvx and pass `DOTENV_PRIVATE_KEY_PRODUCTION` as a runtime secret.

## Guard rails
* `scripts/hooks/check_dotenvx.py` (pre-commit + CI `commits` job) fails if `.env.keys`/`.env.local`/`.env` is staged,
  an unknown `.env.*` appears, or any value in `.env.staging|production|ci` is not `encrypted:`.
* `Settings` refuses to start in staging/production with the default secret, with `debug=true`, or (production) with the
  playground enabled.
* `.dockerignore` is an allow-list, so no env file can enter the build context.

Tool pin: `@dotenvx/dotenvx@2.37.0` (mise `npm:` tool; scripts fall back to `npx` with the same version).
