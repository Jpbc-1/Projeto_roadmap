from typing import Any, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import GoalRecommendation


def _coerce_bool(value: Any, default: bool) -> bool:
    """Mesma razão do helper igual em roadmap_repository.py: a geração do
    roadmap (e as recomendações, geradas na mesma chamada) não usa
    response_schema, então 'is_paid' vem só por instrução de prompt, sem
    garantia de tipo. bool("false") seria True em Python puro."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return default


class SQLAlchemyRecommendationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, goal_id: int, recommendations: List[dict]) -> List[GoalRecommendation]:
        created = []
        for item in recommendations:
            name = str(item.get("name") or "").strip()
            description = str(item.get("description") or "").strip()
            if not name or not description:
                continue  # entrada malformada da IA -- ignora em vez de quebrar tudo
            recommendation = GoalRecommendation(
                goal_id=goal_id,
                name=name[:150],
                description=description,
                is_paid=_coerce_bool(item.get("is_paid"), default=False),
            )
            self.session.add(recommendation)
            created.append(recommendation)

        if created:
            await self.session.commit()
            for recommendation in created:
                await self.session.refresh(recommendation)
        return created

    async def get_by_goal(self, goal_id: int) -> List[GoalRecommendation]:
        result = await self.session.execute(
            select(GoalRecommendation).where(GoalRecommendation.goal_id == goal_id)
        )
        return list(result.scalars().all())
