"""Create all DB tables if missing. Idempotent. Runs on container start."""
import asyncio

from app.db.base import Base  # imports Base + all models
from app.db.session import engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("DB tables ready")


if __name__ == "__main__":
    asyncio.run(main())
