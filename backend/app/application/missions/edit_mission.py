from typing import Optional

from app.domain.repositories.mission_repository import MissionRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.database.models import Mission


class MissionNotFoundError(Exception):
    """Levantado quando a missão não existe."""


class MissionAccessDeniedError(Exception):
    """Levantado quando a missão existe, mas pertence a outro usuário."""


class EditMissionUseCase:
    def __init__(self, mission_repository: MissionRepository, roadmap_repository: RoadmapRepository):
        self.mission_repository = mission_repository
        self.roadmap_repository = roadmap_repository

    async def execute(
        self,
        mission_id: int,
        user_id: int,
        title: Optional[str],
        description: Optional[str],
        estimated_minutes: Optional[int],
    ) -> Mission:
        mission = await self.mission_repository.get_by_id_with_hierarchy(mission_id)
        if mission is None:
            raise MissionNotFoundError(f"Missão {mission_id} não encontrada.")
        if mission.chapter.roadmap.goal.user_id != user_id:
            raise MissionAccessDeniedError("Você não tem acesso a esta missão.")

        fields = {}
        if title is not None:
            fields["title"] = title
        if description is not None:
            fields["description"] = description
        if estimated_minutes is not None:
            fields["estimated_minutes"] = estimated_minutes

        if not fields:
            return mission 

        return await self.roadmap_repository.update_mission(mission_id, **fields)