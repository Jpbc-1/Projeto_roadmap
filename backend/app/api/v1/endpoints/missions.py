from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.missions import MissionCompleteRequest, MissionExecutionOut
from app.application.missions.complete_mission import (
    CompleteMissionUseCase,
    MissionAccessDeniedError,
    MissionAlreadyCompletedError,
    MissionNotFoundError,
)
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository

router = APIRouter()


@router.post(
    "/{mission_id}/complete",
    response_model=MissionExecutionOut,
    status_code=status.HTTP_201_CREATED,
)
async def complete_mission(
    mission_id: int,
    payload: MissionCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyMissionRepository(db)
    use_case = CompleteMissionUseCase(repository)

    try:
        return await use_case.execute(
            mission_id=mission_id,
            user_id=current_user.id,
            user_reflection=payload.user_reflection,
        )
    except (MissionNotFoundError, MissionAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missão não encontrada.")
    except MissionAlreadyCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))