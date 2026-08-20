from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIUsageLog,
    BackgroundJob,
    CalendarEvent,
    Goal,
    GoalRecommendation,
    KnowledgeNode,
    KnowledgeReview,
    Mission,
    MissionExecution,
    OAuthAccount,
    Reminder,
    Roadmap,
    RoadmapChapter,
    User,
    UserAchievement,
    UserPushToken,
    UserStats,
)


class SQLAlchemyUserRepository:
    """Implementação real do UserRepository, usando SQLAlchemy + Postgres."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, email: str, username: str, password_hash: Optional[str] = None) -> User:
        user = User(email=email, password_hash=password_hash, username=username)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def try_deduct_credits(self, user_id: int, amount: int) -> bool:
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id, User.credits_remaining >= amount)
            .values(credits_remaining=User.credits_remaining - amount)
        )
        await self.session.commit()
        return result.rowcount > 0

    async def refund_credits(self, user_id: int, amount: int) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(credits_remaining=User.credits_remaining + amount)
        )
        await self.session.commit()

    async def delete_account(self, user_id: int) -> None:
        goal_ids_subquery = select(Goal.id).where(Goal.user_id == user_id).scalar_subquery()
        roadmap_ids_subquery = select(Roadmap.id).where(Roadmap.goal_id.in_(goal_ids_subquery)).scalar_subquery()
        chapter_ids_subquery = (
            select(RoadmapChapter.id).where(RoadmapChapter.roadmap_id.in_(roadmap_ids_subquery)).scalar_subquery()
        )
        knowledge_node_ids_subquery = (
            select(KnowledgeNode.id).where(KnowledgeNode.user_id == user_id).scalar_subquery()
        )

        await self.session.execute(
            delete(KnowledgeReview).where(KnowledgeReview.knowledge_node_id.in_(knowledge_node_ids_subquery))
        )
        await self.session.execute(delete(MissionExecution).where(MissionExecution.user_id == user_id))

        await self.session.execute(delete(Mission).where(Mission.chapter_id.in_(chapter_ids_subquery)))
        await self.session.execute(delete(RoadmapChapter).where(RoadmapChapter.roadmap_id.in_(roadmap_ids_subquery)))
        await self.session.execute(delete(Roadmap).where(Roadmap.goal_id.in_(goal_ids_subquery)))
        await self.session.execute(
            delete(GoalRecommendation).where(GoalRecommendation.goal_id.in_(goal_ids_subquery))
        )
        await self.session.execute(delete(KnowledgeNode).where(KnowledgeNode.user_id == user_id))
        await self.session.execute(delete(Goal).where(Goal.user_id == user_id))

        await self.session.execute(delete(UserAchievement).where(UserAchievement.user_id == user_id))
        await self.session.execute(delete(UserStats).where(UserStats.user_id == user_id))
        await self.session.execute(delete(Reminder).where(Reminder.user_id == user_id))
        await self.session.execute(delete(CalendarEvent).where(CalendarEvent.user_id == user_id))
        await self.session.execute(delete(OAuthAccount).where(OAuthAccount.user_id == user_id))
        await self.session.execute(delete(UserPushToken).where(UserPushToken.user_id == user_id))
        await self.session.execute(delete(BackgroundJob).where(BackgroundJob.user_id == user_id))
        await self.session.execute(delete(AIUsageLog).where(AIUsageLog.user_id == user_id))

        await self.session.execute(delete(User).where(User.id == user_id))

        await self.session.commit()