from typing import List

from app.application.flashcards.deck_access import require_deck_access
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardContext, FlashcardRepository


class ListFlashcardsByDeckUseCase:
    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(self, deck_id: int, user_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        await require_deck_access(self.deck_repository, deck_id, user_id)
        return await self.flashcard_repository.list_by_deck(deck_id, limit=limit, offset=offset)
