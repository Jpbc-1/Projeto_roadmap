from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.api.v1.schemas.achievements import AchievementOut


class MissionCompleteRequest(BaseModel):
    user_reflection: Optional[str] = Field(None, max_length=2000)
    difficulty_rating: Optional[Literal["too_easy", "just_right", "too_hard"]] = None
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)


class MissionExecutionOut(BaseModel):
    id: int
    mission_id: int
    completed_at: datetime
    xp_rewarded: int
    user_reflection: Optional[str]
    ai_feedback: Optional[str]
    difficulty_rating: Optional[str]
    satisfaction_rating: Optional[int]
    chapter_completed: bool = False
    goal_completed: bool = False
    newly_unlocked_achievements: List[AchievementOut] = []

    class Config:
        from_attributes = True


class MissionCreateRequest(BaseModel):
    goal_id: int
    chapter_id: int
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    estimated_minutes: Optional[int] = Field(None, ge=5, le=180)


class MissionUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    estimated_minutes: Optional[int] = Field(None, ge=5, le=180)


class MissionOut(BaseModel):
    id: int
    chapter_id: int
    title: str
    description: Optional[str]
    estimated_minutes: Optional[int]
    order_index: int
    is_conceptual: bool
    created_by: str

    class Config:
        from_attributes = True