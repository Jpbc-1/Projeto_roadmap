from typing import Optional

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository
from app.infrastructure.database.models import Mission


class ChapterNotFoundError(Exception):
    """Levantado quando o capítulo informado não existe nesse roadmap."""


class ChapterAlreadyCompletedError(Exception):
    """Levantado ao tentar adicionar missão a um capítulo já concluído."""


class CreateMissionUseCase:
    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(
        self,
        goal_id: int,
        user_id: int,
        chapter_id: int,
        title: str,
        description: Optional[str],
        estimated_minutes: Optional[int],
    ) -> Mission:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None:
            raise RoadmapNotFoundError("Nenhum roadmap ativo para este objetivo ainda.")

        chapter = next((c for c in roadmap.chapters if c.id == chapter_id), None)
        if chapter is None:
            raise ChapterNotFoundError(f"Capítulo {chapter_id} não encontrado neste roadmap.")

        if chapter.status == "completed":
            raise ChapterAlreadyCompletedError("Não é possível adicionar missões a um capítulo já concluído.")

        return await self.roadmap_repository.add_mission_to_chapter(
            chapter_id=chapter_id,
            title=title,
            description=description,
            estimated_minutes=estimated_minutes,
        )