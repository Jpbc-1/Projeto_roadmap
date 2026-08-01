from datetime import time
from typing import List, Optional

from app.core import notification_defaults
from app.domain.repositories.reminder_repository import ReminderRepository
from app.infrastructure.database.models import Reminder


class CreateReminderUseCase:
    def __init__(self, reminder_repository: ReminderRepository):
        self.reminder_repository = reminder_repository

    async def execute(
        self,
        user_id: int,
        label: str,
        notification_timing_mode: str,
        notification_style: str,
        time_of_day: Optional[time] = None,
        days_of_week: Optional[List[int]] = None,
        custom_message: Optional[str] = None,
    ) -> Reminder:
        if notification_timing_mode == "custom":
            resolved_time = time_of_day
            resolved_days = days_of_week
        else:
            resolved_time = notification_defaults.DEFAULT_REMINDER_TIME
            resolved_days = notification_defaults.DEFAULT_REMINDER_DAYS_OF_WEEK

        return await self.reminder_repository.create(
            user_id=user_id,
            label=label,
            time_of_day=resolved_time,
            days_of_week=resolved_days,
            notification_timing_mode=notification_timing_mode,
            notification_style=notification_style,
            custom_message=custom_message if notification_style == "custom_message" else None,
        )
