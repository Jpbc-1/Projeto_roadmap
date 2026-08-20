from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RegisterPushTokenInput(BaseModel):
    push_token: str = Field(..., min_length=1, max_length=255)
    platform: Literal["ios", "android"]


class UnregisterPushTokenInput(BaseModel):
    push_token: str = Field(..., min_length=1, max_length=255)


class PushTokenOut(BaseModel):
    id: int
    platform: str
    updated_at: datetime

    class Config:
        from_attributes = True
