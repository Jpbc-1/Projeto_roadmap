import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import (
    achievements,
    auth,
    calendar_events,
    goals,
    jobs,
    missions,
    notifications,
    reminders,
    users,
    knowledge,
)
from app.core.ai.gemini_client import close_shared_http_client
from app.core.notifications.expo_push_client import close_shared_http_client as close_shared_expo_http_client
from app.core.jobs.reminder_scheduler import start_reminder_scheduler, stop_reminder_scheduler
from app.core.jobs.worker import start_worker, stop_worker
from app.infrastructure.database.session import get_db_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_worker()
    start_reminder_scheduler()
    yield
    await stop_worker()
    await stop_reminder_scheduler()
    await close_shared_http_client()
    await close_shared_expo_http_client()


app = FastAPI(
    title="Roadmap AI API",
    description="API do Roadmap AI — transforma objetivos em missões diárias personalizadas.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(missions.router, prefix="/api/v1/missions", tags=["missions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(reminders.router, prefix="/api/v1/reminders", tags=["reminders"])
app.include_router(calendar_events.router, prefix="/api/v1/calendar-events", tags=["calendar-events"])
app.include_router(achievements.router, prefix="/api/v1/achievements", tags=["achievements"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/health", tags=["status"])
def health_check():
    """Endpoint simples para verificar se a API está no ar (não toca o banco)."""
    return {"status": "ok"}


@app.get("/health/db", tags=["status"])
async def health_check_db(db: AsyncSession = Depends(get_db_session)):
    """Verifica se a conexão com o banco está respondendo de verdade (faz um
    SELECT 1). Útil pra testar rapidamente se o banco caiu/expirou sem
    precisar esperar isso quebrar no meio de uma feature real."""
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return {"status": "error", "database": "unreachable", "detail": str(exc)}
    return {"status": "ok", "database": "connected"}

