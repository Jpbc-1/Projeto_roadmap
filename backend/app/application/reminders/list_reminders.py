from typing import List

from app.domain.repositories.reminder_repository import ReminderRepository
from app.infrastructure.database.models import Reminder


class ListRemindersUseCase:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def execute(self, user_id: int, limit: int, offset: int) -> List[Reminder]:
        return await self.reminder_repository.list_by_user(user_id, limit=limit, offset=offset)
