from typing import List, Optional, Protocol

from app.infrastructure.database.models import KnowledgeNode


class KnowledgeNodeRepository(Protocol):
    """Só o CONCEITO (ver docstring de KnowledgeNode em models.py) --
    estado de repetição espaçada/revisão agora vive em FlashcardRepository,
    não aqui."""

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
        importance_score: int,
        mission_id: Optional[int] = None,
    ) -> KnowledgeNode: ...

    async def get_by_id(self, node_id: int) -> Optional[KnowledgeNode]: ...
