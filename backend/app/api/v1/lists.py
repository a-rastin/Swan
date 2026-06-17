import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import List as ListModel
from app.models import User
from app.schemas import ListIn, ListOut

router = APIRouter()


async def _get_owned(db: AsyncSession, user: User, list_id: uuid.UUID) -> ListModel:
    obj = await db.get(ListModel, list_id)
    if obj is None or obj.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "list not found")
    return obj


@router.get("", response_model=list[ListOut])
async def list_lists(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    rows = await db.scalars(
        select(ListModel)
        .where(ListModel.user_id == user.id, ListModel.archived.is_(False))
        .order_by(ListModel.position)
    )
    return list(rows)


@router.post("", response_model=ListOut, status_code=201)
async def create_list(body: ListIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    obj = ListModel(user_id=user.id, **body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.patch("/{list_id}", response_model=ListOut)
async def update_list(
    list_id: uuid.UUID,
    body: ListIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, list_id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete("/{list_id}", status_code=204)
async def delete_list(
    list_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await _get_owned(db, user, list_id)
    await db.delete(obj)
    await db.commit()
