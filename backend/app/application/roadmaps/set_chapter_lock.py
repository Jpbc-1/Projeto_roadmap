from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.roadmaps.create_chapter import ChapterNotFoundError
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository


class SetChapterLockUseCase:
    """Trava/destrava um capítulo contra mudanças da IA (campo
    is_locked_from_ai). Um capítulo travado nunca é escolhido como alvo de
    replace_chapter/insert_chapter pela adaptação -- ver
    ProposeChapterOperationUseCase, que revalida isso em código, não só
    confia no prompt."""

    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(self, goal_id: int, user_id: int, chapter_id: int, locked: bool) -> None:
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

        await self.roadmap_repository.set_chapter_lock(chapter_id, locked)
