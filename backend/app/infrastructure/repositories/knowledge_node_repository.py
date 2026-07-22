from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Goal, KnowledgeNode, KnowledgeReview, UserStats


class SQLAlchemyKnowledgeNodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_goal(self, goal_id: int) -> List[KnowledgeNode]:
        result = await self.session.execute(
            select(KnowledgeNode).where(KnowledgeNode.goal_id == goal_id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        goal_id: int,
        user_id: int,
        topic_name: str,
        embedding: List[float],
        next_review_date: date,
    ) -> KnowledgeNode:
        node = KnowledgeNode(
            goal_id=goal_id,
            user_id=user_id,
            topic_name=topic_name,
            embedding=embedding,
            next_review_date=next_review_date,
        )
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def get_due_for_user(self, user_id: int, today: date) -> List[Tuple[KnowledgeNode, Optional[str]]]:
        result = await self.session.execute(
            select(KnowledgeNode, Goal.title)
            .join(Goal, Goal.id == KnowledgeNode.goal_id)
            .where(KnowledgeNode.user_id == user_id, KnowledgeNode.next_review_date <= today)
            .order_by(KnowledgeNode.next_review_date)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_by_id(self, node_id: int) -> Optional[KnowledgeNode]:
        result = await self.session.execute(select(KnowledgeNode).where(KnowledgeNode.id == node_id))
        return result.scalar_one_or_none()

    async def record_review(
        self,
        node_id: int,
        difficulty: str,
        old_interval: int,
        new_interval: int,
        old_factor: float,
        new_factor: float,
        new_repetition_count: int,
        next_review_date: date,
    ) -> KnowledgeNode:
        node = await self.session.get(KnowledgeNode, node_id)
        if node is None:
            raise ValueError(f"Knowledge node {node_id} não encontrado.")

        node.interval_days = new_interval
        node.easiness_factor = new_factor
        node.repetition_count = new_repetition_count
        node.next_review_date = next_review_date
        node.last_review_at = datetime.now(timezone.utc)

        review = KnowledgeReview(
            knowledge_node_id=node_id,
            difficulty=difficulty,
            old_interval=old_interval,
            new_interval=new_interval,
            old_factor=old_factor,
            new_factor=new_factor,
        )
        self.session.add(review)

        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        result = await self.session.execute(select(UserStats).where(UserStats.user_id == user_id))
        return result.scalar_one_or_none()

    async def apply_daily_review_bonus(
        self,
        user_id: int,
        total_xp: int,
        level: int,
        current_streak: int,
        max_streak: int,
        activity_date: date,
    ) -> None:
        stats = await self.get_user_stats(user_id)
        if stats is None:
            stats = UserStats(
                user_id=user_id,
                total_xp=total_xp,
                current_level=level,
                current_streak=current_streak,
                max_streak=max_streak,
                last_activity_date=activity_date,
            )
            self.session.add(stats)
        else:
            stats.total_xp = total_xp
            stats.current_level = level
            stats.current_streak = current_streak
            stats.max_streak = max_streak
            stats.last_activity_date = activity_date

        await self.session.commit()