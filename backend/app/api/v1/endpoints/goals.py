from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.goals import GoalCreate, GoalCreatedResponse, GoalOut
from app.api.v1.schemas.roadmap import ChapterProgressOut, MissionProgressOut, RoadmapProgressOut
from app.application.goals.create_goal import CreateGoalUseCase
from app.application.goals.generate_roadmap import GenerateRoadmapUseCase
from app.application.goals.get_goal import (
    GetGoalUseCase,
    GoalAccessDeniedError,
    GoalNotFoundError,
)
from app.application.goals.list_goals import ListGoalsUseCase
from app.application.goals.moderate_goal_content import ModerateGoalContentUseCase
from app.application.roadmaps.get_roadmap import GetRoadmapUseCase, RoadmapNotFoundError
from app.core.ai.gemini_client import GeminiClient
from app.core.config import settings
from app.infrastructure.database.models import User
from app.infrastructure.database.session import AsyncSessionLocal, get_db_session
from app.infrastructure.repositories.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository
from app.infrastructure.repositories.roadmap_repository import SQLAlchemyRoadmapRepository

router = APIRouter()


async def _generate_roadmap_background(goal_id: int) -> None:
    """Roda fora do ciclo da requisição HTTP -> precisa da SUA PRÓPRIA sessão
    de banco, já que a sessão da requisição original já foi fechada quando
    a resposta do POST /goals foi enviada ao cliente."""
    async with AsyncSessionLocal() as session:
        goal_repository = SQLAlchemyGoalRepository(session)
        roadmap_repository = SQLAlchemyRoadmapRepository(session)
        ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        moderation_use_case = ModerateGoalContentUseCase(ai_client)

        use_case = GenerateRoadmapUseCase(
            goal_repository=goal_repository,
            roadmap_repository=roadmap_repository,
            moderation_use_case=moderation_use_case,
            ai_client=ai_client,
        )
        await use_case.execute(goal_id)


@router.post("", response_model=GoalCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyGoalRepository(db)
    use_case = CreateGoalUseCase(repository)

    goal = await use_case.execute(
        user_id=current_user.id,
        context_prompt=payload.context_prompt,
        target_date=payload.target_date,
    )

    background_tasks.add_task(_generate_roadmap_background, goal.id)

    return GoalCreatedResponse(
        goal=goal,
        message=(
            "Objetivo recebido! Estamos montando seu roadmap personalizado "
            "— isso pode levar alguns segundos."
        ),
    )


@router.get("", response_model=List[GoalOut])
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyGoalRepository(db)
    use_case = ListGoalsUseCase(repository)
    return await use_case.execute(user_id=current_user.id)


@router.get("/{goal_id}", response_model=GoalOut)
async def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyGoalRepository(db)
    use_case = GetGoalUseCase(repository)

    try:
        return await use_case.execute(goal_id=goal_id, user_id=current_user.id)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")


@router.get("/{goal_id}/roadmap", response_model=RoadmapProgressOut)
async def get_roadmap(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    mission_repository = SQLAlchemyMissionRepository(db)
    use_case = GetRoadmapUseCase(goal_repository, roadmap_repository, mission_repository)

    try:
        roadmap, completed_mission_ids = await use_case.execute(goal_id=goal_id, user_id=current_user.id)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except RoadmapNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return RoadmapProgressOut(
        id=roadmap.id,
        version=roadmap.version,
        chapters=[
            ChapterProgressOut(
                id=chapter.id,
                title=chapter.title,
                order_index=chapter.order_index,
                status=chapter.status,
                missions=[
                    MissionProgressOut(
                        id=mission.id,
                        title=mission.title,
                        description=mission.description,
                        estimated_minutes=mission.estimated_minutes,
                        order_index=mission.order_index,
                        completed=mission.id in completed_mission_ids,
                    )
                    for mission in chapter.missions
                ],
            )
            for chapter in roadmap.chapters
        ],
    )