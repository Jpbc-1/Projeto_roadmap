from datetime import date, datetime
from typing import List, Literal, Optional

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
    category: Optional[str]
    involves_learning: bool
    generation_status: str
    generation_error: Optional[str]
    weekly_active_days: Optional[int]
    daily_time_minutes: Optional[int]
    prior_knowledge_level: Optional[str]
    estimated_completion_weeks: Optional[int]
    # Preenchido só quando generation_status == "awaiting_info" -- o front
    # mostra essas perguntas e envia as respostas via POST /answers.
    pending_questions: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class GoalCreatedResponse(BaseModel):
    goal: GoalOut
    message: str


class GoalAnswersRequest(BaseModel):
    # Mesma ordem/quantidade de goal.pending_questions -- resposta vazia
    # ("") numa posição é tratada como "não respondida", sem quebrar nada.
    answers: List[str]


class RecommendationOut(BaseModel):
    id: int
    name: str
    description: str
    is_paid: bool

    class Config:
        from_attributes = True