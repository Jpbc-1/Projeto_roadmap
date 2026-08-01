from app.domain.repositories.mission_repository import MissionRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository


class MissionNotFoundError(Exception):
    """Levantado quando a missão não existe."""


class MissionAccessDeniedError(Exception):
    """Levantado quando a missão existe, mas pertence a outro usuário."""


class MissionHasExecutionError(Exception):
    """Levantado ao tentar apagar uma missão já concluída.

    Regra dura, não negociável: se isso fosse permitido, seria possível
    completar uma missão (ganhar XP), apagá-la, recriar uma igual e
    completar de novo -- XP infinito em loop. Isso não é uma questão de
    confiar ou não no usuário, é uma garantia estrutural do sistema."""


class DeleteMissionUseCase:
    def __init__(self, mission_repository: MissionRepository, roadmap_repository: RoadmapRepository):
        self.mission_repository = mission_repository
        self.roadmap_repository = roadmap_repository

    async def execute(self, mission_id: int, user_id: int) -> None:
        mission = await self.mission_repository.get_by_id_with_hierarchy(mission_id)
        if mission is None:
            raise MissionNotFoundError(f"Missão {mission_id} não encontrada.")
        if mission.chapter.roadmap.goal.user_id != user_id:
            raise MissionAccessDeniedError("Você não tem acesso a esta missão.")

        if await self.mission_repository.has_execution(mission_id, user_id):
            raise MissionHasExecutionError("Não é possível excluir uma missão já concluída.")

        chapter = mission.chapter
        await self.roadmap_repository.delete_mission(mission_id)

        remaining_mission_ids = await self.mission_repository.get_mission_ids_in_chapter(chapter.id)
        if not remaining_mission_ids:
            return

        completed_ids = await self.mission_repository.get_completed_mission_ids(remaining_mission_ids, user_id)
        chapter_now_complete = set(remaining_mission_ids) <= completed_ids

        if chapter_now_complete and chapter.status != "completed":
            next_chapter_id = await self.mission_repository.get_next_chapter_id(
                roadmap_id=chapter.roadmap_id,
                current_order_index=chapter.order_index,
            )
            await self.roadmap_repository.complete_chapter_and_unlock_next(chapter.id, next_chapter_id)