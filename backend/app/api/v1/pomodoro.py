from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import PomodoroSession, PomodoroSettings, User
from app.schemas import (
    PomodoroSessionIn,
    PomodoroSessionOut,
    PomodoroSettingsIn,
    PomodoroSettingsOut,
    PomodoroStatsOut,
)

router = APIRouter()


@router.get("/settings", response_model=PomodoroSettingsOut)
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(PomodoroSettings, user.id)
    if obj is None:
        obj = PomodoroSettings(user_id=user.id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
    return obj


@router.patch("/settings", response_model=PomodoroSettingsOut)
async def update_settings(
    body: PomodoroSettingsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(PomodoroSettings, user.id)
    if obj is None:
        obj = PomodoroSettings(user_id=user.id)
        db.add(obj)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.post("/sessions", response_model=PomodoroSessionOut, status_code=201)
async def log_session(
    body: PomodoroSessionIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = PomodoroSession(user_id=user.id, **body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/stats", response_model=PomodoroStatsOut)
async def stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())

    def _minutes_q(since: datetime):
        return (
            select(func.sum(
                func.extract("epoch", PomodoroSession.ended_at - PomodoroSession.started_at) / 60
            ))
            .where(
                PomodoroSession.user_id == user.id,
                PomodoroSession.type == "work",
                PomodoroSession.completed.is_(True),
                PomodoroSession.started_at >= since,
                PomodoroSession.ended_at.isnot(None),
            )
        )

    today_min = int(await db.scalar(_minutes_q(today_start)) or 0)
    week_min = int(await db.scalar(_minutes_q(week_start)) or 0)

    today_count = await db.scalar(
        select(func.count()).where(
            PomodoroSession.user_id == user.id,
            PomodoroSession.type == "work",
            PomodoroSession.completed.is_(True),
            PomodoroSession.started_at >= today_start,
        )
    ) or 0

    return PomodoroStatsOut(
        today_work_minutes=today_min,
        week_work_minutes=week_min,
        today_sessions=today_count,
    )
