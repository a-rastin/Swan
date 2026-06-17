"""Telegram linking — user-facing: generate link code + check status."""
import secrets
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import TelegramLink, User

router = APIRouter()

_CODE_CHARS = string.ascii_uppercase + string.digits
_CODE_LEN = 8


def _gen_code() -> str:
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(_CODE_LEN))


class TelegramStatusOut(BaseModel):
    linked: bool
    telegram_chat_id: str | None
    pending_code: str | None


@router.get("/status", response_model=TelegramStatusOut)
async def tg_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    row = await db.scalar(select(TelegramLink).where(TelegramLink.user_id == user.id))
    if row is None:
        return TelegramStatusOut(linked=False, telegram_chat_id=None, pending_code=None)
    return TelegramStatusOut(
        linked=row.telegram_chat_id is not None and row.linked_at is not None,
        telegram_chat_id=row.telegram_chat_id,
        pending_code=row.link_code,
    )


@router.post("/code", response_model=TelegramStatusOut)
async def gen_code(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Generate (or refresh) a one-time link code. User sends this to the Telegram bot."""
    row = await db.scalar(select(TelegramLink).where(TelegramLink.user_id == user.id))
    code = _gen_code()
    if row:
        row.link_code = code
    else:
        row = TelegramLink(user_id=user.id, link_code=code)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return TelegramStatusOut(
        linked=row.telegram_chat_id is not None and row.linked_at is not None,
        telegram_chat_id=row.telegram_chat_id,
        pending_code=row.link_code,
    )


@router.delete("/unlink", status_code=204)
async def unlink(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    row = await db.scalar(select(TelegramLink).where(TelegramLink.user_id == user.id))
    if row:
        await db.delete(row)
        await db.commit()
