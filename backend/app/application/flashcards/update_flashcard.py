from typing import Optional

from app.application.flashcards.deck_access import require_deck_access
from app.application.flashcards.flashcard_access import require_flashcard_access
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.infrastructure.database.models import Flashcard


class UpdateFlashcardUseCase:
    """Edita front/back e/ou move o flashcard pra outro baralho -- não
    mexe em nada do estado de repetição espaçada (isso só muda respondendo
    uma revisão de verdade, ver AnswerFlashcardReviewUseCase)."""

    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(
        self,
        flashcard_id: int,
        user_id: int,
        front: Optional[str] = None,
        back: Optional[str] = None,
        deck_id: Optional[int] = None,
    ) -> Flashcard:
        flashcard = await require_flashcard_access(self.flashcard_repository, flashcard_id, user_id)

        updates = {}
        if front is not None:
            updates["front"] = front
        if back is not None:
            updates["back"] = back
        if deck_id is not None:
            await require_deck_access(self.deck_repository, deck_id, user_id)
            updates["deck_id"] = deck_id

        if not updates:
            return flashcard  

        return await self.flashcard_repository.update(flashcard_id, **updates)
