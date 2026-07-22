from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class DueReviewOut(BaseModel):
    node_id: int
    goal_id: int
    goal_title: Optional[str]
    topic_name: str
    next_review_date: date
    mastery_level: str  


class AnswerReviewRequest(BaseModel):
    difficulty: Literal["again", "hard", "good", "easy"]


class ReviewResultOut(BaseModel):
    node_id: int
    topic_name: str
    new_interval_days: int
    new_easiness_factor: float
    next_review_date: date
    mastery_level: str
    remaining_reviews_today: int
    daily_bonus_awarded: bool
    xp_earned: int