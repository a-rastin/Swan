"""Outbound to Telegram via self-hosted n8n webhook. Phase 5."""
import httpx

from app.core.config import settings


async def notify_n8n(chat_id: str, text: str, meta: dict | None = None) -> bool:
    if not settings.N8N_WEBHOOK_URL:
        return False
    payload = {"chat_id": chat_id, "text": text, "meta": meta or {}}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(settings.N8N_WEBHOOK_URL, json=payload)
        return r.status_code < 300
