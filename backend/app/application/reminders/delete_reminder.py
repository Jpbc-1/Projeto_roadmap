from app.domain.repositories.reminder_repository import ReminderRepository


class ReminderNotFoundError(Exception):
    """Levantado quando o lembrete não existe."""


class ReminderAccessDeniedError(Exception):
    """Levantado quando o lembrete existe, mas pertence a outro usuário."""


class DeleteReminderUseCase:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def execute(self, reminder_id: int, user_id: int) -> None:
        reminder = await self.reminder_repository.get_by_id(reminder_id)
        if reminder is None:
            raise ReminderNotFoundError()
        if reminder.user_id != user_id:
            raise ReminderAccessDeniedError()

        await self.reminder_repository.delete(reminder_id)
