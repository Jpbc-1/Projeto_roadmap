from datetime import date
from typing import Optional

from app.domain.repositories.goal_repository import GoalRepository
from app.infrastructure.database.models import Goal


class CreateGoalUseCase:
    def __init__(self, goal_repository: GoalRepository):
        self.goal_repository = goal_repository

    async def execute(
        self,
        user_id: int,
        context_prompt: str,
        target_date: Optional[date],
    ) -> Goal:
        return await self.goal_repository.create(
            user_id=user_id,
            context_prompt=context_prompt,
            target_date=target_date,
        )