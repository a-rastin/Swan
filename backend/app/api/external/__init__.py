from fastapi import APIRouter

from app.api.external import tasks, telegram

external_router = APIRouter()
external_router.include_router(tasks.router,    tags=["external"])
external_router.include_router(telegram.router, tags=["external"])
