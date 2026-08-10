"""Agendador de lembretes: outra task asyncio dentro do mesmo processo,
separada do worker de jobs (worker.py) de propósito -- o worker processa
jobs que já existem na fila, esse aqui é quem DECIDE que um job novo
precisa existir, checando a cada minuto quem tem lembrete/compromisso
devido agora. Roda todo minuto (não no mesmo intervalo do worker, que é a
cada 2s -- não faz sentido nem é barato checar isso tantas vezes por
minuto) e enfileira em background_jobs -- o worker que já existe cuida do
resto (retry, backoff, etc.), sem duplicar nada disso aqui.

IMPORTANTE -- múltiplas réplicas: cada réplica roda o próprio loop, sem
coordenação nenhuma entre elas, DE PROPÓSITO. Não existe checkpoint local
(nem "última checagem em memória", nem lock distribuído) porque a
dedução de quem já disparou o quê mora inteiramente no banco
(Reminder.last_dispatched_date / CalendarEvent.reminder_dispatched_at,
via try_claim_dispatch -- ver ScheduleDueRemindersUseCase). Isso é o que
resolve duplicar/perder notificação com múltiplas réplicas: não interessa
quantas réplicas rodem esse loop ao mesmo tempo, cada lembrete só é
reivindicado por UMA delas, e a fonte de verdade sobrevive a qualquer
réplica reiniciando (diferente de estado em memória do processo).
"""

import asyncio
import logging

from app.application.notifications.schedule_due_reminders import ScheduleDueRemindersUseCase
from app.core.config import settings
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.calendar_event_repository import SQLAlchemyCalendarEventRepository
from app.infrastructure.repositories.job_repository import SQLAlchemyJobRepository
from app.infrastructure.repositories.reminder_repository import SQLAlchemyReminderRepository

logger = logging.getLogger(__name__)

_scheduler_task = None


async def _run_once() -> None:
    async with AsyncSessionLocal() as session:
        use_case = ScheduleDueRemindersUseCase(
            reminder_repository=SQLAlchemyReminderRepository(session),
            calendar_event_repository=SQLAlchemyCalendarEventRepository(session),
            job_repository=SQLAlchemyJobRepository(session),
        )
        enqueued = await use_case.execute()
        if enqueued:
            logger.info("Agendador de lembretes: %s notificação(ões) enfileirada(s).", enqueued)


async def _poll_loop() -> None:
    logger.info(
        "Agendador de lembretes iniciado (checagem a cada %.0fs).",
        settings.REMINDER_SCHEDULER_INTERVAL_SECONDS,
    )
    while True:
        try:
            await _run_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Agendador de lembretes: falha inesperada no loop.")

        await asyncio.sleep(settings.REMINDER_SCHEDULER_INTERVAL_SECONDS)


def start_reminder_scheduler() -> None:
    """Chamado no startup do FastAPI, junto com start_worker() -- ver
    main.py."""
    global _scheduler_task
    _scheduler_task = asyncio.create_task(_poll_loop())


async def stop_reminder_scheduler() -> None:
    """Chamado no shutdown, junto com stop_worker()."""
    global _scheduler_task
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
