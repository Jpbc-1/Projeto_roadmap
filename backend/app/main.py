from fastapi import FastAPI

from app.api.v1.endpoints import auth

app = FastAPI(
    title="Roadmap AI API",
    description="API do Roadmap AI — transforma objetivos em missões diárias personalizadas.",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/health", tags=["status"])
def health_check():
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}

