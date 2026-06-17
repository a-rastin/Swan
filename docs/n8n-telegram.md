# n8n + Telegram (two-way)

Swan does NOT bundle n8n. You self-host it. Swan exposes an external API + an outbound webhook.

## Auth

External API uses header `X-API-Key: <key>`. Keys are created per user (table `api_keys`,
stored hashed). `EXTERNAL_API_MASTER_KEY` is a fallback admin key.

## Inbound — create a to-do from Telegram (Phase 5)

```
Telegram Bot (n8n trigger)
  → resolve user by telegram_chat_id
  → HTTP Request: POST https://<domain>/api/v1/external/tasks
       headers: X-API-Key: <key>
       body: { "chat_id": "<telegram_chat_id>", "title": "...", "due_at": null }
  → reply to user with confirmation
```

Swan resolves the Swan user from `telegram_links.telegram_chat_id`.

### First-time linking

1. User opens Swan → Settings → "Connect Telegram" → gets a one-time `link_code`.
2. User sends `/link <link_code>` to the bot.
3. n8n calls `POST /api/v1/external/telegram/link` with `{ chat_id, link_code }`.
4. Swan binds `chat_id` ↔ user.

## Outbound — reminders/digests to Telegram (Phase 3/5)

Celery Beat finds due reminders → `POST {N8N_WEBHOOK_URL}`:

```json
{ "chat_id": "123456", "text": "Reminder: Pay rent", "meta": { "task_id": "..." } }
```

n8n node sends the message to Telegram. Web Push fires in parallel from Swan directly.

## Endpoints (Phase 5)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/external/tasks` | create to-do |
| GET | `/api/v1/external/tasks?due=today` | list due tasks |
| PATCH | `/api/v1/external/tasks/{id}/complete` | mark done |
| POST | `/api/v1/external/telegram/link` | bind chat_id to user |
