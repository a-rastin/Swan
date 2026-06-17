"""X-API-Key authentication for the external (n8n) API."""
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import sha256
from app.db.session import get_session
from app.models import ApiKey, User


async def get_external_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Resolve request to a Swan user via API key or master key.

    Master key (EXTERNAL_API_MASTER_KEY) is only for initial setup / n8n testing.
    It requires a chat_id to resolve the target user per request.
    Per-user API keys own their user directly.
    """
    # Check per-user key first
    key_hash = sha256(x_api_key)
    row = await db.scalar(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked.is_(False))
    )
    if row:
        row.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        user = await db.get(User, row.owner_user_id)
        if user and user.is_active:
            return user

    # Fallback master key — returns None (caller must resolve user from chat_id)
    if x_api_key == settings.EXTERNAL_API_MASTER_KEY:
        return None  # type: ignore[return-value]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid API key",
        headers={"WWW-Authenticate": "X-API-Key"},
    )
