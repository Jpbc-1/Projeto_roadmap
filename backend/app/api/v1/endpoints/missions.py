import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.missions import MissionCompleteRequest, MissionExecutionOut
from app.application.knowledge.extract_knowledge_nodes import ExtractKnowledgeNodesUseCase
from app.application.missions.complete_mission import (
    CompleteMissionUseCase,
    MissionAccessDeniedError,
    MissionAlreadyCompletedError,
    MissionNotFoundError,
)
from app.application.roadmaps.adapt_roadmap import AdaptRoadmapUseCase
from app.application.roadmaps.auto_adapt_roadmap import AutoAdaptRoadmapUseCase
from app.core.ai.gemini_client import GeminiClient
from app.core.config import settings
from app.infrastructure.database.models import User
from app.infrastructure.database.session import AsyncSessionLocal, get_db_session
from app.infrastructure.repositories.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.repositories.knowledge_node_repository import SQLAlchemyKnowledgeNodeRepository
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository
from app.infrastructure.repositories.roadmap_repository import SQLAlchemyRoadmapRepository

logger = logging.getLogger(__name__)

router = APIRouter()


async def _auto_adapt_background(goal_id: int, user_id: int, roadmap_id: int) -> None:
    """Roda fora do ciclo da requisição, com sessão própria -- mesma razão
    de sempre: a sessão da requisição original já foi fechada."""
    try:
        async with AsyncSessionLocal() as session:
            goal_repository = SQLAlchemyGoalRepository(session)
            roadmap_repository = SQLAlchemyRoadmapRepository(session)

            triage_ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
            adapt_ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_PRO_MODEL)

            adapt_use_case = AdaptRoadmapUseCase(goal_repository, roadmap_repository, adapt_ai_client)
            auto_adapt_use_case = AutoAdaptRoadmapUseCase(
                roadmap_repository=roadmap_repository,
                triage_ai_client=triage_ai_client,
                adapt_use_case=adapt_use_case,
                chapters_window=settings.AUTO_ADAPT_EVERY_N_CHAPTERS,
            )
            await auto_adapt_use_case.execute(goal_id=goal_id, user_id=user_id, roadmap_id=roadmap_id)
    except Exception:  
        logger.exception(
            "Auto-adapt: falha inesperada fora do use case (goal_id=%s, roadmap_id=%s)", goal_id, roadmap_id
        )


async def _extract_knowledge_background(goal_id: int, user_id: int, chapter_id: int) -> None:
    """Roda fora do ciclo da requisição, com sessão própria. Dispara em TODO
    capítulo concluído (sem janela de N em N, diferente do auto-adapt) --
    o próprio use case decide internamente se o goal envolve aprendizado."""
    try:
        async with AsyncSessionLocal() as session:
            goal_repository = SQLAlchemyGoalRepository(session)
            roadmap_repository = SQLAlchemyRoadmapRepository(session)
            knowledge_node_repository = SQLAlchemyKnowledgeNodeRepository(session)

            extraction_ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
            embedding_ai_client = GeminiClient(
                api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_EMBEDDING_MODEL
            )

            use_case = ExtractKnowledgeNodesUseCase(
                goal_repository=goal_repository,
                roadmap_repository=roadmap_repository,
                knowledge_node_repository=knowledge_node_repository,
                extraction_ai_client=extraction_ai_client,
                embedding_ai_client=embedding_ai_client,
            )
            await use_case.execute(goal_id=goal_id, user_id=user_id, chapter_id=chapter_id)
    except Exception:  
        logger.exception(
            "Knowledge map: falha inesperada fora do use case (goal_id=%s, chapter_id=%s)", goal_id, chapter_id
        )


@router.post(
    "/{mission_id}/complete",
    response_model=MissionExecutionOut,
    status_code=status.HTTP_201_CREATED,
)
async def complete_mission(
    mission_id: int,
    payload: MissionCompleteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    mission_repository = SQLAlchemyMissionRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = CompleteMissionUseCase(mission_repository)

    try:
        result = await use_case.execute(
            mission_id=mission_id,
            user_id=current_user.id,
            user_reflection=payload.user_reflection,
        )
    except (MissionNotFoundError, MissionAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missão não encontrada.")
    except MissionAlreadyCompletedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if result.chapter_completed_id is not None:
        background_tasks.add_task(
            _extract_knowledge_background, result.goal_id, current_user.id, result.chapter_completed_id
        )

        completed_count = await roadmap_repository.count_completed_chapters(result.roadmap_id)
        if completed_count > 0 and completed_count % settings.AUTO_ADAPT_EVERY_N_CHAPTERS == 0:
            background_tasks.add_task(
                _auto_adapt_background, result.goal_id, current_user.id, result.roadmap_id
            )

    return result.execution