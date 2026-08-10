from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    Achievement,
    Goal,
    MissionExecution,
    Roadmap,
    RoadmapChapter,
    UserAchievement,
)


class SQLAlchemyAchievementRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_completed_missions(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(MissionExecution.id)).where(MissionExecution.user_id == user_id)
        )
        return result.scalar_one()

    async def count_completed_chapters(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(RoadmapChapter.id))
            .join(Roadmap, Roadmap.id == RoadmapChapter.roadmap_id)
            .join(Goal, Goal.id == Roadmap.goal_id)
            .where(Goal.user_id == user_id, RoadmapChapter.status == "completed")
        )
        return result.scalar_one()

    async def count_completed_goals(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Goal.id)).where(Goal.user_id == user_id, Goal.status == "achieved")
        )
        return result.scalar_one()

    async def get_by_condition(self, required_condition: str) -> Optional[Achievement]:
        result = await self.session.execute(
            select(Achievement).where(Achievement.required_condition == required_condition)
        )
        return result.scalar_one_or_none()

    async def has_unlocked(self, user_id: int, achievement_id: int) -> bool:
        result = await self.session.execute(
            select(UserAchievement.id).where(
                UserAchievement.user_id == user_id, UserAchievement.achievement_id == achievement_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def unlock(self, user_id: int, achievement_id: int) -> UserAchievement:
        unlocked = UserAchievement(user_id=user_id, achievement_id=achievement_id)
        self.session.add(unlocked)
        await self.session.commit()
        await self.session.refresh(unlocked)
        return unlocked

    async def list_all(self) -> List[Achievement]:
        result = await self.session.execute(select(Achievement).order_by(Achievement.id))
        return list(result.scalars().all())

    async def list_unlocked_for_user(self, user_id: int) -> List[UserAchievement]:
        result = await self.session.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.unlocked_at.desc())
        )
        return list(result.scalars().all())
