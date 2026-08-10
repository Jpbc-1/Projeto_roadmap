from datetime import datetime, timezone
from typing import Optional

from app.domain.repositories.calendar_event_repository import CalendarEventRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.reminder_repository import ReminderRepository


class ScheduleDueRemindersUseCase:
    """
    Roda periodicamente (ver core/jobs/reminder_scheduler.py) e enfileira
    um BackgroundJob "send_reminder_notification" pra cada Reminder/
    CalendarEvent que está devido -- reaproveita a fila que já existe
    (app/core/jobs/), não cria infraestrutura nova.

    IMPORTANTE -- múltiplas réplicas da API: cada candidato "devido"
    passa por um try_claim_dispatch ANTES de enfileirar. Isso é um UPDATE
    atômico condicional no banco (não um lock em memória, que cada
    réplica teria o seu, sem saber da existência das outras) -- só quem
    de fato ganha a corrida enfileira o job. Se três réplicas rodam esse
    método no mesmo segundo e veem o mesmo lembrete "devido", só UMA
    consegue reivindicar o disparo; as outras duas recebem False do claim
    e simplesmente pulam, sem duplicar nem precisar de coordenação
    explícita entre elas. Ver docs/adr.

    NÃO manda notificação nenhuma diretamente -- só decide "isso precisa
    ser avisado" e entrega pro job_repository. Quem manda de verdade é o
    handler (core/jobs/handlers.py), puxado pelo worker que já existe.
    """

    def __init__(
        self,
        reminder_repository: ReminderRepository,
        calendar_event_repository: CalendarEventRepository,
        job_repository: JobRepository,
    ):
        self.reminder_repository = reminder_repository
        self.calendar_event_repository = calendar_event_repository
        self.job_repository = job_repository

    async def execute(self, now_utc: Optional[datetime] = None) -> int:
        now_utc = now_utc or datetime.now(timezone.utc)
        enqueued = 0

        for reminder in await self.reminder_repository.list_due(now_utc):
            won = await self.reminder_repository.try_claim_dispatch(reminder.id)
            if not won:
                continue
            await self.job_repository.enqueue(
                job_type="send_reminder_notification",
                payload={"source_type": "reminder", "source_id": reminder.id},
                user_id=reminder.user_id,
            )
            enqueued += 1

        for event in await self.calendar_event_repository.list_due_reminders(now_utc):
            won = await self.calendar_event_repository.try_claim_dispatch(event.id)
            if not won:
                continue
            await self.job_repository.enqueue(
                job_type="send_reminder_notification",
                payload={"source_type": "calendar_event", "source_id": event.id},
                user_id=event.user_id,
            )
            enqueued += 1

        return enqueued
