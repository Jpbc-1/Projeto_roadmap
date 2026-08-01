from datetime import datetime, time
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Reminder, User


class SQLAlchemyReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        label: str,
        time_of_day: time,
        days_of_week: List[int],
        notification_timing_mode: str = "app_default",
        notification_style: str = "app_generated",
        custom_message: Optional[str] = None,
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            label=label,
            time_of_day=time_of_day,
            days_of_week=days_of_week,
            is_active=True,
            notification_timing_mode=notification_timing_mode,
            notification_style=notification_style,
            custom_message=custom_message,
        )
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def list_by_user(self, user_id: int) -> List[Reminder]:
        result = await self.session.execute(
            select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.time_of_day)
        )
        return list(result.scalars().all())

    async def get_by_id(self, reminder_id: int) -> Optional[Reminder]:
        result = await self.session.execute(select(Reminder).where(Reminder.id == reminder_id))
        return result.scalar_one_or_none()

    async def update(self, reminder_id: int, **fields: Any) -> Reminder:
        reminder = await self.get_by_id(reminder_id)
        if reminder is None:
            raise ValueError(f"Reminder {reminder_id} não encontrado para atualização.")

        for field_name, value in fields.items():
            setattr(reminder, field_name, value)

        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def delete(self, reminder_id: int) -> None:
        reminder = await self.get_by_id(reminder_id)
        if reminder is not None:
            await self.session.delete(reminder)
            await self.session.commit()

    async def list_due(self, now_utc: datetime) -> List[Reminder]:
        # JOIN com User pra ter o fuso de cada dono junto -- sem isso, "8h"
        # significaria coisas diferentes (e provavelmente erradas) pra
        # gente em fusos diferentes do servidor. Filtra em Python porque
        # comparar "dia da semana + hora, já convertido pro fuso de cada
        # linha" não dá pra expressar direto num WHERE simples.
        result = await self.session.execute(
            select(Reminder, User.timezone)
            .join(User, User.id == Reminder.user_id)
            .where(Reminder.is_active.is_(True))
        )

        due: List[Reminder] = []
        for reminder, user_timezone in result.all():
            try:
                tz = ZoneInfo(user_timezone)
            except Exception:
                tz = ZoneInfo("UTC")  # defensivo: fuso inválido salvo por engano não deveria travar o agendador

            local_now = now_utc.astimezone(tz)
            our_weekday = (local_now.weekday() + 1) % 7  # Python: 0=segunda -> nosso: 0=domingo

            if our_weekday not in reminder.days_of_week:
                continue
            if reminder.time_of_day.replace(second=0, microsecond=0) == local_now.time().replace(
                second=0, microsecond=0
            ):
                due.append(reminder)

        return due
