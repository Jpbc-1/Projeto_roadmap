from app.domain.repositories.reminder_repository import ReminderRepository
from app.infrastructure.database.models import Reminder


class ReminderNotFoundError(Exception):
    """Levantado quando o lembrete não existe."""


class ReminderAccessDeniedError(Exception):
    """Levantado quando o lembrete existe, mas pertence a outro usuário."""


class GetReminderUseCase:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def execute(self, reminder_id: int, user_id: int) -> Reminder:
        reminder = await self.reminder_repository.get_by_id(reminder_id)
        if reminder is None:
            raise ReminderNotFoundError()
        if reminder.user_id != user_id:
            raise ReminderAccessDeniedError()
        return reminder
