from typing import Literal, Optional

from pydantic import BaseModel, Field


class NotificationPreferenceFields(BaseModel):
    """
    As 3 escolhas que sempre têm que existir (ver docs/adr/0003),
    compartilhadas entre ReminderCreate e CalendarEventCreate -- o schema
    é reusado, mas cada tabela guarda suas próprias colunas (ver
    docs/adr/0002: dois mecanismos separados, não um sistema polimórfico
    único).

    - notification_timing_mode: 'app_default' (o app decide o horário) ou
      'custom' (a pessoa escolhe).
    - notification_style: 'app_generated' (texto montado na hora do
      disparo) ou 'custom_message' (a pessoa escreve o texto).
    """

    notification_timing_mode: Literal["app_default", "custom"] = "app_default"
    notification_style: Literal["app_generated", "custom_message"] = "app_generated"
    custom_message: Optional[str] = Field(default=None, max_length=280)
