from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.notifications import (
    PushTokenOut,
    RegisterPushTokenInput,
    UnregisterPushTokenInput,
)
from app.application.notifications.register_push_token import RegisterPushTokenUseCase
from app.application.notifications.unregister_push_token import UnregisterPushTokenUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.user_push_token_repository import SQLAlchemyUserPushTokenRepository

router = APIRouter()


@router.post("/register-token", response_model=PushTokenOut, status_code=status.HTTP_200_OK)
async def register_token(
    payload: RegisterPushTokenInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Registra o push token desse aparelho pro usuário atual. UPSERT por
    push_token: se o mesmo aparelho já tinha registrado esse token (de
    novo, ou pra outra conta), a linha é atualizada -- nunca duplicada."""
    repository = SQLAlchemyUserPushTokenRepository(db)
    use_case = RegisterPushTokenUseCase(repository)
    return await use_case.execute(
        user_id=current_user.id,
        push_token=payload.push_token,
        platform=payload.platform,
    )


@router.delete("/unregister-token", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_token(
    payload: UnregisterPushTokenInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove o vínculo desse token com o usuário atual (ex: logout).
    Sempre 204, mesmo se o token não existir -- idempotente, pra não
    precisar de tratamento de erro especial no app se isso for chamado
    duas vezes (ex: logout com rede instável e o app repete a chamada)."""
    repository = SQLAlchemyUserPushTokenRepository(db)
    use_case = UnregisterPushTokenUseCase(repository)
    await use_case.execute(user_id=current_user.id, push_token=payload.push_token)
