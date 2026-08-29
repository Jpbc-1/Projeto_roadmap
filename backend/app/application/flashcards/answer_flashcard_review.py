from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from app.application.flashcards import scheduler
from app.application.flashcards.flashcard_access import require_flashcard_access
from app.application.gamification.streak import calculate_streak_update
from app.core.config import settings
from app.domain.repositories.deck_repository import DeckRepository
from app.domain.repositories.flashcard_repository import FlashcardRepository
from app.infrastructure.database.models import Flashcard

DAILY_REVIEW_BONUS_XP = 20


EASY_STREAK_TO_GRADUATE = 3


class FlashcardNotActiveError(Exception):
    """Levantado ao tentar responder revisão de um flashcard que não está
    "active" -- um candidato pendente precisa ser aprovado primeiro (ver
    ApproveCandidateUseCase), e um já graduado não faz mais parte da
    rotina de revisão (a pessoa pode reativá-lo editando o status, se um
    dia isso for exposto -- não é o caso agora)."""


@dataclass
class AnswerFlashcardReviewResult:
    flashcard: Flashcard
    graduated: bool
    remaining_reviews_today: Optional[int]
    daily_bonus_awarded: bool
    xp_earned: int


class AnswerFlashcardReviewUseCase:
    """Aplica uma resposta ("again"/"hard"/"good"/"easy") via FSRS (ver
    scheduler.py), decide se o cartão graduou, e -- SÓ se o flashcard
    pertence ao baralho PRINCIPAL do usuário -- confere se zerou a fila do
    dia (respeitando settings.DAILY_REVIEW_LIMIT) e credita o bônus de
    streak/XP (mesma lógica de app/application/knowledge/answer_review.py,
    que este use case substitui, só que agora escopada ao baralho
    principal: baralhos extra são pra organização pessoal, sem pressão de
    sequência)."""

    def __init__(self, flashcard_repository: FlashcardRepository, deck_repository: DeckRepository):
        self.flashcard_repository = flashcard_repository
        self.deck_repository = deck_repository

    async def execute(
        self, flashcard_id: int, user_id: int, rating: str, user_timezone: str = "America/Sao_Paulo"
    ) -> AnswerFlashcardReviewResult:
        flashcard = await require_flashcard_access(self.flashcard_repository, flashcard_id, user_id)
        if flashcard.status != "active":
            raise FlashcardNotActiveError(f"Flashcard {flashcard_id} não está ativo.")

        review_datetime = datetime.now(timezone.utc)

        scheduling = scheduler.schedule_review(
            fsrs_state=flashcard.fsrs_state,
            fsrs_step=flashcard.fsrs_step,
            stability=flashcard.stability,
            difficulty=flashcard.difficulty,
            due=flashcard.due,
            last_review_at=flashcard.last_review_at,
            rating=rating,
            review_datetime=review_datetime,
        )

        new_easy_count = flashcard.consecutive_easy_count + 1 if rating == "easy" else 0
        graduated = new_easy_count >= EASY_STREAK_TO_GRADUATE

        card_updates = {
            "fsrs_state": scheduling.fsrs_state,
            "fsrs_step": scheduling.fsrs_step,
            "stability": scheduling.stability,
            "difficulty": scheduling.difficulty,
            "due": scheduling.due,
            "last_review_at": review_datetime,
            "consecutive_easy_count": new_easy_count,
            "status": "graduated" if graduated else "active",
        }

        updated_flashcard = await self.flashcard_repository.record_review(
            flashcard_id=flashcard_id,
            rating=rating,
            old_stability=flashcard.stability,
            new_stability=scheduling.stability,
            old_difficulty=flashcard.difficulty,
            new_difficulty=scheduling.difficulty,
            elapsed_days=scheduling.elapsed_days,
            card_updates=card_updates,
        )

        remaining_count = None
        daily_bonus_awarded = False
        xp_earned = 0

        main_deck = await self.deck_repository.get_or_create_main(user_id)
        if flashcard.deck_id == main_deck.id:
            try:
                today_for_user = datetime.now(ZoneInfo(user_timezone)).date()
                today_start_local = datetime.combine(today_for_user, datetime.min.time(), tzinfo=ZoneInfo(user_timezone))
            except Exception:
                today_for_user = date.today()
                today_start_local = datetime.combine(today_for_user, datetime.min.time(), tzinfo=timezone.utc)

            raw_overdue = await self.flashcard_repository.count_due(user_id, review_datetime, main_deck.id)
            quota_used = await self.flashcard_repository.count_reviews_since(
                user_id, main_deck.id, since=today_start_local
            )
            remaining_quota = max(0, settings.DAILY_REVIEW_LIMIT - quota_used)
            remaining_count = min(raw_overdue, remaining_quota)

            if remaining_count == 0:
                daily_bonus_awarded = await self._award_daily_bonus(user_id, today_for_user)
                if daily_bonus_awarded:
                    xp_earned = DAILY_REVIEW_BONUS_XP

        return AnswerFlashcardReviewResult(
            flashcard=updated_flashcard,
            graduated=graduated,
            remaining_reviews_today=remaining_count,
            daily_bonus_awarded=daily_bonus_awarded,
            xp_earned=xp_earned,
        )

    async def _award_daily_bonus(self, user_id: int, today_for_user: date) -> bool:
        stats = await self.flashcard_repository.get_user_stats(user_id)
        update = calculate_streak_update(stats, xp_to_add=DAILY_REVIEW_BONUS_XP, today=today_for_user)

        return await self.flashcard_repository.apply_daily_review_bonus(
            user_id=user_id,
            total_xp=update.new_total_xp,
            level=update.new_level,
            current_streak=update.new_current_streak,
            max_streak=update.new_max_streak,
            activity_date=update.activity_date,
        )
