from datetime import date
from typing import Literal, Optional

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
        weekly_active_days: Optional[int] = None,
        daily_time_minutes: Optional[int] = None,
        prior_knowledge_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None,
    ) -> Goal:
        return await self.goal_repository.create(
            user_id=user_id,
            context_prompt=context_prompt,
            target_date=target_date,
            weekly_active_days=weekly_active_days,
            daily_time_minutes=daily_time_minutes,
            prior_knowledge_level=prior_knowledge_level,
        )