<div align="center">

# 🦢 Swan

**A self-hosted to-do list + calendar app — bilingual, AI-powered, and built to run in Docker.**

Lists, projects, recurring to-dos, habits, Pomodoro, file attachments, an AI chatbox, and
push/Telegram reminders — all in one place, in English or Persian, on Gregorian or Jalali calendars.

![License](https://img.shields.io/badge/license-MIT-green)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)
![Database](https://img.shields.io/badge/db-PostgreSQL-336791)
![Docker](https://img.shields.io/badge/runs%20in-Docker-2496ED)

</div>

---

## What is Swan?

Swan is a multi-user productivity app you host yourself. It combines a task manager and a
calendar with a few things you don't usually get in a self-hosted app: a built-in AI assistant
that can create tasks from text or voice, two-way Telegram reminders, and full support for both
English (LTR) and Persian (RTL) with Gregorian and Jalali calendars side by side.

Everything runs as a set of Docker containers behind an automatic-HTTPS reverse proxy, so a
single command on a fresh server gets you a working, TLS-secured instance.

## Features

- **Tasks & organization** — lists, projects, sub-tasks, labels, priorities, due dates, and recurring to-dos (RRULE-based).
- **Habits** — track recurring habits with custom schedules, targets, and history.
- **Pomodoro** — built-in focus timer with configurable work/break cycles, optionally tied to a task.
- **AI chatbox** — a Gemini-powered assistant (text *and* voice) that automatically turns what you say into tasks.
- **File attachments** — attach files to tasks via Google Drive (stored in the owner's personal Drive).
- **Reminders & notifications** — web push (PWA / VAPID) plus two-way Telegram via a self-hosted n8n workflow.
- **Bilingual & dual-calendar** — English / Persian, RTL / LTR, and Gregorian / Jalali, switchable per user.
- **PWA** — installable on desktop and mobile, works as a standalone app.
- **Multi-user** — public signup, JWT auth (access + refresh), Argon2 password hashing.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · async SQLAlchemy 2.0 · Alembic |
| Frontend | React · Vite · TypeScript · Tailwind (PWA) |
| Database | PostgreSQL |
| Cache / broker | Redis |
| Background jobs | Celery + Celery Beat |
| Reverse proxy | Caddy (automatic HTTPS via Let's Encrypt) |
| AI | Google Gemini (`gemini-2.0-flash`) |
| Storage | Google Drive (OAuth refresh token) |
| Messaging | Telegram via self-hosted n8n |

## Architecture

```
Browser / PWA → Caddy (TLS) → ┬─ frontend (nginx static)
                              └─ backend (FastAPI / gunicorn)
                                      │
        ┌─────────────────────────────┼──────────────────────────────┐
   PostgreSQL                        Redis                    External APIs
                                       │                 (Gemini, Google Drive)
                              Celery worker + beat
                          (reminders, recurring tasks,
                           digests, web push, n8n outbound)

n8n (self-hosted, external) ⇄ Telegram ⇄ Swan external API (X-API-Key)
```

Containers: `proxy` (Caddy) · `frontend` (nginx) · `backend` (gunicorn + uvicorn) ·
`worker` (Celery) · `beat` (Celery Beat) · `db` (Postgres) · `redis`.

## Project layout

```
backend/   FastAPI app, Celery workers, Alembic migrations, setup scripts
frontend/  React + Vite + Tailwind PWA
docs/      PLAN.md (full build plan), DEPLOY.md (deploy guide), API notes
install.sh One-command installer for a fresh Ubuntu server
Makefile   Shortcuts: make up / down / logs / backup / ps
```

## Quick start (development)

Requires Docker and the Docker Compose plugin.

```bash
git clone https://github.com/a-rastin/Swan.git
cd Swan
cp .env.example .env          # fill in your secrets
docker compose up --build
```

- Frontend: <http://localhost:5173>
- API: <http://localhost:8000/api/v1> — interactive docs at <http://localhost:8000/docs>

## Deploy to production (one command)

On a fresh Ubuntu server with a domain pointed at it:

```bash
git clone https://github.com/a-rastin/Swan.git swan && cd swan
bash install.sh
# then edit .env → set DOMAIN, GEMINI_API_KEY, and (optionally) Google Drive + n8n creds
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

`install.sh` installs Docker if needed, auto-generates every secret (database password, JWT
secrets, external API key, VAPID web-push keys), builds the images, and starts the full stack.
Database tables are created automatically on first boot, and Caddy issues a TLS certificate for
your domain on the first request. Then open `https://<your-domain>` and register the first user.

For a full walkthrough — including Google Drive setup, Telegram/n8n, backups, and admin tasks —
see **[INSTALL.md](INSTALL.md)** and **[docs/DEPLOY.md](docs/DEPLOY.md)**.

## Configuration

All configuration lives in `.env` (copy it from `.env.example`). Key variables:

| Variable | Purpose |
|---|---|
| `DOMAIN` | Your domain — Caddy issues TLS for it |
| `JWT_SECRET` / `JWT_REFRESH_SECRET` | Auth signing keys (auto-generated by `install.sh`) |
| `GEMINI_API_KEY` | Enables the AI chatbox (Google AI Studio) |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET` + `GOOGLE_DRIVE_REFRESH_TOKEN` + `GOOGLE_DRIVE_ROOT_FOLDER_ID` | Google Drive file attachments |
| `VAPID_PUBLIC` / `VAPID_PRIVATE` | Web-push reminders (auto-generated by `install.sh`) |
| `EXTERNAL_API_MASTER_KEY` | Auth for the external API used by n8n/Telegram |
| `N8N_WEBHOOK_URL` | Outbound Telegram reminders via n8n (optional) |

The AI, Google Drive, and Telegram features are optional — Swan runs fine without them; those
sections of the app simply stay inactive until you fill in the matching variables.

## Useful commands

```bash
make up        # build & start the production stack
make down      # stop the stack
make logs      # tail logs
make ps        # service status
make backup    # dump the database to backup_DATE.sql
```

## Documentation

- **[INSTALL.md](INSTALL.md)** — step-by-step installation guide (dev and production)
- **[docs/DEPLOY.md](docs/DEPLOY.md)** — detailed Ubuntu VPS deploy, admin, and backup guide
- **[docs/PLAN.md](docs/PLAN.md)** — full build plan, data model, and API surface

## License

Released under the [MIT License](LICENSE).
