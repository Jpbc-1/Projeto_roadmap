from datetime import date, timedelta
from typing import Optional

from app.domain.repositories.mission_repository import MissionRepository
from app.infrastructure.database.models import MissionExecution


class MissionNotFoundError(Exception):
    """Levantado quando a missão não existe."""


class MissionAccessDeniedError(Exception):
    """Levantado quando a missão existe, mas pertence a outro usuário."""


class MissionAlreadyCompletedError(Exception):
    """Levantado quando o usuário já concluiu essa missão antes."""


class CompleteMissionUseCase:
    def __init__(self, mission_repository: MissionRepository):
        self.mission_repository = mission_repository

    async def execute(
        self,
        mission_id: int,
        user_id: int,
        user_reflection: Optional[str],
    ) -> MissionExecution:
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

        new_total_xp, new_streak, new_max_streak, activity_date = await self._calculate_gamification(
            user_id=user_id,
            xp_rewarded=xp_rewarded,
        )
        new_level = self._calculate_level(new_total_xp)

        return await self.mission_repository.persist_completion(
            mission_id=mission_id,
            user_id=user_id,
            xp_rewarded=xp_rewarded,
            user_reflection=user_reflection,
            chapter_id_to_complete=chapter_id_to_complete,
            next_chapter_id_to_unlock=next_chapter_id_to_unlock,
            new_total_xp=new_total_xp,
            new_level=new_level,
            new_current_streak=new_streak,
            new_max_streak=new_max_streak,
            activity_date=activity_date,
        )

    async def _check_chapter_progress(self, mission, user_id: int, mission_id: int):
        """Decide se, com essa missão sendo concluída agora, o capítulo
        inteiro fica completo -- e se sim, qual é o próximo a desbloquear."""
        mission_ids = await self.mission_repository.get_mission_ids_in_chapter(mission.chapter_id)
        completed_ids = await self.mission_repository.get_completed_mission_ids(mission_ids, user_id)
        completed_ids.add(mission_id)  # esta missão está prestes a ser concluída

        chapter_will_be_completed = set(mission_ids) <= completed_ids

        if not chapter_will_be_completed:
            return None, None

        next_chapter_id = await self.mission_repository.get_next_chapter_id(
            roadmap_id=mission.chapter.roadmap_id,
            current_order_index=mission.chapter.order_index,
        )
        return mission.chapter_id, next_chapter_id

    async def _calculate_gamification(self, user_id: int, xp_rewarded: int):
        """Decide XP total, streak atual e streak máximo, com base no
        histórico de atividade do usuário."""
        stats = await self.mission_repository.get_user_stats(user_id)
        today = date.today()

        if stats is None:
            return xp_rewarded, 1, 1, today

        if stats.last_activity_date == today:
            new_streak = stats.current_streak  # já ativo hoje, streak não muda
        elif stats.last_activity_date == today - timedelta(days=1):
            new_streak = stats.current_streak + 1  # ativo ontem -> streak continua
        else:
            new_streak = 1  # quebrou o streak -> recomeça

        new_total_xp = stats.total_xp + xp_rewarded
        new_max_streak = max(stats.max_streak, new_streak)
        return new_total_xp, new_streak, new_max_streak, today

    @staticmethod
    def _calculate_xp(estimated_minutes: Optional[int]) -> int:
        """Fórmula simples de XP para o MVP: 10 pontos base + 1 por minuto
        estimado da missão. Ajustável depois conforme balanceamento de jogo."""
        return 10 + (estimated_minutes or 0)

    @staticmethod
    def _calculate_level(total_xp: int) -> int:
        """Fórmula simples: a cada 100 XP, sobe 1 nível."""
        return 1 + total_xp // 100