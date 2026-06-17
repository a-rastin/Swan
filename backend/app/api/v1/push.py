from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import PushSubscription, User

router = APIRouter()

class SubscribeBody(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_label: str | None = None


@router.post("/subscribe", status_code=201)
async def subscribe(
    body: SubscribeBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    existing = await db.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
    else:
        db.add(PushSubscription(
            user_id=user.id,
            endpoint=body.endpoint,
            p256dh=body.p256dh,
            auth=body.auth,
            device_label=body.device_label,
        ))
    await db.commit()
    return {"vapid_public": settings.VAPID_PUBLIC}


@router.delete("/subscribe", status_code=204)
async def unsubscribe(
    endpoint: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    sub = await db.scalar(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user.id,
        )
    )
    if sub:
        await db.delete(sub)
        await db.commit()
