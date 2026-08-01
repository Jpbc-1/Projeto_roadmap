from datetime import time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.api.v1.schemas.notification_preferences import NotificationPreferenceFields


class ReminderCreate(NotificationPreferenceFields):
    label: str = Field(..., max_length=120, examples=["Lembrete da manhã"])
    # Ambos opcionais de propósito: só obrigatórios quando
    # notification_timing_mode='custom' (ver validador). Quando
    # 'app_default', o caso de uso preenche com core/notification_defaults.py
    # e ignora o que vier aqui.
    time_of_day: Optional[time] = Field(default=None, examples=["08:00:00"])
    days_of_week: Optional[List[int]] = Field(default=None, examples=[[0, 1, 2, 3, 4, 5, 6]])

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is None:
            return v
        if not v:
            raise ValueError("days_of_week não pode ser uma lista vazia")
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("cada dia deve ser um número de 0 (domingo) a 6 (sábado)")
        return sorted(set(v))

    @model_validator(mode="after")
    def custom_mode_requires_explicit_time(self) -> "ReminderCreate":
        if self.notification_timing_mode == "custom":
            if self.time_of_day is None or not self.days_of_week:
                raise ValueError(
                    "time_of_day e days_of_week são obrigatórios quando "
                    "notification_timing_mode='custom'"
                )
        if self.notification_style == "custom_message" and not self.custom_message:
            raise ValueError("custom_message é obrigatório quando notification_style='custom_message'")
        return self


class ReminderUpdate(NotificationPreferenceFields):
    """Igual ReminderCreate, mas tudo opcional -- PUT parcial: só manda o
    que quer mudar."""

    label: Optional[str] = Field(default=None, max_length=120)
    time_of_day: Optional[time] = None
    days_of_week: Optional[List[int]] = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is None:
            return v
        if not v:
            raise ValueError("days_of_week não pode ser uma lista vazia")
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("cada dia deve ser um número de 0 (domingo) a 6 (sábado)")
        return sorted(set(v))


class ReminderToggleRequest(BaseModel):
    is_active: bool


class ReminderOut(NotificationPreferenceFields):
    id: int
    label: str
    time_of_day: time
    days_of_week: List[int]
    is_active: bool

    class Config:
        from_attributes = True
