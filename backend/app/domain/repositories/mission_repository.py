from datetime import date
from typing import List, Optional, Protocol, Set

from app.infrastructure.database.models import Mission, MissionExecution, UserStats


class MissionExecutionConflictError(Exception):
    """Levantado por persist_completion quando já existe uma execução para
    essa missão+usuário -- detectado pela constraint única do banco
    (uq_mission_execution_user), não só pelo check em Python (has_execution),
    que sozinho não é atômico contra duas requisições concorrentes (duplo
    toque, retry de rede) passando pelo check ao mesmo tempo."""


class MissionRepository(Protocol):
    async def get_by_id_with_hierarchy(self, mission_id: int) -> Optional[Mission]:
        """Busca a missão já carregando chapter -> roadmap -> goal, para
        permitir a checagem de posse (é do usuário logado?) sem N+1 queries."""
        ...

    async def has_execution(self, mission_id: int, user_id: int) -> bool: ...

    async def get_mission_ids_in_chapter(self, chapter_id: int) -> List[int]: ...

    async def get_completed_mission_ids(self, mission_ids: List[int], user_id: int) -> Set[int]: ...

    async def get_next_chapter_id(self, roadmap_id: int, current_order_index: int) -> Optional[int]: ...

    async def get_user_stats(self, user_id: int) -> Optional[UserStats]: ...

    async def lock_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Igual a get_user_stats, mas com SELECT...FOR UPDATE: trava a
        linha (se ela já existir) dentro da transação atual até o próximo
        commit/rollback desta sessão. Precisa ser chamado ANTES de calcular
        o novo XP/streak (calculate_streak_update), e a mesma sessão tem
        que seguir sem commit no meio até persist_completion -- é isso que
        serializa duas conclusões de missões DIFERENTES quase simultâneas
        do mesmo usuário, evitando que uma escrita sobrescreva a outra
        (lost update). Devolve None se o usuário ainda não tem UserStats
        (primeira missão concluída na conta) -- não tem linha pra travar
        ainda; esse caso específico (dois "primeiro ever" concorrentes)
        não é coberto por este lock, só o caso comum de quem já tem stats.
        """
        ...

    async def persist_completion(
        self,
        mission_id: int,
        user_id: int,
        xp_rewarded: int,
        user_reflection: Optional[str],
        chapter_id_to_complete: Optional[int],
        next_chapter_id_to_unlock: Optional[int],
        new_total_xp: int,
        new_level: int,
        new_current_streak: int,
        new_max_streak: int,
        activity_date: date,
        difficulty_rating: Optional[str] = None,
        satisfaction_rating: Optional[int] = None,
    ) -> MissionExecution:
        """Grava TUDO (execução + status de capítulos + estatísticas de
        gamificação) numa única transação atômica. Os valores já vêm
        decididos por quem chama -- este método só persiste.

        difficulty_rating/satisfaction_rating são opcionais (o front decide
        quando pedir) e alimentam o contexto da adaptação depois.

        Levanta MissionExecutionConflictError se essa missão+usuário já
        tiver uma execução (corrida entre requisições concorrentes) -- quem
        chama deve tratar isso como "já concluída", não como erro real."""
        ...