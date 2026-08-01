from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.missions import (
    MissionCompleteRequest,
    MissionCreateRequest,
    MissionExecutionOut,
    MissionOut,
    MissionUpdateRequest,
)
from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.missions.complete_mission import (
    CompleteMissionUseCase,
    MissionAccessDeniedError,
    MissionAlreadyCompletedError,
    MissionNotFoundError,
)
from app.application.missions.create_mission import (
    ChapterAlreadyCompletedError,
    ChapterNotFoundError,
    CreateMissionUseCase,
)
from app.application.missions.delete_mission import DeleteMissionUseCase, MissionHasExecutionError
from app.application.missions.edit_mission import EditMissionUseCase
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.core.config import settings
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository
from app.infrastructure.repositories.roadmap_repository import SQLAlchemyRoadmapRepository

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
    mission_repository = SQLAlchemyMissionRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    job_repository = SQLAlchemyJobRepository(db)
    use_case = CompleteMissionUseCase(mission_repository)

    try:
        result = await use_case.execute(
            mission_id=mission_id,
            user_id=current_user.id,
            user_reflection=payload.user_reflection,
            difficulty_rating=payload.difficulty_rating,
            satisfaction_rating=payload.satisfaction_rating,
        )
    except (MissionNotFoundError, MissionAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missão não encontrada.")
    except MissionAlreadyCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if result.chapter_completed_id is not None:
        # Extração de conhecimento roda em TODO capítulo concluído (o use
        # case decide sozinho se o goal envolve aprendizado). Antes ia
        # direto pra BackgroundTasks; agora entra na fila (background_jobs),
        # que sobrevive a restart e tenta de novo sozinha se falhar.
        await job_repository.enqueue(
            "extract_knowledge_nodes",
            {
                "goal_id": result.goal_id,
                "user_id": current_user.id,
                "chapter_id": result.chapter_completed_id,
            },
            user_id=current_user.id,
        )

        completed_count = await roadmap_repository.count_completed_chapters(result.roadmap_id)
        if completed_count > 0 and completed_count % settings.AUTO_ADAPT_EVERY_N_CHAPTERS == 0:
            await job_repository.enqueue(
                "auto_adapt_roadmap",
                {
                    "goal_id": result.goal_id,
                    "user_id": current_user.id,
                    "roadmap_id": result.roadmap_id,
                },
                user_id=current_user.id,
            )

    return result.execution


@router.post("", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = CreateMissionUseCase(goal_repository, roadmap_repository)

    try:
        return await use_case.execute(
            goal_id=payload.goal_id,
            user_id=current_user.id,
            chapter_id=payload.chapter_id,
            title=payload.title,
            description=payload.description,
            estimated_minutes=payload.estimated_minutes,
        )
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except RoadmapNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ChapterAlreadyCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{mission_id}", response_model=MissionOut)
async def update_mission(
    mission_id: int,
    payload: MissionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    mission_repository = SQLAlchemyMissionRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = EditMissionUseCase(mission_repository, roadmap_repository)

    try:
        return await use_case.execute(
            mission_id=mission_id,
            user_id=current_user.id,
            title=payload.title,
            description=payload.description,
            estimated_minutes=payload.estimated_minutes,
        )
    except (MissionNotFoundError, MissionAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missão não encontrada.")


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(
    mission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    mission_repository = SQLAlchemyMissionRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = DeleteMissionUseCase(mission_repository, roadmap_repository)

    try:
        await use_case.execute(mission_id=mission_id, user_id=current_user.id)
    except (MissionNotFoundError, MissionAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missão não encontrada.")
    except MissionHasExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))