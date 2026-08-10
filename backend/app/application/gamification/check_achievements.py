from typing import List

from app.domain.repositories.achievement_repository import AchievementRepository
from app.domain.services.achievement_rules import AchievementProgress, conditions_met_for
from app.infrastructure.database.models import Achievement


class CheckAchievementsUseCase:
    """
    Roda depois de qualquer evento que PODE ter desbloqueado um marco --
    hoje só é chamado no fim de CompleteMissionUseCase (é onde
    missão/capítulo/objetivo/streak se cruzam), mas não depende disso:
    só recebe user_id + o streak atual (quem chama já tem calculado, ver
    complete_mission.py), e calcula as próprias contagens.
    """

    def __init__(self, achievement_repository: AchievementRepository):
        self.achievement_repository = achievement_repository

    async def execute(self, user_id: int, current_streak: int) -> List[Achievement]:
        progress = AchievementProgress(
            total_missions_completed=await self.achievement_repository.count_completed_missions(user_id),
            total_chapters_completed=await self.achievement_repository.count_completed_chapters(user_id),
            total_goals_completed=await self.achievement_repository.count_completed_goals(user_id),
            current_streak=current_streak,
        )

        newly_unlocked: List[Achievement] = []
        for condition in conditions_met_for(progress):
            achievement = await self.achievement_repository.get_by_condition(condition)
            if achievement is None:
                continue  

            if await self.achievement_repository.has_unlocked(user_id, achievement.id):
                continue

            await self.achievement_repository.unlock(user_id, achievement.id)
            newly_unlocked.append(achievement)

        return newly_unlocked
