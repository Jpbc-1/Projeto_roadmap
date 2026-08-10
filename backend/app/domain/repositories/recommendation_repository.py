from typing import List, Protocol

from app.infrastructure.database.models import GoalRecommendation


class RecommendationRepository(Protocol):
    async def bulk_create(self, goal_id: int, recommendations: List[dict]) -> List[GoalRecommendation]:
        """Persiste as recomendações geradas junto com o roadmap inicial.
        Cada dict deve ter name/description/is_paid -- entradas malformadas
        são ignoradas em vez de derrubar a geração inteira do roadmap."""
        ...

    async def get_by_goal(self, goal_id: int) -> List[GoalRecommendation]: ...

    async def delete_by_goal(self, goal_id: int) -> None:
        """Apaga as recomendações antigas de um goal -- usado quando o
        capítulo 1 é substituído numa adaptação (o rumo do objetivo mudou
        tanto quanto se ele tivesse sido criado de novo, então as
        recomendações antigas, do rumo anterior, também precisam ser
        trocadas, igual o título já era)."""
        ...
