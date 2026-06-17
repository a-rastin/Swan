from fastapi import APIRouter

from app.api.v1 import ai, apikeys, auth, files, habits, lists, pomodoro, projects, push, tasks, telegram, users

api_router = APIRouter()
api_router.include_router(auth.router,     prefix="/auth",     tags=["auth"])
api_router.include_router(users.router,    prefix="/users",    tags=["users"])
api_router.include_router(lists.router,    prefix="/lists",    tags=["lists"])
api_router.include_router(tasks.router,    prefix="/tasks",    tags=["tasks"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(habits.router,   prefix="/habits",   tags=["habits"])
api_router.include_router(pomodoro.router, prefix="/pomodoro", tags=["pomodoro"])
api_router.include_router(push.router,     prefix="/push",     tags=["push"])
api_router.include_router(ai.router,       prefix="/ai",       tags=["ai"])
api_router.include_router(apikeys.router,  prefix="/apikeys",  tags=["apikeys"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(files.router,    prefix="/files",    tags=["files"])
