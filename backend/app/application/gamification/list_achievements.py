from typing import List

from app.domain.repositories.achievement_repository import AchievementRepository
from app.infrastructure.database.models import Achievement


class ListAchievementsUseCase:
    def __init__(self, achievement_repository: AchievementRepository):
        self.achievement_repository = achievement_repository

    async def execute(self) -> List[Achievement]:
        return await self.achievement_repository.list_all()
