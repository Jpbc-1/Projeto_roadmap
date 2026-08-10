from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações centrais da aplicação, carregadas de variáveis de ambiente (.env)."""

    APP_NAME: str = "Roadmap AI API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/roadmap_ai"

    DB_POOL_RECYCLE_SECONDS: int = 1800

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY ausente ou fraca (precisa de pelo menos 32 caracteres). "
                "Gere uma com: python -c \"import secrets; print(secrets.token_urlsafe(32))\" "
                "e coloque no .env (ou nas variáveis de ambiente do seu serviço de deploy)."
            )
        return v

    GEMINI_API_KEY: str = ""

    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_PRO_MODEL: str = "gemini-3.6-flash"
    GEMINI_FALLBACK_MODEL: str = "gemini-3.1-flash-lite"
    AUTO_ADAPT_EVERY_N_CHAPTERS: int = 2
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"

    
    JOB_POLL_INTERVAL_SECONDS: float = 2.0
    JOB_BATCH_SIZE: int = 5
    JOB_MAX_ATTEMPTS: int = 3
    JOB_STALE_AFTER_SECONDS: int = 600

   
    REMINDER_SCHEDULER_INTERVAL_SECONDS: float = 60.0

    CREDITS_FREE_PLAN_STARTING: int = 500
    CREDITS_COST_GENERATE_ROADMAP: int = 150
    CREDITS_COST_ADAPT: int = 60

    LOGIN_RATE_LIMIT_PER_EMAIL: int = 5
    LOGIN_RATE_LIMIT_PER_IP: int = 20
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 900

    GOOGLE_OAUTH_CLIENT_ID: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()