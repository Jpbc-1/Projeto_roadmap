from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    context_prompt: str
    target_date: Optional[date] = None

    weekly_active_days: Optional[int] = Field(None, ge=1, le=7)
    daily_time_minutes: Optional[int] = Field(None, gt=0)
    prior_knowledge_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None


class GoalOut(BaseModel):
    id: int
    title: Optional[str]
    context_prompt: str
    target_date: Optional[date]
    status: str
    generation_status: str
    generation_error: Optional[str]
    weekly_active_days: Optional[int]
    daily_time_minutes: Optional[int]
    prior_knowledge_level: Optional[str]
    estimated_completion_weeks: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalCreatedResponse(BaseModel):
    goal: GoalOut
    message: str