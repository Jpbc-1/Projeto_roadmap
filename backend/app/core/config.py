from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações centrais da aplicação, carregadas de variáveis de ambiente (.env)."""

    APP_NAME: str = "Roadmap AI API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/roadmap_ai"

    class Config:
        env_file = ".env"


settings = Settings()
