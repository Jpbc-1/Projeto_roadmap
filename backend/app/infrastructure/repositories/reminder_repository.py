from datetime import datetime, time
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select, update
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

    async def list_by_user(self, user_id: int, limit: int, offset: int) -> List[Reminder]:
        result = await self.session.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.time_of_day, Reminder.id)
            .limit(limit)
            .offset(offset)
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
                tz = ZoneInfo("UTC") 

            local_now = now_utc.astimezone(tz)
            our_weekday = (local_now.weekday() + 1) % 7 
            today_local = local_now.date()

            if our_weekday not in reminder.days_of_week:
                continue
            if local_now.time() < reminder.time_of_day:
                continue  
            if reminder.last_dispatched_date == today_local:
                continue  

            due.append(reminder)

        return due

    async def try_claim_dispatch(self, reminder_id: int) -> bool:
        """Recalcula 'hoje' sozinho, no fuso do DONO do lembrete -- não
        recebe a data de fora. Se o chamador calculasse 'hoje' com
        date.today() (fuso do servidor) e passasse pra cá, essa data podia
        divergir da que list_due usou pra decidir "ainda não disparou
        hoje" pra ESSE MESMO lembrete, bem perto da virada da meia-noite
        -- a mesma pergunta ("que dia é hoje pra essa pessoa") tem que ser
        respondida do mesmo jeito nos dois lugares."""
        result = await self.session.execute(
            select(Reminder, User.timezone).join(User, User.id == Reminder.user_id).where(Reminder.id == reminder_id)
        )
        row = result.first()
        if row is None:
            return False
        _, user_timezone = row

        try:
            today_local = datetime.now(ZoneInfo(user_timezone)).date()
        except Exception:
            today_local = datetime.now(ZoneInfo("UTC")).date()

        update_result = await self.session.execute(
            update(Reminder)
            .where(
                Reminder.id == reminder_id,
                or_(Reminder.last_dispatched_date.is_(None), Reminder.last_dispatched_date < today_local),
            )
            .values(last_dispatched_date=today_local)
        )
        await self.session.commit()
        return update_result.rowcount > 0
