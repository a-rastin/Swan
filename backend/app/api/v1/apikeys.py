import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import random_token, sha256
from app.db.session import get_session
from app.models import ApiKey, User

router = APIRouter()


class ApiKeyCreateIn(BaseModel):
    name: str
    scopes: str = "tasks:read,tasks:write"


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    scopes: str
    last_used_at: str | None = None
    revoked: bool


class ApiKeyCreateOut(ApiKeyOut):
    raw_key: str   # shown once; never stored plain


@router.get("", response_model=list[ApiKeyOut])
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    rows = list(await db.scalars(
        select(ApiKey)
        .where(ApiKey.owner_user_id == user.id, ApiKey.revoked.is_(False))
        .order_by(ApiKey.id)
    ))
    return rows


@router.post("", response_model=ApiKeyCreateOut, status_code=201)
async def create_key(
    body: ApiKeyCreateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    raw = random_token()
    obj = ApiKey(
        owner_user_id=user.id,
        name=body.name,
        key_hash=sha256(raw),
        scopes=body.scopes,
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    out = ApiKeyCreateOut.model_validate(obj)
    out.raw_key = raw
    return out


@router.delete("/{key_id}", status_code=204)
async def revoke_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    obj = await db.get(ApiKey, key_id)
    if obj is None or obj.owner_user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "key not found")
    obj.revoked = True
    await db.commit()
