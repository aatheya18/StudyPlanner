from fastapi import APIRouter
from backend.app.api.routes import profile, subjects, tasks, sessions, schedules, dashboard, reminders, ai

api_router = APIRouter(prefix="/api")

api_router.include_router(profile.router)
api_router.include_router(subjects.router)
api_router.include_router(tasks.router)
api_router.include_router(sessions.router)
api_router.include_router(schedules.router)
api_router.include_router(dashboard.router)
api_router.include_router(reminders.router)
api_router.include_router(ai.router)
