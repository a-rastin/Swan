"""External task endpoints consumed by n8n."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.external.deps import get_external_user
from app.core.rate_limit import limiter
from app.db.session import get_session
from app.models import Task, TelegramLink, User
from app.schemas import TaskOut

router = APIRouter()


class ExternalTaskIn(BaseModel):
    title: str
    chat_id: str | None = None        # resolve user when master key used
    due_at: datetime | None = None
    priority: int = 0
    notes: str | None = None


async def _resolve_user(
    api_user: User | None,
    chat_id: str | None,
    db: AsyncSession,
) -> User:
    """Return target user. If api_user is None (master key), resolve via chat_id."""
    if api_user is not None:
        return api_user
    if not chat_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "chat_id required with master key")
    link = await db.scalar(
        select(TelegramLink).where(TelegramLink.telegram_chat_id == chat_id)
    )
    if not link:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no Swan user linked to this chat_id")
    user = await db.get(User, link.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return user


@router.post("/tasks", response_model=TaskOut, status_code=201)
@limiter.limit("60/minute")
async def create_task(
    request: Request,
    body: ExternalTaskIn,
    api_user: User | None = Depends(get_external_user),
    db: AsyncSession = Depends(get_session),
):
    user = await _resolve_user(api_user, body.chat_id, db)
    obj = Task(
        user_id=user.id,
        title=body.title[:255],
        notes=body.notes,
        priority=body.priority,
        due_at=body.due_at,
        source="telegram",
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get("/tasks", response_model=list[TaskOut])
@limiter.limit("60/minute")
async def list_tasks(
    request: Request,
    due: str | None = None,          # "today" or ISO date
    chat_id: str | None = None,
    api_user: User | None = Depends(get_external_user),
    db: AsyncSession = Depends(get_session),
):
    user = await _resolve_user(api_user, chat_id, db)
    q = select(Task).where(Task.user_id == user.id, Task.status != "done")
    if due == "today":
        today = date.today()
        q = q.where(
            Task.due_at >= datetime(today.year, today.month, today.day, tzinfo=timezone.utc),
            Task.due_at < datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc),
        )
    elif due:
        try:
            d = date.fromisoformat(due)
            q = q.where(
                Task.due_at >= datetime(d.year, d.month, d.day, tzinfo=timezone.utc),
                Task.due_at < datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc),
            )
        except ValueError:
            pass
    rows = await db.scalars(q.order_by(Task.due_at.nullslast(), Task.created_at))
    return list(rows)


@router.patch("/tasks/{task_id}/complete", response_model=TaskOut)
@limiter.limit("60/minute")
async def complete_task(
    request: Request,
    task_id: str,
    chat_id: str | None = None,
    api_user: User | None = Depends(get_external_user),
    db: AsyncSession = Depends(get_session),
):
    import uuid as _uuid
    user = await _resolve_user(api_user, chat_id, db)
    try:
        tid = _uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid task_id")
    obj = await db.get(Task, tid)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    obj.status = "done"
    obj.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(obj)
    return obj
