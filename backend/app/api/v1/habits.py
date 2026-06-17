import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import Habit, HabitLog, User
from app.schemas import HabitIn, HabitLogIn, HabitOut, HabitStatsOut, HabitUpdate

router = APIRouter()


async def _get_owned(db: AsyncSession, user: User, habit_id: uuid.UUID) -> Habit:
    obj = await db.get(Habit, habit_id)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "habit not found")
    return obj


async def _streak(db: AsyncSession, habit_id: uuid.UUID) -> int:
    today = date.today()
    streak = 0
    current = today
    while True:
        log = await db.scalar(
            select(HabitLog).where(
                HabitLog.habit_id == habit_id,
                HabitLog.log_date == current,
                HabitLog.completed.is_(True),
            )
        )
        if not log:
            break
        streak += 1
        current -= timedelta(days=1)
    return streak


@router.get("", response_model=list[HabitOut])
async def list_habits(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    habits = list(await db.scalars(
        select(Habit)
        .where(Habit.user_id == user.id, Habit.archived.is_(False))
        .order_by(Habit.id)
    ))
    if not habits:
        return []

    today = date.today()
    logs_today = list(await db.scalars(
        select(HabitLog).where(
            HabitLog.habit_id.in_([h.id for h in habits]),
            HabitLog.log_date == today,
            HabitLog.completed.is_(True),
        )
    ))
    done_ids = {l.habit_id for l in logs_today}

    result = []
    for h in habits:
        out = HabitOut.model_validate(h)
        out.today_completed = h.id in done_ids
        if out.today_completed:
            out.streak = await _streak(db, h.id)
        result.append(out)
    return result


@router.post("", response_model=HabitOut, status_code=201)
async def create_habit(
    body: HabitIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = Habit(user_id=user.id, **body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    out = HabitOut.model_validate(obj)
    return out


@router.patch("/{habit_id}", response_model=HabitOut)
async def update_habit(
    habit_id: uuid.UUID,
    body: HabitUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, habit_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return HabitOut.model_validate(obj)


@router.delete("/{habit_id}", status_code=204)
async def delete_habit(
    habit_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, habit_id)
    await db.delete(obj)
    await db.commit()


@router.post("/{habit_id}/log", response_model=dict)
async def toggle_log(
    habit_id: uuid.UUID,
    body: HabitLogIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """Toggle today's (or given date's) completion. Returns {completed, streak}."""
    await _get_owned(db, user, habit_id)
    log_date = body.log_date or date.today()

    existing = await db.scalar(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id,
            HabitLog.log_date == log_date,
        )
    )
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"completed": False, "streak": 0}

    db.add(HabitLog(habit_id=habit_id, log_date=log_date, value=body.value, completed=True))
    await db.commit()
    streak = await _streak(db, habit_id)
    return {"completed": True, "streak": streak}


@router.get("/{habit_id}/stats", response_model=HabitStatsOut)
async def habit_stats(
    habit_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await _get_owned(db, user, habit_id)
    today = date.today()
    thirty_ago = today - timedelta(days=30)

    total = await db.scalar(
        select(func.count()).where(
            HabitLog.habit_id == habit_id,
            HabitLog.log_date >= thirty_ago,
            HabitLog.completed.is_(True),
        )
    ) or 0

    streak = await _streak(db, habit_id)
    return HabitStatsOut(
        streak=streak,
        total_logs=total,
        completion_rate_30d=round(total / 30, 2),
    )
