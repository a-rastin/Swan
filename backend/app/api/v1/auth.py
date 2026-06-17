from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import (
    decode_token,
    hash_password,
    make_access_token,
    make_refresh_token,
    sha256,
    verify_password,
)
from app.db.session import get_session
from app.models import PomodoroSettings, RefreshToken, User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter()

REFRESH_COOKIE = "swan_refresh"


def _set_refresh_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        REFRESH_COOKIE,
        token,
        httponly=True,
        secure=settings.ENV != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 3600,
        path="/api/v1/auth",
    )


async def _issue_refresh(db: AsyncSession, user_id) -> str:
    token = make_refresh_token(str(user_id))
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=sha256(token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_DAYS),
        )
    )
    await db.commit()
    return token


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_session)):
    exists = await db.scalar(select(User).where(User.email == body.email.lower()))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        name=body.name,
        locale=body.locale if body.locale in ("en", "fa") else "en",
    )
    db.add(user)
    await db.flush()
    db.add(PomodoroSettings(user_id=user.id))
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginIn, response: Response, db: AsyncSession = Depends(get_session)):
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    refresh = await _issue_refresh(db, user.id)
    _set_refresh_cookie(response, refresh)
    return TokenOut(access_token=make_access_token(str(user.id)))


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    swan_refresh: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_session),
):
    if not swan_refresh:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing refresh token")
    try:
        payload = decode_token(swan_refresh, refresh=True)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
    row = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == sha256(swan_refresh),
            RefreshToken.revoked.is_(False),
        )
    )
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh token revoked")
    # rotate
    row.revoked = True
    new_refresh = await _issue_refresh(db, row.user_id)
    _set_refresh_cookie(response, new_refresh)
    return TokenOut(access_token=make_access_token(payload["sub"]))


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return Response(status_code=204)
