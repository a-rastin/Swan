# Swan — Build Plan

To-do list + Calendar app. Multi-user, bilingual (English/Persian) with RTL, dual calendars
(Gregorian + Jalali). Runs in Docker on an Ubuntu VPS.

## Locked decisions

| Area | Choice |
|---|---|
| Backend | Python + FastAPI (async SQLAlchemy 2.0, Alembic) |
| Frontend | React + Vite + TypeScript, responsive PWA |
| Database | PostgreSQL |
| Cache / broker | Redis |
| Jobs / scheduler | Celery + Celery Beat |
| Users | Multi-user, public signup |
| Auth | Email + password, JWT (access + refresh). **No email verification, no email reset** (no SMTP). |
| Gemini | Shared `gemini-2.0-flash` key, server-side only. AI **auto-creates** tasks. |
| Google Drive | **Single OAuth2 refresh token for the owner's personal Drive** (no service account, no Workspace). Files in owner's Drive under `Swan/<user>/`. Quota = owner's 15 GB. |
| Telegram / n8n | Two-way. Swan exposes `X-API-Key` external API (inbound) + posts to `N8N_WEBHOOK_URL` (outbound). **n8n is self-hosted by the user — not in this compose.** |
| Notifications | Web Push (PWA, VAPID) + Telegram via n8n |
| Voice | Gemini multimodal (audio sent directly) |
| Reverse proxy | Caddy (auto-HTTPS, Let's Encrypt). Domain + DNS available. |
| UI | Minimal. Tailwind, plain components, light theme, RTL/LTR + Vazirmatn/Inter. No design system. |

## Key constraints / flags

- **Drive storage = owner's personal account quota**, shared by all users. Small-scale only. Bump via Google One.
- **OAuth consent screen stays in "testing"** → add owner as test user; refresh token long-lived.
- **No password recovery via email.** Logged-in change-password only. Forgotten password with no session = admin CLI (`scripts/reset_password.py`).
- All datetimes stored UTC `timestamptz`. Calendar type is display-only (frontend converts).

## Architecture

```
Browser/PWA → Caddy (TLS) → { frontend static (nginx), backend FastAPI }
backend → PostgreSQL, Redis, Gemini API, Google Drive API (OAuth refresh token)
Celery worker + beat → reminders, recurring tasks, digests, web-push, n8n outbound
n8n (self-hosted, external) ⇄ Telegram, calls Swan external API (X-API-Key)
```

Containers: `proxy` (Caddy), `frontend` (nginx static), `backend` (gunicorn+uvicorn),
`worker` (celery), `beat` (celery beat), `db` (postgres), `redis`.

## Data model (PostgreSQL)

- **users**: id, email(unique), password_hash(argon2), name, locale(en/fa),
  calendar_pref(gregorian/jalali), timezone, created_at
- **refresh_tokens**: id, user_id, token_hash, expires_at, revoked
- **lists**: id, user_id, name, color, icon, position, archived
- **projects**: id, user_id, name, description, color, status, start_date, due_date, position
- **tasks**: id, user_id, list_id?, project_id?, parent_task_id?, title, notes, status,
  priority, due_at?, remind_at?, recurrence_rrule?, position, completed_at, source(ui/ai/telegram)
- **labels** + **task_labels** (m2m)
- **habits**: id, user_id, name, color, schedule, target_per_period, unit, archived
- **habit_logs**: id, habit_id, log_date, value, completed
- **pomodoro_settings**: user_id, work_min, short_break, long_break, cycles_before_long, auto_start
- **pomodoro_sessions**: id, user_id, task_id?, type(work/break), started_at, ended_at, completed
- **files**: id, user_id, drive_file_id, name, mime, size, web_view_link, attached_type, attached_id
- **ai_conversations** + **ai_messages**: role, content, audio_ref?, resulting_task_ids[]
- **push_subscriptions**: id, user_id, endpoint, p256dh, auth, device_label
- **api_keys**: id, owner_user_id, name, key_hash, scopes, last_used_at, revoked
- **telegram_links**: user_id, telegram_chat_id, linked_at
- **notifications**: id, user_id, type, payload, read_at, created_at

## API surface

**v1 (JWT):** auth (register/login/refresh/logout/me, change-password), users/settings,
lists, projects, tasks (+subtasks, recurrence, complete, reorder), habits (+log, stats),
pomodoro (sessions, stats), files (Drive upload/list/delete), ai (chat text, voice),
push (subscribe), notifications, calendar (events from-to).

**external (`X-API-Key`, for n8n):** `POST /external/tasks`, `GET /external/tasks?due=today`,
`PATCH /external/tasks/{id}/complete`, `POST /external/telegram/link`.

## Background jobs (Celery Beat)

- every minute: dispatch due reminders → web push + n8n outbound
- midnight per-tz: spawn next recurring task instances; reset daily habit state
- morning: daily digest → push/Telegram
- hourly: token cleanup, Drive orphan sweep

## Google Drive setup (OAuth refresh token)

1. Google Cloud Console → OAuth client (Web application). Add owner as test user.
2. Scope `drive.file`. Redirect = `GOOGLE_OAUTH_REDIRECT`.
3. Run `backend/scripts/drive_auth.py` once → mint `GOOGLE_DRIVE_REFRESH_TOKEN`.
4. Create `Swan/` folder in Drive → put id in `GOOGLE_DRIVE_ROOT_FOLDER_ID`.
5. App auto-refreshes access token; uploads into per-user subfolders.

## Env vars

```
DATABASE_URL=
REDIS_URL=
JWT_SECRET=  JWT_REFRESH_SECRET=
GEMINI_API_KEY=
GOOGLE_OAUTH_CLIENT_ID=  GOOGLE_OAUTH_CLIENT_SECRET=  GOOGLE_OAUTH_REDIRECT=
GOOGLE_DRIVE_REFRESH_TOKEN=  GOOGLE_DRIVE_ROOT_FOLDER_ID=
VAPID_PUBLIC=  VAPID_PRIVATE=  VAPID_SUBJECT=
EXTERNAL_API_MASTER_KEY=
N8N_WEBHOOK_URL=
DOMAIN=  TZ=
```

## Security

HTTPS (Caddy) · argon2 passwords · short access JWT + rotating refresh (httpOnly cookie) ·
CORS locked to domain · rate limits on auth + external API · API keys hashed + scoped ·
Pydantic validation · upload size/type limits · Gemini/Drive keys server-side only ·
`/docs` gated in prod · encrypted nightly `pg_dump` backups · Drive scope `drive.file`.

## Roadmap

| Phase | Scope |
|---|---|
| 0 — Scaffold | monorepo, docker-compose, Postgres, Alembic, base FastAPI + React + i18n/RTL/calendar toggle |
| 1 — Core | auth (register/login/change-password), dashboard, lists, to-dos (+recurrence) |
| 2 — Productivity | projects, habits, pomodoro |
| 3 — Files + Notify | Drive OAuth uploads, web push, reminders (Celery) |
| 4 — AI | Gemini chatbox text + voice → auto-create tasks |
| 5 — Integrations | external API + API keys, n8n two-way, Telegram link |
| 6 — Harden + Ship | tests, security pass, prod deploy, backups, docs |

Testing: pytest (backend), Vitest + RTL (frontend), Playwright e2e (auth/task/AI).

## VPS deploy (Ubuntu)

1. Install Docker + Compose plugin.
2. `ufw` allow 22/80/443.
3. DNS A-record → VPS; set `DOMAIN` in `.env` + Caddyfile.
4. Clone repo, fill `.env`, mint Drive refresh token.
5. `docker compose -f docker-compose.prod.yml up -d`
6. `docker compose exec backend alembic upgrade head`
7. nightly `pg_dump` cron → encrypted off-site.
