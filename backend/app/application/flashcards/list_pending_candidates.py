from typing import List

from app.domain.repositories.flashcard_repository import FlashcardContext, FlashcardRepository


class ListPendingCandidatesUseCase:
    """Candidatos gerados pela extração de IA (status="pending_review"),
    aguardando a pessoa escolher quais realmente quer no baralho -- ver
    ApproveCandidateUseCase e DeleteFlashcardUseCase (rejeitar)."""

    def __init__(self, flashcard_repository: FlashcardRepository):
        self.flashcard_repository = flashcard_repository

    async def execute(self, user_id: int, limit: int, offset: int) -> List[FlashcardContext]:
        return await self.flashcard_repository.list_pending_for_user(user_id, limit=limit, offset=offset)
