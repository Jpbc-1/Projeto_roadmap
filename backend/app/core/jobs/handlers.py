"""Um handler por job_type. Cada um abre seus próprios repositórios/clients
a partir da sessão que o worker já abriu pra esse job (ver worker.py) --
mesma lógica que antes vivia solta dentro de _generate_roadmap_background,
_auto_adapt_background e _extract_knowledge_background nos endpoints, só
que agora persistida como job em vez de FastAPI BackgroundTasks."""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.goals.generate_roadmap import GenerateRoadmapUseCase
from app.application.goals.intake_goal import IntakeGoalUseCase
from app.application.goals.moderate_goal_content import ModerateGoalContentUseCase
from app.application.flashcards.extract_concepts import ExtractConceptsUseCase
from app.application.roadmaps.adapt_roadmap import AdaptRoadmapUseCase
from app.application.roadmaps.auto_adapt_roadmap import AutoAdaptRoadmapUseCase
from app.core.ai.gemini_client import GeminiClient
from app.core.ai.usage_logging import UsageCollector
from app.core.config import settings
from app.core.notifications import expo_push_client
from app.domain.services.notification_content import resolve_calendar_event_content, resolve_reminder_content
from app.infrastructure.repositories.calendar_event_repository import SQLAlchemyCalendarEventRepository
from app.infrastructure.repositories.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository
from app.infrastructure.repositories.deck_repository import SQLAlchemyDeckRepository
from app.infrastructure.repositories.flashcard_repository import SQLAlchemyFlashcardRepository
from app.infrastructure.repositories.knowledge_node_repository import SQLAlchemyKnowledgeNodeRepository
from app.infrastructure.repositories.recommendation_repository import SQLAlchemyRecommendationRepository
from app.infrastructure.repositories.reminder_repository import SQLAlchemyReminderRepository
from app.infrastructure.repositories.roadmap_repository import SQLAlchemyRoadmapRepository
from app.infrastructure.repositories.user_push_token_repository import SQLAlchemyUserPushTokenRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository

logger = logging.getLogger(__name__)


async def handle_intake_goal(session: AsyncSession, payload: Dict[str, Any]) -> None:
    """Modera + melhora o prompt + detecta info faltando. Se ficar pronto
    pra gerar (não precisou perguntar nada), encadeia o próximo job
    ("generate_roadmap") na mesma fila -- se precisou parar pra perguntar
    ou foi rejeitado, não encadeia nada; o objetivo fica esperando o
    usuário (ou parado, se rejeitado)."""
    goal_repository = SQLAlchemyGoalRepository(session)
    user_repository = SQLAlchemyUserRepository(session)
    job_repository = SQLAlchemyJobRepository(session)
    usage = UsageCollector(user_id=payload.get("user_id"))

    moderation_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_FALLBACK_MODEL,
        on_usage=usage.logger_for("moderation"),
    )
    moderation_use_case = ModerateGoalContentUseCase(moderation_ai_client)

    intake_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL,
        fallback_models=[settings.GEMINI_FALLBACK_MODEL],
        on_usage=usage.logger_for("intake"),
    )

    use_case = IntakeGoalUseCase(goal_repository, user_repository, moderation_use_case, intake_ai_client)
    outcome = await use_case.execute(goal_id=payload["goal_id"])
    await usage.flush(session)

    if outcome == "ready":
        await job_repository.enqueue(
            "generate_roadmap", {"goal_id": payload["goal_id"]}, user_id=payload.get("user_id")
        )


async def handle_generate_roadmap(session: AsyncSession, payload: Dict[str, Any]) -> None:
    goal_repository = SQLAlchemyGoalRepository(session)
    roadmap_repository = SQLAlchemyRoadmapRepository(session)
    recommendation_repository = SQLAlchemyRecommendationRepository(session)
    user_repository = SQLAlchemyUserRepository(session)
    usage = UsageCollector(user_id=payload.get("user_id"))

    generation_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_PRO_MODEL,
        fallback_models=[settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL],
        on_usage=usage.logger_for("generate_roadmap"),
    )

    use_case = GenerateRoadmapUseCase(
        goal_repository, roadmap_repository, recommendation_repository, user_repository, generation_ai_client
    )
    await use_case.execute(goal_id=payload["goal_id"])
    await usage.flush(session)


async def handle_adapt_roadmap(session: AsyncSession, payload: Dict[str, Any]) -> None:
    goal_repository = SQLAlchemyGoalRepository(session)
    roadmap_repository = SQLAlchemyRoadmapRepository(session)
    recommendation_repository = SQLAlchemyRecommendationRepository(session)
    usage = UsageCollector(user_id=payload.get("user_id"))

    ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_PRO_MODEL,
        fallback_models=[settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL],
        on_usage=usage.logger_for("adapt_roadmap"),
    )

    use_case = AdaptRoadmapUseCase(goal_repository, roadmap_repository, recommendation_repository, ai_client)
    await use_case.execute(
        goal_id=payload["goal_id"], user_id=payload["user_id"], feedback=payload.get("feedback")
    )
    await usage.flush(session)


async def handle_auto_adapt_roadmap(session: AsyncSession, payload: Dict[str, Any]) -> None:
    goal_repository = SQLAlchemyGoalRepository(session)
    roadmap_repository = SQLAlchemyRoadmapRepository(session)
    recommendation_repository = SQLAlchemyRecommendationRepository(session)
    usage = UsageCollector(user_id=payload.get("user_id"))

    triage_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_FALLBACK_MODEL,
        on_usage=usage.logger_for("auto_adapt_triage"),
    )
    adapt_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_PRO_MODEL,
        fallback_models=[settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL],
        on_usage=usage.logger_for("auto_adapt"),
    )

    adapt_use_case = AdaptRoadmapUseCase(goal_repository, roadmap_repository, recommendation_repository, adapt_ai_client)
    use_case = AutoAdaptRoadmapUseCase(
        roadmap_repository=roadmap_repository,
        triage_ai_client=triage_ai_client,
        adapt_use_case=adapt_use_case,
        chapters_window=settings.AUTO_ADAPT_EVERY_N_CHAPTERS,
    )
    await use_case.execute(
        goal_id=payload["goal_id"], user_id=payload["user_id"], roadmap_id=payload["roadmap_id"]
    )
    await usage.flush(session)


async def handle_extract_knowledge_nodes(session: AsyncSession, payload: Dict[str, Any]) -> None:
    """Nome do job continua "extract_knowledge_nodes" por compatibilidade
    com jobs já enfileirados antes desta mudança -- o que ele FAZ agora é
    mais do que extrair o nó: também julga importância e já gera o
    flashcard candidato (ver ExtractConceptsUseCase)."""
    goal_repository = SQLAlchemyGoalRepository(session)
    roadmap_repository = SQLAlchemyRoadmapRepository(session)
    knowledge_node_repository = SQLAlchemyKnowledgeNodeRepository(session)
    flashcard_repository = SQLAlchemyFlashcardRepository(session)
    deck_repository = SQLAlchemyDeckRepository(session)
    usage = UsageCollector(user_id=payload.get("user_id"))

    extraction_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_FALLBACK_MODEL,
        on_usage=usage.logger_for("extract_knowledge_nodes"),
    )
    embedding_ai_client = GeminiClient(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_EMBEDDING_MODEL,
        on_usage=usage.logger_for("embedding"),
    )

    use_case = ExtractConceptsUseCase(
        goal_repository=goal_repository,
        roadmap_repository=roadmap_repository,
        knowledge_node_repository=knowledge_node_repository,
        flashcard_repository=flashcard_repository,
        deck_repository=deck_repository,
        extraction_ai_client=extraction_ai_client,
        embedding_ai_client=embedding_ai_client,
    )
    await use_case.execute(
        goal_id=payload["goal_id"],
        user_id=payload["user_id"],
        chapter_id=payload["chapter_id"],
    )
    await usage.flush(session)


async def handle_send_reminder_notification(session: AsyncSession, payload: Dict[str, Any]) -> None:
    """Resolve o conteúdo (padrão do app ou mensagem da pessoa, ver
    domain/services/notification_content.py) e envia o push.

    Importante: NUNCA confia em texto vindo do payload -- ele só tem
    source_type/source_id. O conteúdo é sempre recalculado aqui, na hora
    do disparo, buscando o registro fresco no banco. Isso importa de
    verdade pro modo 'app_generated': se o payload guardasse o texto no
    momento do agendamento, uma missão concluída entre agendar e disparar
    deixaria a notificação desatualizada (avisando de algo que a pessoa
    já fez).

    Envio de verdade via Expo Push API (ver _send_push): manda pra todos
    os aparelhos que o usuário tiver registrado em UserPushToken. Se não
    tiver nenhum (nunca abriu o app com push habilitado, por exemplo),
    _send_push não faz nada -- não é erro, é o estado normal antes do
    primeiro registro."""
    source_type = payload["source_type"]
    source_id = payload["source_id"]

    if source_type == "reminder":
        reminder_repository = SQLAlchemyReminderRepository(session)
        roadmap_repository = SQLAlchemyRoadmapRepository(session)
        reminder = await reminder_repository.get_by_id(source_id)
        if reminder is None or not reminder.is_active:
            return 
        pending_mission_title = None
        if reminder.notification_style == "app_generated":
            pending_mission_title = await roadmap_repository.get_current_pending_mission_title_for_user(
                reminder.user_id
            )
        content = resolve_reminder_content(reminder, pending_mission_title=pending_mission_title)
        await _send_push(session, user_id=reminder.user_id, title=content.title, body=content.body)

    elif source_type == "calendar_event":
        event_repository = SQLAlchemyCalendarEventRepository(session)
        event = await event_repository.get_by_id(source_id)
        if event is None or not event.notify_enabled:
            return
        content = resolve_calendar_event_content(event)
        await _send_push(session, user_id=event.user_id, title=content.title, body=content.body)

    else:
        raise ValueError(f"source_type desconhecido em send_reminder_notification: {source_type!r}")


async def _send_push(session: AsyncSession, user_id: int, title: str, body: str) -> None:
    """Envia a notificação via Expo Push API pra TODOS os aparelhos que
    esse usuário tem registrados (UserPushToken) -- uma pessoa pode ter
    celular + tablet, por exemplo, e todos devem receber.

    Falha parcial não derruba o envio inteiro: o retorno do Expo é
    processado token a token, então se o envio pra UM aparelho falhar
    (ou o token dele estiver morto), os outros aparelhos do mesmo
    usuário ainda recebem a notificação normalmente.

    Se a chamada ao Expo falhar por completo (rede fora, credenciais
    erradas, etc. -- ver ExpoPushAPIError), a exceção é deixada subir
    de propósito: isso faz handle_send_reminder_notification falhar e o
    worker re-agendar esse job com backoff exponencial (mesma
    infraestrutura de retry que qualquer outro handler já usa, ver
    job_repository.mark_failed_or_retry) -- é exatamente o que a própria
    Expo recomenda pra erro de rede/5xx, sem precisar duplicar lógica de
    retry aqui.
    """
    token_repository = SQLAlchemyUserPushTokenRepository(session)
    tokens = await token_repository.list_by_user_id(user_id)
    if not tokens:
        return 

    for chunk_start in range(0, len(tokens), expo_push_client.EXPO_MAX_MESSAGES_PER_REQUEST):
        chunk = tokens[chunk_start : chunk_start + expo_push_client.EXPO_MAX_MESSAGES_PER_REQUEST]
        messages = [{"to": token.push_token, "title": title, "body": body, "data": {}} for token in chunk]

        response = await expo_push_client.send_push_batch(messages)
        tickets = response.get("data", [])

        dead_tokens: List[str] = []
        for token_row, ticket in zip(chunk, tickets):
            if not isinstance(ticket, dict) or ticket.get("status") != "error":
                continue  
            details = ticket.get("details") or {}
            if details.get("error") == "DeviceNotRegistered":
                dead_tokens.append(token_row.push_token)
            else:
                logger.warning(
                    "Expo push: ticket de erro (user_id=%s, não DeviceNotRegistered): %s",
                    user_id,
                    ticket.get("message"),
                )

        if dead_tokens:
            await token_repository.delete_by_tokens(dead_tokens)


JOB_HANDLERS = {
    "intake_goal": handle_intake_goal,
    "generate_roadmap": handle_generate_roadmap,
    "adapt_roadmap": handle_adapt_roadmap,
    "auto_adapt_roadmap": handle_auto_adapt_roadmap,
    "extract_knowledge_nodes": handle_extract_knowledge_nodes,
    "send_reminder_notification": handle_send_reminder_notification,
}
