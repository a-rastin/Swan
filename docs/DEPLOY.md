# Swan — Ubuntu VPS Deploy Guide

## Quickstart (one command)

On a fresh Ubuntu server, after pushing this repo to GitHub:

```bash
git clone https://github.com/<you>/swan.git && cd swan
bash install.sh
# edit .env → set DOMAIN + GEMINI_API_KEY + Google Drive creds
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

`install.sh` installs Docker if missing, generates every secret (DB password, JWT, API
master key, VAPID web-push keys), builds images, and starts the stack. DB tables are
auto-created on first boot — no manual migration step. Caddy auto-issues TLS for `$DOMAIN`.

Open `https://<DOMAIN>` and register the first user. Done.

The manual walkthrough below explains each piece if you want more control.

---

## Prerequisites

- Ubuntu 22.04 VPS with root/sudo access
- A domain pointed at the server (A record)
- Docker + Docker Compose v2 installed

```bash
# Install Docker on Ubuntu 22.04
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## 1. Clone & configure

```bash
git clone <your-repo> /opt/swan
cd /opt/swan
cp .env.example .env
```

Edit `.env` and fill in every value:

| Variable | How to get it |
|---|---|
| `DATABASE_URL` | Keep default — points to the compose postgres service |
| `REDIS_URL` | Keep default — points to the compose redis service |
| `JWT_SECRET` | `openssl rand -hex 32` |
| `JWT_REFRESH_SECRET` | `openssl rand -hex 32` |
| `GEMINI_API_KEY` | Google AI Studio |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET` | Google Cloud Console → OAuth 2.0 credentials |
| `GOOGLE_DRIVE_REFRESH_TOKEN` | Run `python backend/scripts/drive_auth.py` locally first |
| `GOOGLE_DRIVE_ROOT_FOLDER_ID` | The Drive folder ID shown by drive_auth.py |
| `VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY` | `python backend/scripts/gen_vapid.py` |
| `VAPID_SUBJECT` | `mailto:admin@yourdomain.com` |
| `EXTERNAL_API_MASTER_KEY` | `openssl rand -hex 24` |
| `N8N_WEBHOOK_URL` | Your self-hosted n8n webhook URL |
| `DOMAIN` | Your domain e.g. `swan.example.com` |

---

## 2. Get the Google Drive refresh token

Run this **once** from your local machine (needs browser):

```bash
cd /opt/swan
pip install google-auth-oauthlib
python backend/scripts/drive_auth.py
```

Follow the browser OAuth flow. The script prints `GOOGLE_DRIVE_REFRESH_TOKEN` and `GOOGLE_DRIVE_ROOT_FOLDER_ID` — paste them into `.env`.

---

## 3. Build & start (production)

```bash
cd /opt/swan
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

This starts: `db`, `redis`, `backend` (gunicorn), `worker` (celery), `beat` (celery-beat), `frontend` (nginx), `proxy` (Caddy).

Caddy auto-obtains TLS for `$DOMAIN` on first request.

---

## 4. Database tables

Tables are created automatically on backend startup (`scripts/start.sh` → `app.db.init_db`).
No manual step needed for a fresh install.

For schema changes later (Alembic), once migrations exist:

```bash
docker compose exec backend alembic upgrade head
```

---

## 5. Verify

```bash
# Health check
curl https://swan.example.com/health
# → {"status":"ok"}

# Logs
docker compose logs -f backend
docker compose logs -f worker
```

---

## 6. Updates

```bash
cd /opt/swan
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose exec backend alembic upgrade head
```

---

## 7. Admin operations

### Reset a forgotten password

```bash
docker compose exec backend python scripts/reset_password.py user@example.com newpassword123
```

### Revoke all refresh tokens (security incident)

```sql
docker compose exec db psql -U swan -d swan -c "UPDATE refresh_tokens SET revoked=true;"
```

---

## 8. Backups

```bash
# Dump postgres
docker compose exec db pg_dump -U swan swan > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260101.sql | docker compose exec -T db psql -U swan -d swan
```

Schedule with cron (`crontab -e`):

```
0 3 * * * cd /opt/swan && docker compose exec -T db pg_dump -U swan swan > /backups/swan_$(date +\%Y\%m\%d).sql
```

---

## 9. n8n Telegram integration

See `docs/n8n-telegram.md` for full setup. Summary:

1. Create Telegram bot via @BotFather → get token
2. In n8n: Telegram Trigger node → receives messages
3. HTTP Request node: `POST https://$DOMAIN/api/external/telegram/link` with header `X-API-Key: $EXTERNAL_API_MASTER_KEY` and body `{"chat_id": "...", "link_code": "..."}`
4. Users generate link codes in Swan Settings → Telegram section → send `/link CODE` to the bot

Outbound reminders: Swan POSTs to `N8N_WEBHOOK_URL` with `{"chat_id": "...", "text": "..."}` — forward to Telegram Send Message node in n8n.

---

## 10. Firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

All other ports (5432, 6379, 8000) are internal to Docker network — not exposed to host.
