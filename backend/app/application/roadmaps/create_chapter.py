from typing import Optional

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository


class ChapterNotFoundError(Exception):
    """Levantado quando after_chapter_id não corresponde a nenhum capítulo deste roadmap."""


class CannotInsertAfterCompletedChapterError(Exception):
    """Levantado ao tentar inserir um capítulo logo após um capítulo já
    concluído que NÃO é o último do roadmap. O desbloqueio automático só
    dispara quando o capítulo IMEDIATAMENTE anterior é concluído -- um
    capítulo concluído no passado não vai disparar de novo, então o capítulo
    novo ficaria "locked" pra sempre, preso entre dois capítulos já
    resolvidos."""


class CreateChapterUseCase:
    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(
        self,
        goal_id: int,
        user_id: int,
        title: str,
        after_chapter_id: Optional[int] = None,
    ):
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None or not roadmap.chapters:
            raise RoadmapNotFoundError("Nenhum roadmap ativo para este objetivo ainda.")

        last_chapter = roadmap.chapters[-1] 

        if after_chapter_id is None: 
            reference_chapter = last_chapter
        else:
            reference_chapter = next((c for c in roadmap.chapters if c.id == after_chapter_id), None)
            if reference_chapter is None:
                raise ChapterNotFoundError(f"Capítulo {after_chapter_id} não encontrado neste roadmap.")

        is_end_of_roadmap = reference_chapter.id == last_chapter.id

        if reference_chapter.status == "completed" and not is_end_of_roadmap:
            raise CannotInsertAfterCompletedChapterError(
                "Não é possível inserir um capítulo logo após um capítulo já concluído "
                "que não seja o último -- ele ficaria bloqueado para sempre. Insira depois "
                "do capítulo atual (em andamento) ou de um dos capítulos futuros."
            )

        # Só desbloqueia na hora se estiver entrando no fim de um roadmap já
        # todo concluído (mesma regra que o "adicionar no final" original já
        # seguia). Em qualquer outra posição o capítulo entra "locked" e é
        # desbloqueado sozinho no momento certo -- o order_index já cuida
        # disso via complete_chapter_and_unlock_next.
        new_status = "in_progress" if (is_end_of_roadmap and reference_chapter.status == "completed") else "locked"

        await self.roadmap_repository.insert_chapter_after(
            roadmap_id=roadmap.id,
            title=title,
            after_order_index=reference_chapter.order_index,
            status=new_status,
        )