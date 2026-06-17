#!/usr/bin/env bash
#
# Swan one-command installer for a fresh Ubuntu server.
#   1. Installs Docker (if missing)
#   2. Creates .env from template + auto-generates all secrets
#   3. Generates VAPID web-push keys
#   4. Builds and starts the full stack (auto-creates DB tables)
#
# Usage:  ./install.sh
#
set -euo pipefail

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

rand() { openssl rand -hex "${1:-32}"; }

set_env() {  # set_env KEY VALUE  (replaces or appends in .env)
  local key="$1" val="$2"
  if grep -q "^${key}=" .env; then
    # use | as sed delimiter; escape | and & in value
    local esc; esc=$(printf '%s' "$val" | sed -e 's/[|&\\]/\\&/g')
    sed -i "s|^${key}=.*|${key}=${esc}|" .env
  else
    printf '%s=%s\n' "$key" "$val" >> .env
  fi
}

echo "==> [1/4] Docker"
if ! command -v docker >/dev/null 2>&1; then
  echo "    installing Docker..."
  curl -fsSL https://get.docker.com | sh
fi

echo "==> [2/4] .env + secrets"
[ -f .env ] || cp .env.example .env

# Generate secrets only if still at placeholder defaults.
if grep -q '^POSTGRES_PASSWORD=change_me$' .env; then
  DB_PASS="$(rand 16)"
  set_env POSTGRES_PASSWORD "$DB_PASS"
  set_env DATABASE_URL "postgresql+asyncpg://swan:${DB_PASS}@db:5432/swan"
fi
grep -q '^JWT_SECRET=change_me_access$'           .env && set_env JWT_SECRET "$(rand 32)"
grep -q '^JWT_REFRESH_SECRET=change_me_refresh$'  .env && set_env JWT_REFRESH_SECRET "$(rand 32)"
grep -q '^EXTERNAL_API_MASTER_KEY=change_me_external$' .env && set_env EXTERNAL_API_MASTER_KEY "$(rand 24)"
set_env ENV production

echo "==> [3/4] Build images + VAPID keys"
$COMPOSE build backend >/dev/null

if grep -q '^VAPID_PUBLIC=$' .env; then
  VAPID_OUT="$($COMPOSE run --rm --no-deps backend python scripts/gen_vapid.py)"
  set_env VAPID_PUBLIC  "$(printf '%s\n' "$VAPID_OUT" | sed -n 's/^VAPID_PUBLIC=//p')"
  set_env VAPID_PRIVATE "$(printf '%s\n' "$VAPID_OUT" | sed -n 's/^VAPID_PRIVATE=//p')"
fi

echo "==> [4/4] Starting stack"
$COMPOSE up -d --build

cat <<'EOF'

✅ Swan is up. Tables auto-created on first boot.

Still required in .env (then run:  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d):
  DOMAIN                       your domain (TLS auto-issued by Caddy)
  GEMINI_API_KEY               AI chat
  GOOGLE_OAUTH_CLIENT_ID/SECRET + GOOGLE_DRIVE_REFRESH_TOKEN + GOOGLE_DRIVE_ROOT_FOLDER_ID   file uploads
  N8N_WEBHOOK_URL              Telegram reminders (optional)

Create first user:  open https://<DOMAIN> and register.
Logs:               docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
EOF
