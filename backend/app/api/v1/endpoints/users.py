from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.users import GamificationProfileOut
from app.application.users.get_gamification_profile import GetGamificationProfileUseCase
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository

router = APIRouter()


@router.get("/me", response_model=GamificationProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyMissionRepository(db)
    use_case = GetGamificationProfileUseCase(repository)
    return await use_case.execute(current_user)