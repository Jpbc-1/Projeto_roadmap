from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Set

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
        carregados (para evitar N+1 queries ao montar a resposta)."""
        ...

    async def append_chapters(
        self,
        roadmap_id: int,
        chapters_data: List[Dict[str, Any]],
        starting_order_index: int,
        unlock_first_chapter: bool,
        ai_generation_log: Dict[str, Any],
    ) -> None:
        """Modo ESTENDER: adiciona uma nova leva de capítulos ao final de um
        roadmap existente (usado quando não sobra nenhum capítulo 'locked')."""
        ...

    async def get_chapter_ids_with_executions(self, chapter_ids: List[int]) -> Set[int]:
        """Checagem de segurança: entre os ids informados, quais têm
        qualquer missão já executada (não podem ser apagados)."""
        ...

    async def replace_locked_chapters(
        self,
        roadmap_id: int,
        chapter_ids_to_delete: List[int],
        chapters_data: List[Dict[str, Any]],
        starting_order_index: int,
        ai_generation_log: Dict[str, Any],
    ) -> None:
        """Modo REESCREVER: apaga capítulos 'locked' pendentes e insere
        novos no lugar deles (usado quando ainda existem capítulos não
        alcançados, evitando duplicação de conteúdo)."""
        ...

    async def get_pending_mission_ids(self, chapter_id: int, user_id: int) -> List[int]:
        """Missões do capítulo que o usuário ainda NÃO concluiu -- são as
        únicas que podem ser regeneradas com segurança."""
        ...

    async def get_chapter_reflections(
        self, chapter_id: int, user_id: int, since: Optional[datetime] = None
    ) -> List[Dict[str, str]]:
        """Reflexões (Diário da Evolução) que o usuário deixou nas missões
        já concluídas desse capítulo, para alimentar a adaptação. Se
        'since' for informado, considera só reflexões de missões concluídas
        DEPOIS desse momento -- evita reenviar à IA algo que uma adaptação
        anterior já processou."""
        ...

    async def count_completed_chapters(self, roadmap_id: int) -> int:
        """Quantos capítulos desse roadmap já estão com status 'completed'
        -- usado para decidir quando a triagem automática deve rodar."""
        ...

    async def get_reflections_for_chapters(
        self, chapter_ids: List[int], user_id: int
    ) -> List[Dict[str, str]]:
        """Reflexões de várias missões de vários capítulos de uma vez
        (usado pela triagem automática, que olha os últimos N capítulos)."""
        ...

    async def get_chapters_by_roadmap(self, roadmap_id: int) -> List[Any]:
        """Lista os capítulos de um roadmap (usado pela triagem automática
        para identificar os últimos capítulos concluídos)."""
        ...

    async def get_missions_by_chapter(self, chapter_id: int) -> List[Any]:
        """Lista as missões de um capítulo, com título e descrição --
        usado pela extração de conceitos do Mapa do Conhecimento."""
        ...

    async def split_chapter_with_new(
        self,
        roadmap_id: int,
        chapter_id: int,
        mission_ids_to_delete: List[int],
        new_chapter_title: str,
        new_chapter_order_index: int,
        new_chapter_missions: List[Dict[str, Any]],
    ) -> None:
        """Fecha o capítulo em andamento no que já foi concluído (apagando
        as missões pendentes dele) e cria um capítulo NOVO logo em seguida
        com o conteúdo ajustado -- usado quando a adaptação muda de rumo o
        suficiente para não fazer mais sentido continuar no mesmo capítulo."""
        ...