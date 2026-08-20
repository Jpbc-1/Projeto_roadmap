from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.infrastructure.database.models import Flashcard


class FlashcardNotFoundError(Exception):
    """Levantado quando o flashcard não existe."""


class FlashcardAccessDeniedError(Exception):
    """Levantado quando o flashcard existe, mas pertence a outro usuário."""


async def require_flashcard_access(flashcard_repository: FlashcardRepository, flashcard_id: int, user_id: int) -> Flashcard:
    flashcard = await flashcard_repository.get_by_id(flashcard_id)
    if flashcard is None:
        raise FlashcardNotFoundError(f"Flashcard {flashcard_id} não encontrado.")
    if flashcard.user_id != user_id:
        raise FlashcardAccessDeniedError("Você não tem acesso a este flashcard.")
    return flashcard
