from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.achievements import AchievementOut, UnlockedAchievementOut
from app.application.gamification.list_achievements import ListAchievementsUseCase
from app.application.gamification.list_user_achievements import ListUserAchievementsUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.achievement_repository import SQLAlchemyAchievementRepository

router = APIRouter()


@router.get("", response_model=List[AchievementOut])
async def list_achievements(db: AsyncSession = Depends(get_db_session)):
    """Todas as conquistas que existem, desbloqueadas ou não -- não
    depende de login, é a mesma lista pra todo mundo (é o 'catálogo')."""
    repository = SQLAlchemyAchievementRepository(db)
    use_case = ListAchievementsUseCase(repository)
    return await use_case.execute()


@router.get("/me", response_model=List[UnlockedAchievementOut])
async def list_my_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyAchievementRepository(db)
    use_case = ListUserAchievementsUseCase(repository)
    return await use_case.execute(current_user.id)
