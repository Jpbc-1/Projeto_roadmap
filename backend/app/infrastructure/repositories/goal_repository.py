from datetime import date
from typing import Any, List, Literal, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Goal


class SQLAlchemyGoalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        context_prompt: str,
        target_date: Optional[date],
        weekly_active_days: Optional[int] = None,
        daily_time_minutes: Optional[int] = None,
        prior_knowledge_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None,
    ) -> Goal:
        goal = Goal(
            user_id=user_id,
            title=None, 
            context_prompt=context_prompt,
            target_date=target_date,
            status="active",
            generation_status="pending",
            weekly_active_days=weekly_active_days,
            daily_time_minutes=daily_time_minutes,
            prior_knowledge_level=prior_knowledge_level,
        )
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def list_by_user(self, user_id: int) -> List[Goal]:
        result = await self.session.execute(
            select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, goal_id: int) -> Optional[Goal]:
        result = await self.session.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def update(self, goal_id: int, **fields: Any) -> Goal:
        goal = await self.get_by_id(goal_id)
        if goal is None:
            raise ValueError(f"Goal {goal_id} não encontrado para atualização.")

        for field_name, value in fields.items():
            setattr(goal, field_name, value)

        await self.session.commit()
        await self.session.refresh(goal)
        return goal