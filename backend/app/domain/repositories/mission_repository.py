from datetime import date
from typing import List, Optional, Protocol, Set

from app.infrastructure.database.models import Mission, MissionExecution, UserStats


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
    ) -> MissionExecution:
        """Grava TUDO (execução + status de capítulos + estatísticas de
        gamificação) numa única transação atômica. Os valores já vêm
        decididos por quem chama -- este método só persiste."""
        ...