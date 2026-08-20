from typing import Dict, List, Optional, Protocol

from app.infrastructure.database.models import Deck


class DeckRepository(Protocol):
    async def get_or_create_main(self, user_id: int) -> Deck:
        """O baralho 'Principal' dessa conta -- cria na hora se ainda não
        existir (ver Deck.is_main em models.py). É pra ONDE os flashcards
        aprovados da extração de IA vão por padrão, e é o único baralho
        que conta pro streak (ver AnswerFlashcardReviewUseCase)."""
        ...

    async def create(self, user_id: int, name: str) -> Deck:
        """Baralho extra, NÃO principal -- is_main sempre False aqui (só
        get_or_create_main cria um baralho principal)."""
        ...

    async def get_by_id(self, deck_id: int) -> Optional[Deck]: ...

    async def list_by_user(self, user_id: int) -> List[Deck]:
        """Todos os baralhos da conta -- normalmente poucos (não temos
        paginação aqui de propósito: baralho é algo que a pessoa cria
        deliberadamente, não algo que se acumula em massa como reminders)."""
        ...

    async def count_flashcards_by_status(self, deck_id: int) -> Dict[str, int]:
        """Quantos flashcards em cada status ('active'/'pending_review'/
        'graduated') esse baralho tem -- usado só pra exibir contagem na
        listagem de baralhos, sem carregar os flashcards inteiros."""
        ...

    async def move_flashcards_and_delete(self, deck_id: int, target_deck_id: int) -> None:
        """Move todo flashcard de deck_id pra target_deck_id, depois apaga
        deck_id -- usado por DeleteDeckUseCase. Nunca apaga flashcard
        junto: baralho é só uma organização, apagar um não deveria
        destruir o progresso de revisão de ninguém (ver DeleteDeckUseCase
        pra a proteção de não deixar apagar o baralho principal)."""
        ...
