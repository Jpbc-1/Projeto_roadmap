from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    job_type: str
    status: str
    attempts: int
    max_attempts: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
