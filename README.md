# Swan

To-do list + Calendar app. Bilingual (English / Persian) with RTL, dual calendars
(Gregorian + Jalali). FastAPI + React (PWA) + PostgreSQL. Runs in Docker.

See [docs/PLAN.md](docs/PLAN.md) for the full build plan.

## Features

Lists · Projects · To-dos (recurring) · Habits · Pomodoro · Google Drive file attachments ·
Gemini AI chatbox (text + voice, auto-creates tasks) · Web-push reminders ·
Two-way Telegram via self-hosted n8n · English/Persian + RTL + Jalali/Gregorian calendars.

## Quick start (dev)

```bash
cp .env.example .env        # fill secrets
docker compose up --build
docker compose exec backend alembic upgrade head
```

- Frontend (dev): http://localhost:5173
- API: http://localhost:8000/api/v1 — docs at http://localhost:8000/docs

## Deploy (prod) — one command

On a fresh Ubuntu server:

```bash
git clone https://github.com/<you>/swan.git && cd swan
bash install.sh
# edit .env → set DOMAIN + GEMINI_API_KEY + Google Drive creds, then:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

`install.sh` installs Docker, generates all secrets (DB / JWT / API key / VAPID), builds,
and starts the stack. DB tables auto-create on first boot; Caddy auto-issues TLS for `$DOMAIN`.
Full guide: [docs/DEPLOY.md](docs/DEPLOY.md).

## Layout

```
backend/   FastAPI app, Celery workers, Alembic migrations, setup scripts
frontend/  React + Vite + Tailwind PWA
docs/      PLAN.md, API.md, deploy notes
```
