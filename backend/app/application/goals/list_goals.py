from typing import List

from app.domain.repositories.goal_repository import GoalRepository
from app.infrastructure.database.models import Goal


class ListGoalsUseCase:
    def __init__(self, goal_repository: GoalRepository):
        self.goal_repository = goal_repository

    async def execute(self, user_id: int, limit: int, offset: int) -> List[Goal]:
        return await self.goal_repository.list_by_user(user_id, limit=limit, offset=offset)