from datetime import date
from typing import List, Optional, Protocol, Tuple

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

    async def get_due_for_user(
        self, user_id: int, today: date, limit: int, offset: int
    ) -> List[Tuple[KnowledgeNode, Optional[str]]]:
        """Nós com revisão pendente (next_review_date <= today), já com o
        título do goal correspondente (evita N+1 no endpoint)."""
        ...

    async def count_due_for_user(self, user_id: int, today: date) -> int:
        """Quantos nós têm revisão pendente -- COUNT direto, não a lista
        inteira. Ver docstring da implementação SQLAlchemy pro motivo de
        isso ser um método separado de get_due_for_user, não a mesma
        chamada com len()."""
        ...

    async def get_by_id(self, node_id: int) -> Optional[KnowledgeNode]: ...

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
        """Aplica o resultado de uma revisão: atualiza o nó (novo intervalo,
        fator, contagem, próxima data) E grava uma linha de auditoria em
        knowledge_reviews, numa única transação."""
        ...

    async def get_user_stats(self, user_id: int):
        """Reaproveita a mesma tabela user_stats das missões -- XP e streak
        são um sistema único, não um contador separado por funcionalidade."""
        ...

    async def apply_daily_review_bonus(
        self,
        user_id: int,
        total_xp: int,
        level: int,
        current_streak: int,
        max_streak: int,
        activity_date: date,
    ) -> None:
        """Aplica o bônus por ter zerado a fila de revisões do dia."""
        ...