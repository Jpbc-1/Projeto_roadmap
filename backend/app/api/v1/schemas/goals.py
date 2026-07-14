from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class GoalCreate(BaseModel):
    context_prompt: str
    target_date: Optional[date] = None


class GoalOut(BaseModel):
    id: int
    title: Optional[str]
    context_prompt: str
    target_date: Optional[date]
    status: str
    generation_status: str
    generation_error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalCreatedResponse(BaseModel):
    goal: GoalOut
    message: str