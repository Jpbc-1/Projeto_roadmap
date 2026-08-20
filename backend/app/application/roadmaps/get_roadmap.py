from typing import Set, Tuple

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.mission_repository import MissionRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.database.models import Roadmap


class RoadmapNotFoundError(Exception):
    """Levantado quando o goal ainda não tem um roadmap ativo. A mensagem
    já reflete o generation_status de verdade do goal (pending/
    awaiting_info/rejected/failed) -- antes disso era um texto genérico
    hedge ("pode estar sendo gerado, rejeitado ou falhado") que não dizia
    qual dos três realmente aconteceu, obrigando o front a adivinhar."""


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
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None:
            status_messages = {
                "pending": "Seu roadmap ainda está sendo gerado -- isso leva alguns segundos.",
                "awaiting_info": "Responda as perguntas pendentes (GET /goals/{id}) para continuar a geração.",
                "rejected": goal.generation_error or "Este objetivo foi rejeitado na moderação.",
                "failed": goal.generation_error or "A geração do roadmap falhou. Tente criar o objetivo de novo.",
                "deleted": "O roadmap deste objetivo foi apagado.",
            }
            raise RoadmapNotFoundError(
                status_messages.get(
                    goal.generation_status,
                    "Nenhum roadmap ativo para este objetivo ainda.",
                )
            )

        all_mission_ids = [mission.id for chapter in roadmap.chapters for mission in chapter.missions]
        completed_mission_ids = await self.mission_repository.get_completed_mission_ids(
            all_mission_ids, user_id
        )

        return roadmap, completed_mission_ids