from datetime import datetime
from typing import Optional

from app.core import notification_defaults
from app.domain.repositories.calendar_event_repository import CalendarEventRepository
from app.infrastructure.database.models import CalendarEvent


class CreateCalendarEventUseCase:
    def __init__(self, calendar_event_repository: CalendarEventRepository):
        self.calendar_event_repository = calendar_event_repository

    async def execute(
        self,
        user_id: int,
        title: str,
        start_datetime: datetime,
        notification_timing_mode: str,
        notification_style: str,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        is_all_day: bool = False,
        notify_enabled: bool = True,
        remind_before_minutes: Optional[int] = None,
        custom_message: Optional[str] = None,
    ) -> CalendarEvent:
        resolved_minutes = None
        if notify_enabled:
            resolved_minutes = (
                remind_before_minutes
                if notification_timing_mode == "custom"
                else notification_defaults.DEFAULT_EVENT_REMINDER_MINUTES
            )

        return await self.calendar_event_repository.create(
            user_id=user_id,
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            is_all_day=is_all_day,
            notify_enabled=notify_enabled,
            remind_before_minutes=resolved_minutes,
            notification_timing_mode=notification_timing_mode,
            notification_style=notification_style,
            custom_message=custom_message if notification_style == "custom_message" else None,
        )
