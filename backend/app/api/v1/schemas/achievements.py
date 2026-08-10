from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AchievementOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    required_condition: str
    icon_url: Optional[str]

    class Config:
        from_attributes = True


class UnlockedAchievementOut(BaseModel):
    achievement: AchievementOut
    unlocked_at: datetime

    class Config:
        from_attributes = True
