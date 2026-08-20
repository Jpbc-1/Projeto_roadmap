from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


FLASHCARD_TEXT_MAX_LENGTH = 2000


class FlashcardCreateRequest(BaseModel):
    front: str = Field(..., min_length=1, max_length=FLASHCARD_TEXT_MAX_LENGTH)
    back: str = Field(..., min_length=1, max_length=FLASHCARD_TEXT_MAX_LENGTH)
    deck_id: Optional[int] = None


class FlashcardUpdateRequest(BaseModel):
    front: Optional[str] = Field(None, min_length=1, max_length=FLASHCARD_TEXT_MAX_LENGTH)
    back: Optional[str] = Field(None, min_length=1, max_length=FLASHCARD_TEXT_MAX_LENGTH)
    deck_id: Optional[int] = None


class ApproveCandidateRequest(BaseModel):
    deck_id: Optional[int] = None


class AnswerFlashcardReviewRequest(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]


class FlashcardOut(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    status: str
    due: datetime
    created_at: datetime
    deck_name: Optional[str] = None
    mission_title: Optional[str] = None
    chapter_title: Optional[str] = None
    goal_id: Optional[int] = None
    goal_title: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_context(cls, context) -> "FlashcardOut":
        """Monta a partir de um FlashcardRepository.FlashcardContext
        (flashcard + contexto de origem), usado por list/due -- ver
        from_attributes acima para o caso mais simples (flashcard puro,
        sem contexto, usado por create/update/approve)."""
        return cls(
            id=context.flashcard.id,
            deck_id=context.flashcard.deck_id,
            front=context.flashcard.front,
            back=context.flashcard.back,
            status=context.flashcard.status,
            due=context.flashcard.due,
            created_at=context.flashcard.created_at,
            deck_name=context.deck_name,
            mission_title=context.mission_title,
            chapter_title=context.chapter_title,
            goal_id=context.goal_id,
            goal_title=context.goal_title,
        )


class AnswerFlashcardReviewResponse(BaseModel):
    flashcard: FlashcardOut
    graduated: bool
    remaining_reviews_today: Optional[int]
    daily_bonus_awarded: bool
    xp_earned: int
