from datetime import date
from typing import Optional

from pydantic import BaseModel


class GamificationProfileOut(BaseModel):
    user_id: int
    username: Optional[str]
    email: str
    total_xp: int
    current_level: int
    current_streak: int
    max_streak: int
    last_activity_date: Optional[date]