from typing import List

from app.domain.repositories.achievement_repository import AchievementRepository
from app.infrastructure.database.models import UserAchievement


class ListUserAchievementsUseCase:
    def __init__(self, achievement_repository: AchievementRepository):
        self.achievement_repository = achievement_repository

    async def execute(self, user_id: int, limit: int, offset: int) -> List[UserAchievement]:
        return await self.achievement_repository.list_unlocked_for_user(user_id, limit=limit, offset=offset)
