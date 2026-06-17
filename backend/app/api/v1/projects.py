import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import Project, User
from app.schemas import ProjectIn, ProjectOut, ProjectUpdate

router = APIRouter()


async def _get_owned(db: AsyncSession, user: User, pid: uuid.UUID) -> Project:
    obj = await db.get(Project, pid)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    return obj


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    rows = await db.scalars(
        select(Project)
        .where(Project.user_id == user.id, Project.status != "archived")
        .order_by(Project.position, Project.id)
    )
    return list(rows)


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = Project(user_id=user.id, **body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, project_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, project_id)
    await db.delete(obj)
    await db.commit()
