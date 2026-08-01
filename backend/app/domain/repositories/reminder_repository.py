from datetime import datetime, time
from typing import Any, List, Optional, Protocol

from app.infrastructure.database.models import Reminder


class ReminderRepository(Protocol):
    async def create(
        self,
        user_id: int,
        label: str,
        time_of_day: time,
        days_of_week: List[int],
        notification_timing_mode: str = "app_default",
        notification_style: str = "app_generated",
        custom_message: Optional[str] = None,
    ) -> Reminder: ...

    async def list_by_user(self, user_id: int) -> List[Reminder]: ...

    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]: ...

    async def update(self, reminder_id: int, **fields: Any) -> Reminder: ...

    async def delete(self, reminder_id: int) -> None: ...

    async def list_due(self, now_utc: datetime) -> List[Reminder]:
        """Lembretes ativos cujo dia da semana + horário batem com 'now_utc'
        NO FUSO DO DONO de cada lembrete (não em UTC direto -- ver
        User.timezone). Usado pelo agendador de disparo, não pela tela."""
        ...
