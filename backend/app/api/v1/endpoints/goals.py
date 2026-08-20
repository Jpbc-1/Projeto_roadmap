from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.goals.create_goal import EmailNotVerifiedError

from app.api.v1.dependencies import get_current_user
from app.api.v1.dependencies import PaginationParams, get_current_user
from app.api.v1.schemas.goals import (
    GoalAnswersRequest,
    GoalCreate,
    GoalCreatedResponse,
    GoalOut,
    RecommendationOut,
)
from app.api.v1.schemas.roadmap import (
    AdaptGoalRequest,
    AdaptGoalResponse,
    ChapterCreateRequest,
    ChapterLockRequest,
    ChapterProgressOut,
    MissionProgressOut,
    RoadmapProgressOut,
)
from app.application.goals.answer_goal_questions import AnswerGoalQuestionsUseCase, GoalNotAwaitingInfoError
from app.application.goals.create_goal import CreateGoalUseCase
from app.application.goals.get_goal import (
    GetGoalUseCase,
    GoalAccessDeniedError,
    GoalNotFoundError,
)
from app.application.goals.list_goals import ListGoalsUseCase
from app.application.roadmaps.adapt_roadmap import AdaptationFailedError, AdaptRoadmapUseCase
from app.application.roadmaps.delete_roadmap import DeleteRoadmapUseCase
from app.application.roadmaps.confirm_adaptation import (
    AdaptationOperationNoLongerValidError,
    ConfirmAdaptationUseCase,
    NoPendingAdaptationError,
    RejectAdaptationUseCase,
)
from app.application.roadmaps.create_chapter import (
    CannotInsertAfterCompletedChapterError,
    ChapterNotFoundError,
    CreateChapterUseCase,
)
from app.application.roadmaps.get_roadmap import GetRoadmapUseCase, RoadmapNotFoundError
from app.application.roadmaps.propose_chapter_operation import ProposeChapterOperationUseCase
from app.application.roadmaps.set_chapter_lock import SetChapterLockUseCase
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.usage_logging import UsageCollector
from app.core.config import settings
from app.core.error_sanitization import safe_error_message
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository
from app.infrastructure.repositories.mission_repository import SQLAlchemyMissionRepository
from app.infrastructure.repositories.recommendation_repository import SQLAlchemyRecommendationRepository
from app.infrastructure.repositories.roadmap_repository import SQLAlchemyRoadmapRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

router = APIRouter()


@router.post("", response_model=GoalCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyGoalRepository(db)
    job_repository = SQLAlchemyJobRepository(db)
    use_case = CreateGoalUseCase(repository)
    user_repository = SQLAlchemyUserRepository(db)

    try:
        goal = await use_case.execute(
            user_id=current_user.id,
            is_email_verified=current_user.email_verified, # <-- O parâmetro novo aqui
            context_prompt=payload.context_prompt,
            target_date=payload.target_date,
            weekly_active_days=payload.weekly_active_days,
            daily_time_minutes=payload.daily_time_minutes,
            prior_knowledge_level=payload.prior_knowledge_level,
        )
    except EmailNotVerifiedError as e:
        # Se o e-mail não for verificado, devolvemos 403 e a execução para aqui!
        raise HTTPException(status_code=403, detail=str(e))

    charged = await user_repository.try_deduct_credits(
        current_user.id, settings.CREDITS_COST_GENERATE_ROADMAP
    )
    if not charged:
        # Se falhou a cobrança, apagamos o objetivo que tínhamos acabado de criar e damos erro.
        await repository.delete(goal.id) 
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                f"Créditos insuficientes (precisa de {settings.CREDITS_COST_GENERATE_ROADMAP}) "
                "para criar um novo objetivo."
            ),
        )

    await job_repository.enqueue("intake_goal", {"goal_id": goal.id}, user_id=current_user.id)

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
    pagination: PaginationParams = Depends(PaginationParams),
):
    repository = SQLAlchemyGoalRepository(db)
    use_case = ListGoalsUseCase(repository)
    return await use_case.execute(user_id=current_user.id, limit=pagination.limit, offset=pagination.offset)


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


@router.post("/{goal_id}/answers", status_code=status.HTTP_202_ACCEPTED)
async def answer_goal_questions(
    goal_id: int,
    payload: GoalAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Responde às perguntas de esclarecimento da triagem inicial (quando
    GET /goals/{id} mostra generation_status="awaiting_info" e
    pending_questions preenchido). Depois de respondido, a geração do
    roadmap é enfileirada de verdade."""
    goal_repository = SQLAlchemyGoalRepository(db)
    job_repository = SQLAlchemyJobRepository(db)
    use_case = AnswerGoalQuestionsUseCase(goal_repository)

    try:
        await use_case.execute(goal_id=goal_id, user_id=current_user.id, answers=payload.answers)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except GoalNotAwaitingInfoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await job_repository.enqueue("generate_roadmap", {"goal_id": goal_id}, user_id=current_user.id)

    return {"message": "Respostas recebidas! Estamos montando seu roadmap."}


@router.get("/{goal_id}/recommendations", response_model=List[RecommendationOut])
async def get_recommendations(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Recursos (apps, cursos, livros, comunidades) sugeridos pela IA junto
    com a geração inicial do roadmap -- lista vazia é normal (a IA só
    sugere quando tem confiança real, ver generate_roadmap.py)."""
    goal_repository = SQLAlchemyGoalRepository(db)
    recommendation_repository = SQLAlchemyRecommendationRepository(db)

    goal = await goal_repository.get_by_id(goal_id)
    if goal is None or goal.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")

    return await recommendation_repository.get_by_goal(goal_id)


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

    # Capítulo/missão "atuais" calculados aqui pra o front não precisar
    # varrer chapters/missions procurando o primeiro não concluído.
    current_chapter = next((c for c in roadmap.chapters if c.status == "in_progress"), None)
    current_mission_id = None
    if current_chapter is not None:
        current_mission = next(
            (m for m in current_chapter.missions if m.id not in completed_mission_ids), None
        )
        current_mission_id = current_mission.id if current_mission is not None else None

    return RoadmapProgressOut(
        id=roadmap.id,
        version=roadmap.version,
        current_chapter_id=current_chapter.id if current_chapter is not None else None,
        current_mission_id=current_mission_id,
        chapters=[
            ChapterProgressOut(
                id=chapter.id,
                title=chapter.title,
                order_index=chapter.order_index,
                status=chapter.status,
                created_by=chapter.created_by,
                is_locked_from_ai=chapter.is_locked_from_ai,
                missions=[
                    MissionProgressOut(
                        id=mission.id,
                        title=mission.title,
                        description=mission.description,
                        estimated_minutes=mission.estimated_minutes,
                        order_index=mission.order_index,
                        completed=mission.id in completed_mission_ids,
                        is_conceptual=mission.is_conceptual,
                        created_by=mission.created_by,
                    )
                    for mission in chapter.missions
                ],
            )
            for chapter in roadmap.chapters
        ],
    )


@router.delete("/{goal_id}/roadmap", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Apaga o roadmap ativo deste objetivo -- capítulos, missões e
    execuções registradas vão junto. O objetivo em si (Goal) continua
    existindo, só fica sem roadmap; GET /goals/{goal_id}/roadmap volta a
    dar 404 depois disso, agora com generation_status="deleted"."""
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = DeleteRoadmapUseCase(goal_repository, roadmap_repository)

    try:
        await use_case.execute(goal_id=goal_id, user_id=current_user.id)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except RoadmapNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/{goal_id}/adapt", response_model=AdaptGoalResponse)
async def adapt_goal(
    goal_id: int,
    payload: AdaptGoalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    recommendation_repository = SQLAlchemyRecommendationRepository(db)
    user_repository = SQLAlchemyUserRepository(db)

    goal = await goal_repository.get_by_id(goal_id)
    if goal is None or goal.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")

    charged = await user_repository.try_deduct_credits(current_user.id, settings.CREDITS_COST_ADAPT)
    if not charged:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Créditos insuficientes (precisa de {settings.CREDITS_COST_ADAPT}) para adaptar o roadmap.",
        )

    usage = UsageCollector(user_id=current_user.id)

    try:
        proposal_ai_client = GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_PRO_MODEL,
            fallback_models=[settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL],
            on_usage=usage.logger_for("propose_chapter_operation"),
        )
        propose_use_case = ProposeChapterOperationUseCase(
            goal_repository, roadmap_repository, proposal_ai_client
        )

        try:
            classification = await propose_use_case.execute(
                goal_id=goal_id, user_id=current_user.id, feedback=payload.feedback
            )
        except (GoalNotFoundError, GoalAccessDeniedError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
        except RoadmapNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

        if classification.scope == "chapter_operation" and classification.operation is not None:
            return AdaptGoalResponse(
                message=classification.operation.get("summary") or "Alteração proposta em um capítulo.",
                requires_confirmation=True,
            )

        ai_client = GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_PRO_MODEL,
            fallback_models=[settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL],
            on_usage=usage.logger_for("adapt_roadmap"),
        )
        use_case = AdaptRoadmapUseCase(goal_repository, roadmap_repository, recommendation_repository, ai_client)

        try:
            result = await use_case.execute(
                goal_id=goal_id,
                user_id=current_user.id,
                feedback=payload.feedback,
            )
        except (GoalNotFoundError, GoalAccessDeniedError):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
        except RoadmapNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        except AdaptationFailedError as exc:
            raise HTTPException(
                status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
                detail=safe_error_message(exc, "Não foi possível adaptar o roadmap agora"),
            )
    except HTTPException:
        await user_repository.refund_credits(current_user.id, settings.CREDITS_COST_ADAPT)
        raise
    finally:
        await usage.flush(db)

    return AdaptGoalResponse(
        message=f"{result.chapters_changed} capítulo(s) e {result.missions_changed} missão(ões) atualizados!",
        chapters_changed=result.chapters_changed,
        missions_changed=result.missions_changed,
    )


@router.post("/{goal_id}/adapt/confirm")
async def confirm_adaptation(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Aplica de fato a proposta que ficou pendente depois de um POST
    /adapt que retornou requires_confirmation=True."""
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = ConfirmAdaptationUseCase(goal_repository, roadmap_repository)

    try:
        await use_case.execute(goal_id=goal_id, user_id=current_user.id)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except NoPendingAdaptationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except AdaptationOperationNoLongerValidError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return {"message": "Alteração aplicada com sucesso."}


@router.post("/{goal_id}/adapt/reject")
async def reject_adaptation(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Descarta a proposta pendente -- o roadmap continua exatamente como
    estava, nada é alterado."""
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = RejectAdaptationUseCase(goal_repository, roadmap_repository)

    try:
        await use_case.execute(goal_id=goal_id, user_id=current_user.id)
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except NoPendingAdaptationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"message": "Alteração descartada. Seu roadmap continua como estava."}


@router.post("/{goal_id}/chapters", status_code=status.HTTP_201_CREATED)
async def create_chapter(
    goal_id: int,
    payload: ChapterCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = CreateChapterUseCase(goal_repository, roadmap_repository)

    try:
        await use_case.execute(
            goal_id=goal_id,
            user_id=current_user.id,
            title=payload.title,
            after_chapter_id=payload.after_chapter_id,
        )
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except RoadmapNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CannotInsertAfterCompletedChapterError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"message": "Capítulo criado. Adicione missões a ele para começar."}


@router.patch("/{goal_id}/chapters/{chapter_id}/lock")
async def set_chapter_lock(
    goal_id: int,
    chapter_id: int,
    payload: ChapterLockRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Trava (locked=true) ou destrava (locked=false) um capítulo contra
    mudanças da adaptação por IA -- tanto pra proteger um capítulo que a
    pessoa já ajustou do jeito que queria, quanto porque a IA nunca deve
    tentar mudar aquele conteúdo de novo."""
    goal_repository = SQLAlchemyGoalRepository(db)
    roadmap_repository = SQLAlchemyRoadmapRepository(db)
    use_case = SetChapterLockUseCase(goal_repository, roadmap_repository)

    try:
        await use_case.execute(
            goal_id=goal_id, user_id=current_user.id, chapter_id=chapter_id, locked=payload.locked
        )
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")
    except RoadmapNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ChapterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    verb = "travado" if payload.locked else "destravado"
    return {"message": f"Capítulo {verb} para alterações da IA."}


@router.post("/{goal_id}/knowledge", response_model=KnowledgeNodeOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge_node(
    goal_id: int,
    payload: CreateKnowledgeNodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal_repository = SQLAlchemyGoalRepository(db)
    knowledge_node_repository = SQLAlchemyKnowledgeNodeRepository(db)
    embedding_ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_EMBEDDING_MODEL)
    use_case = CreateKnowledgeNodeUseCase(goal_repository, knowledge_node_repository, embedding_ai_client)

    try:
        result = await use_case.execute(
            goal_id=goal_id, user_id=current_user.id, topic_name=payload.topic_name
        )
    except (GoalNotFoundError, GoalAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objetivo não encontrado.")

    return KnowledgeNodeOut(
        node_id=result.node.id,
        topic_name=result.node.topic_name,
        next_review_date=result.node.next_review_date,
        mastery_level=compute_mastery_level(result.node.interval_days),
        was_duplicate=result.was_duplicate,
    )
