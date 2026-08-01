from datetime import datetime
from typing import Optional

from pydantic import Field, ValidationInfo, field_validator, model_validator

from app.api.v1.schemas.notification_preferences import NotificationPreferenceFields


class CalendarEventCreate(NotificationPreferenceFields):
    title: str = Field(..., max_length=200, examples=["Dentista"])
    description: Optional[str] = Field(default=None, max_length=1000)
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    is_all_day: bool = False
    notify_enabled: bool = True
    # Obrigatório só quando notify_enabled=True e timing_mode='custom'
    # (ver validador). Até 1 semana (10080 min) antes -- só pra pegar erro
    # de digitação.
    remind_before_minutes: Optional[int] = Field(default=None, ge=0, le=10080)

    @field_validator("end_datetime")
    @classmethod
    def end_after_start(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        start = info.data.get("start_datetime")
        if v is not None and start is not None and v < start:
            raise ValueError("end_datetime não pode ser antes de start_datetime")
        return v

    @model_validator(mode="after")
    def notification_fields_are_consistent(self) -> "CalendarEventCreate":
        if not self.notify_enabled:
            return self
        if self.notification_timing_mode == "custom" and self.remind_before_minutes is None:
            raise ValueError(
                "remind_before_minutes é obrigatório quando notify_enabled=True "
                "e notification_timing_mode='custom'"
            )
        if self.notification_style == "custom_message" and not self.custom_message:
            raise ValueError("custom_message é obrigatório quando notification_style='custom_message'")
        return self


class CalendarEventUpdate(NotificationPreferenceFields):
    """Igual CalendarEventCreate, mas tudo opcional -- PUT parcial."""

    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    notify_enabled: Optional[bool] = None
    remind_before_minutes: Optional[int] = Field(default=None, ge=0, le=10080)


class CalendarEventOut(NotificationPreferenceFields):
    id: int
    title: str
    description: Optional[str]
    start_datetime: datetime
    end_datetime: Optional[datetime]
    is_all_day: bool
    notify_enabled: bool
    remind_before_minutes: Optional[int]

    class Config:
        from_attributes = True
