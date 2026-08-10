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
    ) -> List[Dict[str, Any]]:
        """Reflexões (Diário da Evolução), nível de dificuldade sentido e
        satisfação com o roadmap que o usuário deixou nas missões já
        concluídas desse capítulo, para alimentar a adaptação -- cada item
        tem mission_title/reflection/difficulty_rating/satisfaction_rating
        (os 3 últimos são opcionais). Se 'since' for informado, considera só
        execuções DEPOIS desse momento -- evita reenviar à IA algo que uma
        adaptação anterior já processou."""
        ...

    async def count_completed_chapters(self, roadmap_id: int) -> int:
        """Quantos capítulos desse roadmap já estão com status 'completed'
        -- usado para decidir quando a triagem automática deve rodar."""
        ...

    async def get_reflections_for_chapters(
        self, chapter_ids: List[int], user_id: int
    ) -> List[Dict[str, Any]]:
        """Mesma ideia de get_chapter_reflections, mas de vários capítulos
        de uma vez (usado pela triagem automática, que olha os últimos N
        capítulos)."""
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

    async def add_mission_to_chapter(
        self,
        chapter_id: int,
        title: str,
        description: Optional[str],
        estimated_minutes: Optional[int],
    ) -> Any:
        """Adiciona uma missão criada manualmente ao final de um capítulo
        existente (order_index calculado automaticamente). created_by fica
        "user" -- este método só é usado pelo fluxo de criação manual."""
        ...

    async def update_mission(self, mission_id: int, **fields: Any) -> Any:
        """Atualiza campos de uma missão existente (edição manual)."""
        ...

    async def delete_mission(self, mission_id: int) -> None:
        """Apaga uma missão E reordena o order_index das missões
        remanescentes do mesmo capítulo, para não deixar buraco na sequência
        (ex: apagar a missão de índice 1 em [0,1,2,3] deixa [0,2,3] sem essa
        reordenação -- este método fecha isso para [0,1,2]). O CHAMADOR é
        responsável por já ter checado que ela não tem execução -- este
        método não valida isso de novo."""
        ...

    async def insert_chapter_after(
        self,
        roadmap_id: int,
        title: str,
        after_order_index: int,
        status: str,
    ) -> Any:
        """Insere um único capítulo manual (created_by="user", sem missões)
        logo após a posição informada, empurrando +1 no order_index de todo
        capítulo que já estava depois dela. Diferente de append_chapters,
        que assume que não há nada para empurrar porque sempre insere no
        final do roadmap -- este método permite inserir em qualquer posição,
        inclusive no meio."""
        ...

    async def complete_chapter_and_unlock_next(self, chapter_id: int, next_chapter_id: Optional[int]) -> None:
        """Marca um capítulo como completed e desbloqueia o próximo, se
        houver -- usado quando apagar a última missão pendente de um
        capítulo faz ele terminar "sozinho"."""
        ...

    async def set_pending_adaptation(self, roadmap_id: int, operation: Dict[str, Any]) -> None:
        """Guarda uma operação (replace_chapter/insert_chapter) como
        proposta pendente -- NÃO aplica nada nos capítulos/missões reais
        ainda. Ver ProposeChapterOperationUseCase."""
        ...

    async def clear_pending_adaptation(self, roadmap_id: int) -> None:
        """Descarta a proposta pendente, aplicada ou não -- usado tanto
        depois de confirmar quanto depois de rejeitar."""
        ...

    async def replace_chapter_content(self, chapter_id: int, title: str, missions_data: List[Dict[str, Any]]) -> None:
        """Aplica um operation type="replace_chapter" confirmado: troca o
        título do capítulo e SUBSTITUI todas as suas missões (apaga as
        antigas, insere as novas com created_by="ai"). Só deve ser chamado
        depois que ConfirmAdaptationUseCase já validou que o capítulo não
        está completed nem locked -- este método não revalida isso."""
        ...

    async def insert_full_chapter_after(
        self,
        roadmap_id: int,
        after_order_index: int,
        title: str,
        missions_data: List[Dict[str, Any]],
        status: str = "locked",
    ) -> Any:
        """Como insert_chapter_after, mas já vem COM missões (usado ao
        aplicar um operation type="insert_chapter" confirmado) --
        created_by="ai" tanto no capítulo quanto nas missões, diferente de
        insert_chapter_after (criação manual, created_by="user")."""
        ...

    async def set_chapter_lock(self, chapter_id: int, locked: bool) -> None:
        """Liga/desliga is_locked_from_ai -- um capítulo travado nunca é
        alvo de replace_chapter/insert_chapter pela adaptação."""
        ...

    async def get_current_pending_mission_title_for_user(self, user_id: int) -> Optional[str]:
        """Título da missão "atual" (primeira pendente do capítulo em
        andamento) do objetivo ativo mais recente do usuário -- usado pra
        enriquecer notificação de lembrete genérico (Reminder não é preso a
        um goal específico, ver models.py). Se o usuário tiver mais de um
        objetivo ativo, pega só o mais recente; se não achar nenhuma
        missão pendente, devolve None (quem chama cai pro texto padrão do
        lembrete)."""
        ...