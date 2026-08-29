from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional, Protocol

from app.infrastructure.database.models import Flashcard


@dataclass
class FlashcardContext:
    """Flashcard + de onde ele veio, pra exibir como contexto opcional na
    UI (ver pedido original: "gostaria que o flashcard aparecesse também
    de que missão e capítulo ele veio"). Os campos de origem são todos
    Optional porque um flashcard criado manualmente (knowledge_node_id
    NULL) ou cujo conceito não pôde ser atribuído a uma missão específica
    (KnowledgeNode.mission_id NULL, ver extract_concepts.py) não tem essa
    informação -- e não deveria: é só contexto extra, nunca obrigatório."""

    flashcard: Flashcard
    deck_name: str
    mission_title: Optional[str]
    chapter_title: Optional[str]
    goal_id: Optional[int]
    goal_title: Optional[str]


class FlashcardRepository(Protocol):
    async def create(self, **fields: Any) -> Flashcard:
        """Cria com os campos passados via kwargs (mesmo padrão de update
        abaixo) -- quem chama monta os valores certos (ex: estado inicial
        do FSRS vem de scheduler.new_card_state(), não daqui)."""
        ...

    async def get_by_id(self, flashcard_id: int) -> Optional[Flashcard]: ...

    async def update(self, flashcard_id: int, **fields: Any) -> Flashcard:
        """Atualiza só os campos passados -- usado tanto pra aprovar um
        candidato (status/fsrs_state/due) quanto editar conteúdo (front/
        back/deck_id) quanto aplicar o resultado de uma revisão
        (fsrs_state/stability/difficulty/due/last_review_at/
        consecutive_easy_count/status), mesmo padrão genérico já usado em
        ReminderRepository.update e GoalRepository.update."""
        ...

    async def delete(self, flashcard_id: int) -> None: ...

    async def list_pending_for_user(self, user_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        """Candidatos gerados pela extração (status="pending_review"),
        aguardando a pessoa decidir se aprova ou rejeita -- ver GET
        /flashcards/pending."""
        ...

    async def list_by_deck(self, deck_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        """Flashcards de um baralho (qualquer status) -- ver GET
        /decks/{deck_id}/flashcards."""
        ...

    async def list_due(
        self,
        user_id: int,
        now: datetime,
        deck_id: Optional[int],
        goal_id: Optional[int],
        limit: int,
        offset: int,
    ) -> List[FlashcardContext]:
        """Flashcards status="active" com due <= now, mais antigos
        primeiro -- deck_id/goal_id filtram quando informados (goal_id
        via o KnowledgeNode de origem; flashcard manual, sem
        knowledge_node, nunca aparece filtrando por goal_id). O limit
        efetivo já vem short-circuited pelo teto diário -- ver
        GetDueFlashcardsUseCase, este método só executa a query."""
        ...

    async def count_due(self, user_id: int, now: datetime, deck_id: Optional[int]) -> int:
        """COUNT direto (não list_due()+len()) -- mesmo motivo de
        KnowledgeNodeRepository.count_due_for_user antes dele: usado por
        AnswerFlashcardReviewUseCase só pra saber SE zerou a fila (decide
        o bônus/streak), não pra listar, e list_due agora é paginada."""
        ...

    async def count_reviews_since(self, user_id: int, deck_id: Optional[int], since: datetime) -> int:
        """Quantas revisões essa conta já fez, no baralho indicado (ou em
        todos, se None), desde o instante informado -- usado pra aplicar
        o TETO DIÁRIO de revisões (ver settings.DAILY_REVIEW_LIMIT):
        deriva do log de revisões (flashcard_reviews) em vez de manter um
        contador solto, então não tem risco de ficar dessincronizado."""
        ...

    async def create_review_log(
        self,
        flashcard_id: int,
        rating: str,
        old_stability: Optional[float],
        new_stability: Optional[float],
        old_difficulty: Optional[float],
        new_difficulty: Optional[float],
        elapsed_days: Optional[int],
    ) -> None:
        """Só a linha de auditoria, sem tocar o estado do cartão -- ver
        record_review() pra o caso comum (aplicar resultado + logar numa
        transação atômica só)."""
        ...

    async def record_review(
        self,
        flashcard_id: int,
        rating: str,
        old_stability: Optional[float],
        new_stability: Optional[float],
        old_difficulty: Optional[float],
        new_difficulty: Optional[float],
        elapsed_days: Optional[int],
        card_updates: dict,
    ) -> Flashcard:
        """Aplica card_updates (fsrs_state/stability/difficulty/due/
        last_review_at/consecutive_easy_count/status) e grava o log de
        auditoria numa ÚNICA transação -- é este método (não update() +
        create_review_log() em sequência) que AnswerFlashcardReviewUseCase
        deve usar, pra nunca sobrar um cartão atualizado sem o log
        correspondente se o processo cair no meio."""
        ...

    async def get_user_stats(self, user_id: int):
        """Reaproveita a mesma UserStats de missões -- XP e streak são um
        sistema único, não um contador separado por funcionalidade."""
        ...

    async def apply_daily_review_bonus(
        self,
        user_id: int,
        total_xp: int,
        level: int,
        current_streak: int,
        max_streak: int,
        activity_date,
    ) -> bool:
        """Aplica o bônus por ter zerado a fila de revisões do dia -- SÓ
        chamado quando a fila do BARALHO PRINCIPAL zera (ver
        AnswerFlashcardReviewUseCase); baralhos extra não contam pro
        streak.

        Idempotente por dia via UPDATE...WHERE atômico condicionado a
        user_stats.last_bonus_date (mesmo padrão de try_deduct_credits):
        SÓ aplica se last_bonus_date ainda não for hoje. Devolve True se
        aplicou de verdade, False se o bônus de hoje já tinha sido dado
        antes (nesse caso quem chama NÃO deve contar XP/bônus de novo).

        Isso importa porque "a fila zerou" não é um evento único no dia:
        se a fila esvaziar de novo mais tarde (um card "again" que a
        própria FSRS reagenda pra minutos depois, ou um flashcard novo
        que entrou e foi revisado ainda hoje), ela pode voltar a zerar
        outra vez -- sem esta trava, isso concederia o bônus mais de uma
        vez no mesmo dia."""
        ...
