from typing import AsyncGenerator 
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    # pool_pre_ping: antes de emprestar uma conexão do pool, faz um "SELECT 1"
    # rápido nela. Se o servidor (ou um pooler no meio do caminho, tipo o do
    # Supabase) já tiver derrubado essa conexão por inatividade, o SQLAlchemy
    # descarta ela e abre uma nova na hora, de forma transparente -- em vez de
    # estourar erro só quando a gente tentasse de fato usar a conexão morta
    # (que era o que estava expirando nos seus testes).
    pool_pre_ping=True,
    # Reforço: recicla proativamente qualquer conexão mais velha que N
    # segundos, mesmo que o pre_ping não tenha notado problema ainda.
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)



async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI para injetar uma sessão de banco por requisição."""
    async with AsyncSessionLocal() as session:
        yield session