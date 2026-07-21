from datetime import date
from typing import List, Protocol

from app.infrastructure.database.models import KnowledgeNode


class KnowledgeNodeRepository(Protocol):
    async def get_by_goal(self, goal_id: int) -> List[KnowledgeNode]:
        """Todos os nós de conhecimento já registrados para esse goal --
        usado para comparar embeddings e evitar duplicatas semânticas."""
        ...

    async def create(
        self,
        goal_id: int,
        user_id: int,
        topic_name: str,
        embedding: List[float],
        next_review_date: date,
    ) -> KnowledgeNode: ...