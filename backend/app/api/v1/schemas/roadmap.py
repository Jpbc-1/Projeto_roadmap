from typing import List, Optional

from pydantic import BaseModel


class MissionProgressOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_minutes: Optional[int]
    order_index: int
    completed: bool


class ChapterProgressOut(BaseModel):
    id: int
    title: str
    order_index: int
    status: str
    missions: List[MissionProgressOut]


class RoadmapProgressOut(BaseModel):
    id: int
    version: int
    chapters: List[ChapterProgressOut]


class AdaptGoalRequest(BaseModel):
    feedback: Optional[str] = None


class AdaptGoalResponse(BaseModel):
    message: str
    new_chapters_count: int