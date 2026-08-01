from typing import Any, Dict

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository


class NoPendingAdaptationError(Exception):
    """Levantado quando não há nenhuma proposta de operação pendente pra
    confirmar ou rejeitar (ex: endpoint chamado duas vezes, ou sem nunca
    ter havido uma proposta)."""


class AdaptationOperationNoLongerValidError(Exception):
    """Levantado quando a proposta pendente não pode mais ser aplicada com
    segurança -- o capítulo-alvo foi concluído, travado ou deixou de
    existir no tempo entre a proposta (POST /adapt) e a confirmação (POST
    /adapt/confirm). A proposta é descartada como efeito colateral de
    levantar este erro (não fica "presa" pendente pra sempre, já que
    confirmar de novo nunca vai funcionar enquanto essa condição persistir)."""


async def _get_authorized_roadmap(goal_repository, roadmap_repository, goal_id: int, user_id: int):
    goal = await goal_repository.get_by_id(goal_id)
    if goal is None:
        raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
    if goal.user_id != user_id:
        raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

    roadmap = await roadmap_repository.get_active_by_goal(goal_id)
    if roadmap is None or not roadmap.pending_adaptation:
        raise NoPendingAdaptationError("Não há nenhuma alteração pendente de confirmação.")
    return roadmap


def _find_valid_target_chapter(roadmap, operation: Dict[str, Any]):
    """Mesma validação que ProposeChapterOperationUseCase já fez na hora de
    propor -- refeita aqui porque o estado pode ter mudado nesse meio tempo
    (a pessoa pode ter concluído o capítulo, ou travado ele, entre o
    POST /adapt e o POST /adapt/confirm). Devolve o capítulo se ainda for
    seguro aplicar a operação nele, ou None se não for."""
    target_chapter = next(
        (c for c in roadmap.chapters if c.id == operation.get("target_chapter_id")), None
    )
    if target_chapter is None:
        return None
    if target_chapter.status == "completed" or target_chapter.is_locked_from_ai:
        return None
    return target_chapter


class ConfirmAdaptationUseCase:
    """Aplica de fato a operação que ProposeChapterOperationUseCase deixou
    pendente em roadmap.pending_adaptation -- é só AQUI que o banco muda,
    depois do usuário ver o resumo ("Reescrever o Capítulo 2...") e topar."""

    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(self, goal_id: int, user_id: int) -> None:
        roadmap = await _get_authorized_roadmap(self.goal_repository, self.roadmap_repository, goal_id, user_id)
        operation = roadmap.pending_adaptation
        new_chapter = operation.get("new_chapter") or {}
        missions_data = new_chapter.get("missions") or []

        target_chapter = _find_valid_target_chapter(roadmap, operation)
        if target_chapter is None:
            # A proposta não pode mais ser aplicada -- descarta em vez de
            # deixar "presa" pendente pra sempre, e avisa quem chamou (o
            # endpoint deve devolver um erro real, nunca "sucesso").
            await self.roadmap_repository.clear_pending_adaptation(roadmap.id)
            raise AdaptationOperationNoLongerValidError(
                "O capítulo dessa proposta mudou de estado (foi concluído ou travado) "
                "desde que a alteração foi sugerida. Peça a adaptação de novo."
            )

        if operation.get("type") == "replace_chapter":
            await self.roadmap_repository.replace_chapter_content(
                chapter_id=target_chapter.id,
                title=new_chapter.get("title", ""),
                missions_data=missions_data,
            )
        elif operation.get("type") == "insert_chapter":
            await self.roadmap_repository.insert_full_chapter_after(
                roadmap_id=roadmap.id,
                after_order_index=target_chapter.order_index,
                title=new_chapter.get("title", ""),
                missions_data=missions_data,
            )
        else:
            # Formato de operação desconhecido (não deveria acontecer, já
            # que só ProposeChapterOperationUseCase escreve esse campo, mas
            # não silencia isso como "sucesso" se acontecer).
            await self.roadmap_repository.clear_pending_adaptation(roadmap.id)
            raise AdaptationOperationNoLongerValidError(
                f"Tipo de operação pendente desconhecido: {operation.get('type')!r}."
            )

        await self.roadmap_repository.clear_pending_adaptation(roadmap.id)


class RejectAdaptationUseCase:
    """Só descarta a proposta pendente -- nenhuma mudança é feita nos
    capítulos/missões reais, o roadmap continua exatamente como estava."""

    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(self, goal_id: int, user_id: int) -> None:
        roadmap = await _get_authorized_roadmap(self.goal_repository, self.roadmap_repository, goal_id, user_id)
        await self.roadmap_repository.clear_pending_adaptation(roadmap.id)
