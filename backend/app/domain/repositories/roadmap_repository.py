from typing import Any, Dict, List, Optional, Protocol

from app.infrastructure.database.models import Roadmap


class RoadmapRepository(Protocol):
    async def create_full_roadmap(
        self,
        goal_id: int,
        version: int,
        ai_generation_log: Dict[str, Any],
        chapters_data: List[Dict[str, Any]],
    ) -> Roadmap: ...

    async def get_active_by_goal(self, goal_id: int) -> Optional[Roadmap]:
        """Busca o roadmap ativo de um goal, já com capítulos e missões
        carregados."""
        ...