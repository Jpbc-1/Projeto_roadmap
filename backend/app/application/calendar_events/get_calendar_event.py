from app.domain.repositories.calendar_event_repository import CalendarEventRepository
from app.infrastructure.database.models import CalendarEvent


class CalendarEventNotFoundError(Exception):
    """Levantado quando o compromisso não existe."""


class CalendarEventAccessDeniedError(Exception):
    """Levantado quando o compromisso existe, mas pertence a outro usuário."""


class GetCalendarEventUseCase:
    def __init__(self, calendar_event_repository: CalendarEventRepository):
        self.calendar_event_repository = calendar_event_repository

    async def execute(self, event_id: int, user_id: int) -> CalendarEvent:
        event = await self.calendar_event_repository.get_by_id(event_id)
        if event is None:
            raise CalendarEventNotFoundError()
        if event.user_id != user_id:
            raise CalendarEventAccessDeniedError()
        return event
