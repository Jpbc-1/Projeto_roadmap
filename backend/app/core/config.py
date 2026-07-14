from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações centrais da aplicação, carregadas de variáveis de ambiente (.env)."""

    APP_NAME: str = "Roadmap AI API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/roadmap_ai"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    class Config:
        env_file = ".env"


settings = Settings()