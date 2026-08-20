from datetime import date, datetime, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from app.application.flashcards.deck_access import require_deck_access
from app.core.config import settings
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardContext, FlashcardRepository


class GetDueFlashcardsUseCase:
    """deck_id/goal_id opcionais: sem eles, traz due de tudo. Aplica o
    teto diário (settings.DAILY_REVIEW_LIMIT, ver docstring lá) no MESMO
    escopo que foi pedido -- se filtrou por um deck, o teto é daquele
    deck; sem filtro, o teto é do total combinado. Isso é intencional:
    o objetivo é nunca mostrar mais que o teto NUMA TELA, seja qual for
    o recorte."""

    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(
        self,
        user_id: int,
        user_timezone: str,
        deck_id: Optional[int],
        goal_id: Optional[int],
        limit: int,
        offset: int,
    ) -> List[FlashcardContext]:
        if deck_id is not None:
            await require_deck_access(self.deck_repository, deck_id, user_id)

        now = datetime.now(timezone.utc)

        try:
            today_start_local = datetime.combine(
                datetime.now(ZoneInfo(user_timezone)).date(), datetime.min.time(), tzinfo=ZoneInfo(user_timezone)
            )
        except Exception:
            today_start_local = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)

        quota_used = await self.flashcard_repository.count_reviews_since(user_id, deck_id, since=today_start_local)
        remaining_quota = max(0, settings.DAILY_REVIEW_LIMIT - quota_used)
        if remaining_quota == 0:
            return []  

        effective_limit = min(limit, remaining_quota)
        return await self.flashcard_repository.list_due(
            user_id, now, deck_id=deck_id, goal_id=goal_id, limit=effective_limit, offset=offset
        )
