from typing import List, Optional

from pydantic import BaseModel, Field


class MissionProgressOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_minutes: Optional[int]
    order_index: int
    completed: bool
    is_conceptual: bool
    created_by: str


class ChapterProgressOut(BaseModel):
    id: int
    title: str
    order_index: int
    status: str 
    created_by: str
    is_locked_from_ai: bool
    missions: List[MissionProgressOut]


class RoadmapProgressOut(BaseModel):
    id: int
    version: int
    current_chapter_id: Optional[int]
    current_mission_id: Optional[int]
    pending_adaptation: Optional[dict] = None
    chapters: List[ChapterProgressOut]


class AdaptGoalRequest(BaseModel):
    feedback: Optional[str] = Field(None, max_length=1000)


class ChapterCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    after_chapter_id: Optional[int] = None


class AdaptGoalResponse(BaseModel):
    message: str
    job_id: Optional[int] = None
    requires_confirmation: bool = False
    chapters_changed: Optional[int] = None
    missions_changed: Optional[int] = None


class ChapterLockRequest(BaseModel):
    locked: bool