from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_session
from app.models import User
from app.schemas import ChangePasswordIn, UserOut, UserSettingsIn

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserSettingsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    if body.name is not None:
        user.name = body.name
    if body.locale in ("en", "fa"):
        user.locale = body.locale
    if body.calendar_pref in ("gregorian", "jalali"):
        user.calendar_pref = body.calendar_pref
    if body.timezone:
        user.timezone = body.timezone
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/me/password", status_code=204)
async def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "current password wrong")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
