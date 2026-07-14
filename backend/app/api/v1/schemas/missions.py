from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MissionCompleteRequest(BaseModel):
    user_reflection: Optional[str] = None  


class MissionExecutionOut(BaseModel):
    id: int
    mission_id: int
    completed_at: datetime
    xp_rewarded: int
    user_reflection: Optional[str]
    ai_feedback: Optional[str]

    class Config:
        from_attributes = True