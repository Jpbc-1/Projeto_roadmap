from app.domain.repositories.deck_repository import DeckRepository
from app.infrastructure.database.models import Deck


class DeckNotFoundError(Exception):
    """Levantado quando o baralho não existe."""


class DeckAccessDeniedError(Exception):
    """Levantado quando o baralho existe, mas pertence a outro usuário."""


async def require_deck_access(deck_repository: DeckRepository, deck_id: int, user_id: int) -> Deck:
    """Busca + confere dono, repetido em vários use cases (criar flashcard
    num deck específico, mover flashcard de deck, listar flashcards de um
    deck, apagar deck) -- um lugar só pra essa checagem em vez de
    duplicada em cada um."""
    deck = await deck_repository.get_by_id(deck_id)
    if deck is None:
        raise DeckNotFoundError(f"Baralho {deck_id} não encontrado.")
    if deck.user_id != user_id:
        raise DeckAccessDeniedError("Você não tem acesso a este baralho.")
    return deck
