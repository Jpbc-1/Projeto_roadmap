import logging

from fastapi import FastAPI

from app.api.v1.endpoints import auth, goals, missions, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Roadmap AI API",
    description="API do Roadmap AI — transforma objetivos em missões diárias personalizadas.",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
app.include_router(missions.router, prefix="/api/v1/missions", tags=["missions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health", tags=["status"])
def health_check():
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}

