from datetime import datetime
from typing import Any, List, Optional, Protocol

from app.infrastructure.database.models import CalendarEvent


class CalendarEventRepository(Protocol):
    async def create(
        self,
        user_id: int,
        title: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        is_all_day: bool = False,
        notify_enabled: bool = True,
        remind_before_minutes: Optional[int] = None,
        notification_timing_mode: str = "app_default",
        notification_style: str = "app_generated",
        custom_message: Optional[str] = None,
    ) -> CalendarEvent: ...

    async def list_by_range(self, user_id: int, start: datetime, end: datetime) -> List[CalendarEvent]:
        """Lista compromissos cujo início cai dentro do intervalo -- é o
        que alimenta a visão de calendário (mês/semana) na tela de
        Rotina."""
        ...

    async def get_by_id(self, event_id: int) -> Optional[CalendarEvent]: ...

    async def update(self, event_id: int, **fields: Any) -> CalendarEvent: ...

    async def delete(self, event_id: int) -> None: ...

    async def list_due_reminders(self, now_utc: datetime) -> List[CalendarEvent]:
        """Eventos com notify_enabled=True cujo horário de lembrete
        (start_datetime - remind_before_minutes) cai no minuto de
        'now_utc'. start_datetime já é tz-aware/absoluto, então isso NÃO
        precisa de conversão de fuso (diferente de Reminder.list_due).
        Usado pelo agendador de disparo, não pela tela de calendário."""
        ...
