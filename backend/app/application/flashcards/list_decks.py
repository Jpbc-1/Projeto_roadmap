from dataclasses import dataclass
from typing import List

from app.domain.repositories.deck_repository import DeckRepository
from app.infrastructure.database.models import Deck


@dataclass
class DeckSummary:
    deck: Deck
    active_count: int
    pending_count: int
    graduated_count: int


class ListDecksUseCase:
    """Garante que o baralho principal existe e aparece SEMPRE em primeiro
    (mesmo pra quem nunca teve nenhum flashcard ainda) -- chamar
    get_or_create_main aqui, e não só confiar que alguma extração já
    criou, evita a tela de baralhos aparecer vazia/confusa pra quem ainda
    não tem nenhum conceito extraído mas já quer criar um flashcard manual
    num baralho novo."""

    def __init__(self, deck_repository: DeckRepository):
        self.deck_repository = deck_repository

    async def execute(self, user_id: int) -> List[DeckSummary]:
        await self.deck_repository.get_or_create_main(user_id)
        decks = await self.deck_repository.list_by_user(user_id)

        summaries = []
        for deck in decks:
            counts = await self.deck_repository.count_flashcards_by_status(deck.id)
            summaries.append(
                DeckSummary(
                    deck=deck,
                    active_count=counts.get("active", 0),
                    pending_count=counts.get("pending_review", 0),
                    graduated_count=counts.get("graduated", 0),
                )
            )
        return summaries
