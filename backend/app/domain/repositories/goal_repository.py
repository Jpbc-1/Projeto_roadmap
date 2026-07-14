from datetime import date
from typing import Any, List, Optional, Protocol

from app.infrastructure.database.models import Goal


class GoalRepository(Protocol):
    async def create(
        self,
        user_id: int,
        context_prompt: str,
        target_date: Optional[date],
    ) -> Goal: ...

    async def list_by_user(self, user_id: int) -> List[Goal]: ...

    async def get_by_id(self, goal_id: int) -> Optional[Goal]: ...

    async def update(self, goal_id: int, **fields: Any) -> Goal: ...