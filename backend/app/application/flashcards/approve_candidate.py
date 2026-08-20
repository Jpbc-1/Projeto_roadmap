from typing import Optional

from app.application.flashcards.deck_access import require_deck_access
from app.application.flashcards.flashcard_access import require_flashcard_access
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.infrastructure.database.models import Flashcard


class NotAPendingCandidateError(Exception):
    """Levantado quando o flashcard não está esperando aprovação (já foi
    aprovado antes, ou é um flashcard criado manualmente que nunca passou
    por essa etapa)."""


class ApproveCandidateUseCase:
    """Move um candidato de "pending_review" pra "active" -- ele já nasceu
    com o estado inicial do FSRS (ver ExtractConceptsUseCase), então só
    precisa trocar o status (e opcionalmente o baralho de destino, se a
    pessoa quiser um baralho diferente do principal)."""

    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(self, flashcard_id: int, user_id: int, deck_id: Optional[int] = None) -> Flashcard:
        flashcard = await require_flashcard_access(self.flashcard_repository, flashcard_id, user_id)
        if flashcard.status != "pending_review":
            raise NotAPendingCandidateError(f"Flashcard {flashcard_id} não está aguardando aprovação.")

        if deck_id is not None:
            await require_deck_access(self.deck_repository, deck_id, user_id)
        else:
            deck_id = flashcard.deck_id  

        return await self.flashcard_repository.update(flashcard_id, status="active", deck_id=deck_id)
