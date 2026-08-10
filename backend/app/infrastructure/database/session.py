from typing import AsyncGenerator 
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI para injetar uma sessão de banco por requisição."""
    async with AsyncSessionLocal() as session:
        yield session