"""Admin password reset (no email infra). Run inside the backend container.

Usage:
    docker compose exec backend python scripts/reset_password.py user@example.com NEWPASS
"""
import asyncio
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


async def main(email: str, new_password: str) -> None:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if not user:
            print(f"no user: {email}")
            return
        user.password_hash = hash_password(new_password)
        await db.commit()
        print(f"password reset for {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: reset_password.py EMAIL NEWPASS")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
