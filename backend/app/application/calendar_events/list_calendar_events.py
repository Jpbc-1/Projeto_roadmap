from datetime import datetime
from typing import List

from app.domain.repositories.calendar_event_repository import CalendarEventRepository
from app.infrastructure.database.models import CalendarEvent


class ListCalendarEventsUseCase:
    def __init__(self, calendar_event_repository: CalendarEventRepository):
        self.calendar_event_repository = calendar_event_repository

    async def execute(self, user_id: int, start: datetime, end: datetime) -> List[CalendarEvent]:
        return await self.calendar_event_repository.list_by_range(user_id, start, end)
