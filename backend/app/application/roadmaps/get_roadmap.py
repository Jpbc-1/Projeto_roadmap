from typing import Set, Tuple

from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.mission_repository import MissionRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.database.models import Roadmap


class RoadmapNotFoundError(Exception):
    """Levantado quando o goal ainda não tem um roadmap ativo (geração
    pendente, rejeitada ou falhou)."""


class GetRoadmapUseCase:
    def __init__(
        self,
        goal_repository: GoalRepository,
        roadmap_repository: RoadmapRepository,
        mission_repository: MissionRepository,
    ):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository
        self.mission_repository = mission_repository

    async def execute(self, goal_id: int, user_id: int) -> Tuple[Roadmap, Set[int]]:
        from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError

        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None:
            raise RoadmapNotFoundError(
                "Nenhum roadmap ativo para este objetivo ainda "
                "(pode estar sendo gerado, ter sido rejeitado, ou falhado)."
            )

        all_mission_ids = [mission.id for chapter in roadmap.chapters for mission in chapter.missions]
        completed_mission_ids = await self.mission_repository.get_completed_mission_ids(
            all_mission_ids, user_id
        )

        return roadmap, completed_mission_ids