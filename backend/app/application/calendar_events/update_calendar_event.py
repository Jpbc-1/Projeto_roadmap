from datetime import datetime
from typing import Optional

from app.core import notification_defaults
from app.domain.repositories.calendar_event_repository import CalendarEventRepository
from app.infrastructure.database.models import CalendarEvent


class CalendarEventNotFoundError(Exception):
    """Levantado quando o compromisso não existe."""


class CalendarEventAccessDeniedError(Exception):
    """Levantado quando o compromisso existe, mas pertence a outro usuário."""


class UpdateCalendarEventUseCase:
    def __init__(self, calendar_event_repository: CalendarEventRepository):
        self.calendar_event_repository = calendar_event_repository

    async def execute(
        self,
        event_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        is_all_day: Optional[bool] = None,
        notify_enabled: Optional[bool] = None,
        remind_before_minutes: Optional[int] = None,
        notification_timing_mode: Optional[str] = None,
        notification_style: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> CalendarEvent:
        existing = await self.calendar_event_repository.get_by_id(event_id)
        if existing is None:
            raise CalendarEventNotFoundError()
        if existing.user_id != user_id:
            raise CalendarEventAccessDeniedError()

        fields = {}
        if title is not None:
            fields["title"] = title
        if description is not None:
            fields["description"] = description
        if start_datetime is not None:
            fields["start_datetime"] = start_datetime
        if end_datetime is not None:
            fields["end_datetime"] = end_datetime
        if is_all_day is not None:
            fields["is_all_day"] = is_all_day
        if notification_style is not None:
            fields["notification_style"] = notification_style
        if custom_message is not None:
            fields["custom_message"] = custom_message

        # notify_enabled, timing_mode e remind_before_minutes andam juntos
        # -- mesma lógica do create, resolvidos de novo aqui pra nunca
        # deixar o registro num estado inconsistente (ex: notify_enabled
        # ligado com remind_before_minutes nulo).
        effective_notify = notify_enabled if notify_enabled is not None else existing.notify_enabled
        effective_mode = notification_timing_mode or existing.notification_timing_mode

        if notify_enabled is not None or notification_timing_mode is not None or remind_before_minutes is not None:
            fields["notify_enabled"] = effective_notify
            fields["notification_timing_mode"] = effective_mode
            if not effective_notify:
                fields["remind_before_minutes"] = None
            elif effective_mode == "custom":
                fields["remind_before_minutes"] = (
                    remind_before_minutes if remind_before_minutes is not None else existing.remind_before_minutes
                )
            else:
                fields["remind_before_minutes"] = notification_defaults.DEFAULT_EVENT_REMINDER_MINUTES

        if not fields:
            return existing

        return await self.calendar_event_repository.update(event_id, **fields)
