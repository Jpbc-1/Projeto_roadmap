from datetime import time
from typing import List, Optional

from app.core import notification_defaults
from app.domain.repositories.reminder_repository import ReminderRepository
from app.infrastructure.database.models import Reminder


class ReminderNotFoundError(Exception):
    """Levantado quando o lembrete não existe."""


class ReminderAccessDeniedError(Exception):
    """Levantado quando o lembrete existe, mas pertence a outro usuário."""


class UpdateReminderUseCase:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def execute(
        self,
        reminder_id: int,
        user_id: int,
        label: Optional[str] = None,
        notification_timing_mode: Optional[str] = None,
        notification_style: Optional[str] = None,
        time_of_day: Optional[time] = None,
        days_of_week: Optional[List[int]] = None,
        custom_message: Optional[str] = None,
    ) -> Reminder:
        existing = await self.reminder_repository.get_by_id(reminder_id)
        if existing is None:
            raise ReminderNotFoundError()
        if existing.user_id != user_id:
            raise ReminderAccessDeniedError()

        # PUT parcial: só monta o dict com o que de fato veio na
        # requisição -- nunca sobrescreve campo nenhum com None sem querer.
        fields = {}
        if label is not None:
            fields["label"] = label
        if notification_style is not None:
            fields["notification_style"] = notification_style
        if custom_message is not None:
            fields["custom_message"] = custom_message

        # timing_mode e horário sempre andam juntos -- resolve os dois ou
        # nenhum, pra nunca deixar o registro com mode='custom' mas
        # horário do modo antigo (ou vice-versa).
        if notification_timing_mode is not None:
            fields["notification_timing_mode"] = notification_timing_mode
            if notification_timing_mode == "custom":
                fields["time_of_day"] = time_of_day if time_of_day is not None else existing.time_of_day
                fields["days_of_week"] = days_of_week if days_of_week else existing.days_of_week
            else:
                fields["time_of_day"] = notification_defaults.DEFAULT_REMINDER_TIME
                fields["days_of_week"] = notification_defaults.DEFAULT_REMINDER_DAYS_OF_WEEK
        elif time_of_day is not None or days_of_week:
            # timing_mode não mudou, mas a pessoa ajustou horário/dias na
            # mão -- só faz sentido se já estava em 'custom'.
            fields["time_of_day"] = time_of_day if time_of_day is not None else existing.time_of_day
            fields["days_of_week"] = days_of_week if days_of_week else existing.days_of_week

        if not fields:
            return existing

        return await self.reminder_repository.update(reminder_id, **fields)
