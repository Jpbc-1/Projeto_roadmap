from typing import List, Protocol

from app.infrastructure.database.models import GoalRecommendation


class RecommendationRepository(Protocol):
    async def bulk_create(self, goal_id: int, recommendations: List[dict]) -> List[GoalRecommendation]:
        """Persiste as recomendações geradas junto com o roadmap inicial.
        Cada dict deve ter name/description/is_paid -- entradas malformadas
        são ignoradas em vez de derrubar a geração inteira do roadmap."""
        ...

    async def get_by_goal(self, goal_id: int) -> List[GoalRecommendation]: ...
