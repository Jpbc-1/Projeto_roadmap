from datetime import date
from typing import Any, List, Literal, Optional, Protocol

from app.infrastructure.database.models import Goal


class GoalRepository(Protocol):
    async def create(
        self,
        user_id: int,
        context_prompt: str,
        target_date: Optional[date],
        weekly_active_days: Optional[int] = None,
        daily_time_minutes: Optional[int] = None,
        prior_knowledge_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None,
    ) -> Goal: ...

    async def list_by_user(self, user_id: int) -> List[Goal]: ...

    async def get_by_id(self, goal_id: int) -> Optional[Goal]: ...

    async def update(self, goal_id: int, **fields: Any) -> Goal: ...