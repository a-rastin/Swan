import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_ph = PasswordHasher()


def hash_password(raw: str) -> str:
    return _ph.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, raw)
    except VerifyMismatchError:
        return False


def _encode(sub: str, secret: str, minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, secret, algorithm="HS256")


def make_access_token(user_id: str) -> str:
    return _encode(user_id, settings.JWT_SECRET, settings.ACCESS_TOKEN_MINUTES)


def make_refresh_token(user_id: str) -> str:
    return _encode(user_id, settings.JWT_REFRESH_SECRET, settings.REFRESH_TOKEN_DAYS * 24 * 60)


def decode_token(token: str, refresh: bool = False) -> dict:
    secret = settings.JWT_REFRESH_SECRET if refresh else settings.JWT_SECRET
    return jwt.decode(token, secret, algorithms=["HS256"])


def random_token() -> str:
    return secrets.token_urlsafe(32)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
