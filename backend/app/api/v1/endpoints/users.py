from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.users import DeleteAccountRequest, GamificationProfileOut
from app.application.auth.delete_account import (
    DeleteAccountUseCase,
    IncorrectPasswordError,
    PasswordConfirmationRequiredError,
    UserNotFoundError,
)
from app.application.users.get_gamification_profile import GetGamificationProfileUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter()


@router.get("/me", response_model=GamificationProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyMissionRepository(db)
    use_case = GetGamificationProfileUseCase(repository)
    return await use_case.execute(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Apaga a conta autenticada e TUDO que pertence a ela (objetivos,
    roadmaps, reminders, calendar_events, conquistas, contas OAuth
    vinculadas, push tokens, histórico de conhecimento...) -- ver
    UserRepository.delete_account pro escopo completo. IRREVERSÍVEL.

    Exige a senha atual no corpo da requisição como reconfirmação (exceto
    pra contas só de login social, que não têm senha) -- protege contra
    um token de sessão sequestrado ser suficiente sozinho pra destruir a
    conta."""
    repository = SQLAlchemyUserRepository(db)
    use_case = DeleteAccountUseCase(repository)

    try:
        await use_case.execute(user_id=current_user.id, password=payload.password)
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    except PasswordConfirmationRequiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe a senha atual para confirmar a exclusão da conta.",
        )
    except IncorrectPasswordError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha incorreta.")