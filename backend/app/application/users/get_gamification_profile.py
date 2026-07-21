from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.repositories.mission_repository import MissionRepository
from app.infrastructure.database.models import User


@dataclass
class GamificationProfile:
    user_id: int
    username: Optional[str]
    email: str
    total_xp: int
    current_level: int
    current_streak: int
    max_streak: int
    last_activity_date: Optional[date]


class GetGamificationProfileUseCase:
    def __init__(self, mission_repository: MissionRepository):
        self.mission_repository = mission_repository

    async def execute(self, user: User) -> GamificationProfile:
        stats = await self.mission_repository.get_user_stats(user.id)

        return GamificationProfile(
            user_id=user.id,
            username=user.username,
            email=user.email,
            total_xp=stats.total_xp if stats else 0,
            current_level=stats.current_level if stats else 1,
            current_streak=stats.current_streak if stats else 0,
            max_streak=stats.max_streak if stats else 0,
            last_activity_date=stats.last_activity_date if stats else None,
        )