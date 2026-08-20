from typing import Optional

from app.application.flashcards import scheduler
from app.application.flashcards.deck_access import require_deck_access
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.infrastructure.database.models import Flashcard


class CreateFlashcardUseCase:
    """Flashcard criado diretamente pela pessoa, sem passar por extração
    de IA -- knowledge_node_id fica NULL (ver Flashcard em models.py).
    Nasce direto em status="active" (diferente dos candidatos da IA, que
    nascem "pending_review"): aqui a própria pessoa já decidiu que quer
    isso no baralho, não tem candidato pra aprovar."""

    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(self, user_id: int, front: str, back: str, deck_id: Optional[int] = None) -> Flashcard:
        if deck_id is None:
            deck = await self.deck_repository.get_or_create_main(user_id)
            deck_id = deck.id
        else:
            await require_deck_access(self.deck_repository, deck_id, user_id)

        initial_state = scheduler.new_card_state()
        return await self.flashcard_repository.create(
            user_id=user_id,
            deck_id=deck_id,
            knowledge_node_id=None,
            front=front,
            back=back,
            status="active",
            fsrs_state=initial_state.fsrs_state,
            fsrs_step=initial_state.fsrs_step,
            stability=initial_state.stability,
            difficulty=initial_state.difficulty,
            due=initial_state.due,
        )
