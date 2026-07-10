from fastapi import FastAPI

app = FastAPI(
    title="Roadmap AI API",
    description="API do Roadmap AI — transforma objetivos em missões diárias personalizadas.",
    version="0.1.0",
)


@app.get("/health", tags=["status"])
def health_check():
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}


# Os routers de cada domínio (objetivos, roadmaps, missões, usuários...)
# serão incluídos aqui conforme forem implementados, ex:
# from app.api.v1.endpoints import goals
# app.include_router(goals.router, prefix="/api/v1/goals", tags=["goals"])
