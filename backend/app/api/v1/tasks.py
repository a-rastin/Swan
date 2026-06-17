import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import Task, User
from app.schemas import TaskIn, TaskOut, TaskUpdate
from app.services.recurrence import compute_next_task_dates

router = APIRouter()


async def _get_owned(db: AsyncSession, user: User, task_id: uuid.UUID) -> Task:
    obj = await db.get(Task, task_id)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    return obj


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    list_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    due_from: datetime | None = None,
    due_to: datetime | None = None,
):
    q = select(Task).where(Task.user_id == user.id)
    if list_id:
        q = q.where(Task.list_id == list_id)
    if project_id:
        q = q.where(Task.project_id == project_id)
    if status_filter:
        q = q.where(Task.status == status_filter)
    if due_from:
        q = q.where(Task.due_at >= due_from)
    if due_to:
        q = q.where(Task.due_at <= due_to)
    rows = await db.scalars(q.order_by(Task.position, Task.created_at))
    return list(rows)


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(body: TaskIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    obj = Task(user_id=user.id, **body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, task_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, task_id)
    obj.status = "done"
    obj.completed_at = datetime.now(timezone.utc)
    await db.flush()

    if obj.recurrence_rrule:
        new_due, new_remind = compute_next_task_dates(
            obj.recurrence_rrule, obj.due_at, obj.remind_at
        )
        next_task = Task(
            user_id=obj.user_id,
            list_id=obj.list_id,
            project_id=obj.project_id,
            title=obj.title,
            notes=obj.notes,
            priority=obj.priority,
            recurrence_rrule=obj.recurrence_rrule,
            due_at=new_due,
            remind_at=new_remind,
            source=obj.source,
        )
        db.add(next_task)

    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, task_id)
    await db.delete(obj)
    await db.commit()
