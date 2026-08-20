from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import KnowledgeNode


class SQLAlchemyKnowledgeNodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_goal(self, goal_id: int) -> List[KnowledgeNode]:
        result = await self.session.execute(select(KnowledgeNode).where(KnowledgeNode.goal_id == goal_id))
        return list(result.scalars().all())

    async def create(
        self,
        goal_id: int,
        user_id: int,
        topic_name: str,
        embedding: List[float],
        importance_score: int,
        mission_id: Optional[int] = None,
    ) -> KnowledgeNode:
        node = KnowledgeNode(
            goal_id=goal_id,
            user_id=user_id,
            mission_id=mission_id,
            topic_name=topic_name,
            embedding=embedding,
            importance_score=importance_score,
        )
        self.session.add(node)
        await self.session.commit()
        await self.session.refresh(node)
        return node

    async def get_by_id(self, node_id: int) -> Optional[KnowledgeNode]:
        return await self.session.get(KnowledgeNode, node_id)
