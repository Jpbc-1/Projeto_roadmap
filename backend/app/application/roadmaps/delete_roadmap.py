from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.application.roadmaps.get_roadmap import RoadmapNotFoundError
from app.domain.repositories.goal_repository import GoalRepository
from app.domain.repositories.roadmap_repository import RoadmapRepository


class DeleteRoadmapUseCase:
    """Apaga o roadmap ativo de um objetivo -- capítulos, missões e
    execuções vão junto (ver SQLAlchemyRoadmapRepository.delete_roadmap
    pra ordem exata). Reaproveita as MESMAS exceções de GetRoadmapUseCase
    (GoalNotFoundError/GoalAccessDeniedError/RoadmapNotFoundError) porque
    é literalmente a mesma resolução de acesso, só que terminando em
    DELETE em vez de leitura.

    Decisão de escopo: o Goal em si SOBREVIVE, só fica sem roadmap
    (generation_status vira "deleted", ver mensagem correspondente em
    get_roadmap.py) -- "excluir roadmap" é diferente de "excluir
    objetivo". Se um dia fizer sentido apagar o Goal inteiro (levando
    junto KnowledgeNode/GoalRecommendation ligados a ele), isso é outro
    use case, não uma extensão deste.

    Sem checagem de progresso/execuções concluídas de propósito: essa
    proteção (get_chapter_ids_with_executions) existe só pro fluxo de
    ADAPTAÇÃO automática/manual, pra IA não reescrever sozinha um capítulo
    que a pessoa já andou -- aqui é o próprio dono da conta pedindo
    explicitamente pra apagar, incluindo qualquer progresso registrado."""

    def __init__(self, goal_repository: GoalRepository, roadmap_repository: RoadmapRepository):
        self.goal_repository = goal_repository
        self.roadmap_repository = roadmap_repository

    async def execute(self, goal_id: int, user_id: int) -> None:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        roadmap = await self.roadmap_repository.get_active_by_goal(goal_id)
        if roadmap is None:
            raise RoadmapNotFoundError("Nenhum roadmap ativo para este objetivo ainda.")

        await self.roadmap_repository.delete_roadmap(roadmap.id)
        await self.goal_repository.update(goal_id, generation_status="deleted")
