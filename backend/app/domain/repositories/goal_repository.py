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

    async def list_by_user(self, user_id: int, limit: int, offset: int) -> List[Goal]: ...

    async def get_by_id(self, goal_id: int) -> Optional[Goal]: ...

    async def update(self, goal_id: int, **fields: Any) -> Goal: ...

    async def rollback(self) -> None:
        """Desfaz qualquer mudança não commitada na sessão atual. Usado nos
        `except` de use cases em background (ex: GenerateRoadmapUseCase,
        IntakeGoalUseCase) antes de tentar gravar generation_status="failed"
        -- se a exceção capturada veio de uma falha de banco no meio de uma
        transação, a sessão fica "suja" e qualquer novo comando (incluindo
        esse próprio update de status) falharia sem esse rollback antes."""
        ...