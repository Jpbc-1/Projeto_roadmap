from app.domain.repositories.deck_repository import DeckRepository
from app.infrastructure.database.models import Deck


class CreateDeckUseCase:
    """Baralho extra, por tema -- o principal nasce sozinho (ver
    DeckRepository.get_or_create_main), nunca por aqui."""

    def __init__(self, deck_repository: DeckRepository):
        self.deck_repository = deck_repository

    async def execute(self, user_id: int, name: str) -> Deck:
        return await self.deck_repository.create(user_id=user_id, name=name)
