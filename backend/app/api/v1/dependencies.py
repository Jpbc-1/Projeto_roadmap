from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency para proteger endpoints: exige um JWT válido no header Authorization."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    repository = SQLAlchemyUserRepository(db)
    user = await repository.get_by_email(email)
    if user is None:
        raise credentials_exception

    return user


class PaginationParams:
    """Dependency de paginação compartilhada por todo endpoint de listagem
    do usuário (reminders, calendar-events, goals, achievements/me,
    knowledge/due) -- ver settings.DEFAULT_PAGE_SIZE/MAX_PAGE_SIZE.

    O teto (`le=settings.MAX_PAGE_SIZE`) é a parte que importa de verdade:
    sem ele, alguém pedindo `?limit=999999` ainda conseguiria puxar uma
    conta inteira numa chamada só, mesmo com o endpoint "tendo paginação".
    FastAPI já devolve 422 sozinho se o valor pedido for maior que o teto
    ou menor que 1 -- não precisa validar isso à mão em cada endpoint.

    Uso: `pagination: PaginationParams = Depends(PaginationParams)` na
    assinatura do endpoint -- os campos viram query params documentados
    automaticamente no OpenAPI/Swagger."""

    def __init__(
        self,
        limit: int = Query(
            settings.DEFAULT_PAGE_SIZE,
            ge=1,
            le=settings.MAX_PAGE_SIZE,
            description="Quantos registros devolver (máximo definido pelo servidor).",
        ),
        offset: int = Query(0, ge=0, description="Quantos registros pular a partir do início."),
    ):
        self.limit = limit
        self.offset = offset
