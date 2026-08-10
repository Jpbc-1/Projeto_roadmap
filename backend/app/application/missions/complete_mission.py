from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from app.application.gamification.streak import calculate_streak_update
from app.domain.repositories.mission_repository import MissionExecutionConflictError, MissionRepository
from app.infrastructure.database.models import MissionExecution


class MissionNotFoundError(Exception):
    """Levantado quando a missão não existe."""


class MissionAccessDeniedError(Exception):
    """Levantado quando a missão existe, mas pertence a outro usuário."""


class MissionAlreadyCompletedError(Exception):
    """Levantado quando o usuário já concluiu essa missão antes."""


@dataclass
class MissionCompletionResult:
    execution: MissionExecution
    roadmap_id: int
    goal_id: int
    chapter_completed_id: Optional[int]
    current_streak: int
    goal_completed: bool


class CompleteMissionUseCase:
    def __init__(self, mission_repository: MissionRepository):
        self.mission_repository = mission_repository

    async def execute(
        self,
        mission_id: int,
        user_id: int,
        user_reflection: Optional[str],
        user_timezone: str,
        difficulty_rating: Optional[str] = None,
        satisfaction_rating: Optional[int] = None,
    ) -> MissionCompletionResult:
        mission = await self.mission_repository.get_by_id_with_hierarchy(mission_id)
        if mission is None:
            raise MissionNotFoundError(f"Missão {mission_id} não encontrada.")

        if mission.chapter.roadmap.goal.user_id != user_id:
            raise MissionAccessDeniedError("Você não tem acesso a esta missão.")

        if await self.mission_repository.has_execution(mission_id, user_id):
            raise MissionAlreadyCompletedError("Esta missão já foi concluída.")

        xp_rewarded = self._calculate_xp(mission.estimated_minutes)

        chapter_id_to_complete, next_chapter_id_to_unlock = await self._check_chapter_progress(
            mission=mission,
            user_id=user_id,
            mission_id=mission_id,
        )

        stats = await self.mission_repository.get_user_stats(user_id)
        try:
            today_for_user = datetime.now(ZoneInfo(user_timezone)).date()
        except Exception:
            today_for_user = date.today() 
        streak_update = calculate_streak_update(stats, xp_to_add=xp_rewarded, today=today_for_user)

        try:
            execution = await self.mission_repository.persist_completion(
                mission_id=mission_id,
                user_id=user_id,
                xp_rewarded=xp_rewarded,
                user_reflection=user_reflection,
                chapter_id_to_complete=chapter_id_to_complete,
                next_chapter_id_to_unlock=next_chapter_id_to_unlock,
                new_total_xp=streak_update.new_total_xp,
                new_level=streak_update.new_level,
                new_current_streak=streak_update.new_current_streak,
                new_max_streak=streak_update.new_max_streak,
                activity_date=streak_update.activity_date,
                difficulty_rating=difficulty_rating,
                satisfaction_rating=satisfaction_rating,
            )
        except MissionExecutionConflictError:
            raise MissionAlreadyCompletedError("Esta missão já foi concluída.")

        return MissionCompletionResult(
            execution=execution,
            roadmap_id=mission.chapter.roadmap_id,
            goal_id=mission.chapter.roadmap.goal_id,
            chapter_completed_id=chapter_id_to_complete,
            current_streak=streak_update.new_current_streak,
            goal_completed=chapter_id_to_complete is not None and next_chapter_id_to_unlock is None,
        )

    async def _check_chapter_progress(self, mission, user_id: int, mission_id: int):
        """Decide se, com essa missão sendo concluída agora, o capítulo
        inteiro fica completo -- e se sim, qual é o próximo a desbloquear."""
        mission_ids = await self.mission_repository.get_mission_ids_in_chapter(mission.chapter_id)
        completed_ids = await self.mission_repository.get_completed_mission_ids(mission_ids, user_id)
        completed_ids.add(mission_id)  

        chapter_will_be_completed = set(mission_ids) <= completed_ids

        if not chapter_will_be_completed:
            return None, None

        next_chapter_id = await self.mission_repository.get_next_chapter_id(
            roadmap_id=mission.chapter.roadmap_id,
            current_order_index=mission.chapter.order_index,
        )
        return mission.chapter_id, next_chapter_id

    @staticmethod
    def _calculate_xp(estimated_minutes: Optional[int]) -> int:
        """Fórmula simples de XP para o MVP: 10 pontos base + 1 por minuto
        estimado da missão. Ajustável depois conforme balanceamento de jogo."""
        return 10 + (estimated_minutes or 0)