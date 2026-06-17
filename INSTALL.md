# Installing Swan — Step by Step

This guide covers two paths:

- **[Path A — Local development](#path-a--local-development)** — run Swan on your own machine to try it or hack on it.
- **[Path B — Production deploy](#path-b--production-deploy)** — run Swan on a server with a real domain and HTTPS.

Pick the one that matches what you want. Most people running Swan "for real" want Path B.

---

## Before you start

You need **Docker** and the **Docker Compose plugin**. Check with:

```bash
docker --version
docker compose version
```

If both print a version, you're set. If not:

- **Linux:** `curl -fsSL https://get.docker.com | sh` (Path B's installer does this for you).
- **Mac / Windows:** install [Docker Desktop](https://www.docker.com/products/docker-desktop/), which includes Compose.

> Note: commands use `docker compose` (with a space), the v2 plugin syntax. The older
> `docker-compose` (with a hyphen) won't work with this project.

---

## Path A — Local development

Use this to run Swan on `localhost`. No domain or HTTPS involved.

### 1. Clone the repository

```bash
git clone https://github.com/a-rastin/Swan.git
cd Swan
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Open `.env` in an editor. For a quick local run you can leave most values as-is, but replace the
placeholder secrets so they aren't the literal word `change_me`:

```bash
JWT_SECRET=$(openssl rand -hex 32)
JWT_REFRESH_SECRET=$(openssl rand -hex 32)
```

(Run those two commands and paste the output into the matching lines, or just type any long random
strings.) The AI, Google Drive, and Telegram fields can stay empty — those features simply stay
off until you fill them in.

### 3. Build and start the stack

```bash
docker compose up --build
```

This starts Postgres, Redis, the FastAPI backend, the Celery worker and beat scheduler, and the
React dev server. The first build takes a few minutes; later starts are fast. Leave this terminal
running (or add `-d` to run it in the background).

### 4. Open the app

- **Frontend:** <http://localhost:5173>
- **API docs:** <http://localhost:8000/docs>

Register a user on the frontend and you're in. Database tables are created automatically on first
boot — there's no manual migration step for a fresh install.

### 5. Stopping

Press `Ctrl+C` in the terminal, or if you used `-d`:

```bash
docker compose down
```

Your data lives in Docker volumes, so it survives restarts. To wipe it completely, add `-v`:
`docker compose down -v`.

---

## Path B — Production deploy

This puts Swan on a public server with automatic HTTPS. The whole thing is essentially one command.

### What you need first

1. An **Ubuntu server** (22.04 recommended) with root/sudo access.
2. A **domain name** with a DNS **A record** pointing at the server's IP address
   (e.g. `swan.example.com → 203.0.113.10`). HTTPS won't work until DNS resolves.
3. SSH access to the server.

### 1. Point your domain at the server

In your DNS provider, create an A record for the (sub)domain you'll use, pointing to the server's
public IP. Give it a minute to propagate. You can check with `ping swan.example.com`.

### 2. SSH in and clone the repo

```bash
ssh youruser@your-server-ip
git clone https://github.com/a-rastin/Swan.git swan
cd swan
```

### 3. Run the installer

```bash
bash install.sh
```

This script does the heavy lifting:

- installs Docker if it isn't already present,
- creates `.env` from the template and **auto-generates every secret** (database password, JWT
  secrets, external API key, and VAPID web-push keys),
- builds the Docker images,
- starts the full production stack (with Caddy for TLS),
- and auto-creates the database tables on first boot.

> If Docker was just installed, you may need to log out and back in (or run `newgrp docker`) so
> your user can run Docker without `sudo`, then re-run `bash install.sh`.

### 4. Finish configuring `.env`

The installer leaves a few values for you to fill in. Open `.env`:

```bash
nano .env
```

At minimum, set:

| Variable | What to put | Required? |
|---|---|---|
| `DOMAIN` | Your domain, e.g. `swan.example.com` | **Yes** — needed for HTTPS |
| `GEMINI_API_KEY` | A key from [Google AI Studio](https://aistudio.google.com/app/apikey) | Only for the AI chatbox |
| `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` | From Google Cloud Console | Only for Drive attachments |
| `GOOGLE_DRIVE_REFRESH_TOKEN` / `GOOGLE_DRIVE_ROOT_FOLDER_ID` | From the Drive auth step below | Only for Drive attachments |
| `N8N_WEBHOOK_URL` | Your self-hosted n8n webhook URL | Only for Telegram reminders |

`DATABASE_URL`, `REDIS_URL`, and the auto-generated secrets should be left as the installer set them.

### 5. Apply the config and (re)start

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Caddy will request a TLS certificate for your domain on the first request, so the first load may
take a few extra seconds.

> Tip: this long command is wrapped as `make up`. You can also use `make down`, `make logs`,
> `make ps`, and `make backup`.

### 6. Open Swan and create the first user

Visit `https://<your-domain>` and register. That account is your owner account.

### 7. Verify it's healthy

```bash
curl https://<your-domain>/health        # → {"status":"ok"}
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

---

## Optional: enable Google Drive attachments

File attachments are stored in the **owner's personal Google Drive**. To turn this on:

1. In **Google Cloud Console**, create an OAuth 2.0 Client (type: *Web application*) and add
   yourself as a test user. Use the `drive.file` scope. Copy the client ID and secret into `.env`.
2. Mint a refresh token by running the helper script **once from a machine with a browser**:

   ```bash
   cd swan
   pip install google-auth-oauthlib
   python backend/scripts/drive_auth.py
   ```

   Follow the browser OAuth flow. The script prints `GOOGLE_DRIVE_REFRESH_TOKEN` and
   `GOOGLE_DRIVE_ROOT_FOLDER_ID` — paste both into `.env`.
3. Re-run `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` to apply.

---

## Optional: Telegram reminders via n8n

Swan talks to Telegram through a **self-hosted n8n** instance (not included in this stack):

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and get its token.
2. In n8n, add a **Telegram Trigger** node to receive messages.
3. Add an **HTTP Request** node that POSTs to
   `https://<your-domain>/api/external/telegram/link` with header
   `X-API-Key: <EXTERNAL_API_MASTER_KEY>`.
4. Set `N8N_WEBHOOK_URL` in `.env` so Swan can send outbound reminders.

Users link their account by generating a code in **Settings → Telegram** and sending `/link CODE`
to the bot. See `docs/DEPLOY.md` for the full workflow.

---

## Day-to-day operations

**Update to the latest version:**

```bash
cd swan
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**Back up the database:**

```bash
make backup        # writes backup_<timestamp>.sql
```

Or schedule a nightly dump with cron (`crontab -e`):

```
0 3 * * * cd /path/to/swan && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_dump -U swan swan > /backups/swan_$(date +\%Y\%m\%d).sql
```

**Reset a forgotten password** (no email reset is built in):

```bash
docker compose exec backend python scripts/reset_password.py user@example.com newpassword123
```

**Firewall** — only open what you need:

```bash
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable
```

Ports 5432 (Postgres), 6379 (Redis), and 8000 (backend) stay internal to the Docker network.

---

## Troubleshooting

- **HTTPS / certificate errors:** confirm your DNS A record points at the server and that ports
  80 and 443 are open. Caddy needs both to issue a certificate.
- **`docker compose` "command not found":** you have the old standalone tool. Install the Compose
  v2 plugin, or upgrade Docker.
- **Permission denied talking to Docker:** add your user to the docker group
  (`sudo usermod -aG docker $USER`) and start a new shell.
- **AI / Drive / Telegram features look disabled:** that's expected until the matching `.env`
  values are filled in. Set them, then re-run the `up -d` command.
- **Check what's wrong:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f`
  shows live logs for all services.
