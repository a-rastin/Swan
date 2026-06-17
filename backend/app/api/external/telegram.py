"""Telegram link endpoint — called by n8n when user sends /link <code> to the bot."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.external.deps import get_external_user
from app.core.rate_limit import limiter
from app.db.session import get_session
from app.models import TelegramLink, User

router = APIRouter()


class TelegramLinkIn(BaseModel):
    chat_id: str
    link_code: str


@router.post("/telegram/link")
@limiter.limit("30/minute")
async def link_telegram(
    request: Request,
    body: TelegramLinkIn,
    _api_user: User | None = Depends(get_external_user),
    db: AsyncSession = Depends(get_session),
):
    row = await db.scalar(
        select(TelegramLink).where(TelegramLink.link_code == body.link_code.strip().upper())
    )
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "invalid or expired link code")

    # Check code not already used
    if row.linked_at and not row.link_code:
        raise HTTPException(status.HTTP_409_CONFLICT, "already linked")

    row.telegram_chat_id = body.chat_id
    row.linked_at = datetime.now(timezone.utc)
    row.link_code = None
    await db.commit()
    return {"ok": True, "linked": True}
