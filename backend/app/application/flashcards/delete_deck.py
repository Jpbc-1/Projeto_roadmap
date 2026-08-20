from app.application.flashcards.deck_access import require_deck_access
from app.domain.repositories.deck_repository import DeckRepository


class CannotDeleteMainDeckError(Exception):
    """Levantado ao tentar apagar o baralho principal -- ele não pode ser
    removido (é pra onde tudo volta quando outro baralho é apagado, e é o
    único que conta pro streak)."""


class DeleteDeckUseCase:
    """Nunca apaga flashcard em cascata: move todo mundo pro baralho
    principal antes de apagar o baralho em si (ver
    DeckRepository.move_flashcards_and_delete) -- baralho é só uma forma
    de organizar, apagar um não deveria destruir progresso de revisão de
    ninguém."""

    def __init__(self, deck_repository: DeckRepository):
        self.deck_repository = deck_repository

    async def execute(self, deck_id: int, user_id: int) -> None:
        deck = await require_deck_access(self.deck_repository, deck_id, user_id)
        if deck.is_main:
            raise CannotDeleteMainDeckError("O baralho principal não pode ser apagado.")

        main_deck = await self.deck_repository.get_or_create_main(user_id)
        await self.deck_repository.move_flashcards_and_delete(deck_id, main_deck.id)
