from app.application.flashcards.flashcard_access import require_flashcard_access
from app.domain.repositories.flashcard_repository import FlashcardRepository


class DeleteFlashcardUseCase:
    """Serve tanto pra REJEITAR um candidato pendente (ver GET
    /flashcards/pending -- rejeitar é só não querer aquilo, não faz
    sentido guardar um registro morto de algo que a pessoa nunca chegou a
    usar) quanto pra apagar de vez um flashcard ativo ou já graduado --
    mesmo endpoint, mesma ação, independente do status atual."""

    def __init__(self, flashcard_repository: FlashcardRepository):
        self.flashcard_repository = flashcard_repository

    async def execute(self, flashcard_id: int, user_id: int) -> None:
        await require_flashcard_access(self.flashcard_repository, flashcard_id, user_id)
        await self.flashcard_repository.delete(flashcard_id)
