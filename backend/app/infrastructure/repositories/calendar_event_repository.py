from datetime import datetime, timedelta
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import CalendarEvent


class SQLAlchemyCalendarEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        title: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        is_all_day: bool = False,
        notify_enabled: bool = True,
        remind_before_minutes: Optional[int] = None,
        notification_timing_mode: str = "app_default",
        notification_style: str = "app_generated",
        custom_message: Optional[str] = None,
    ) -> CalendarEvent:
        event = CalendarEvent(
            user_id=user_id,
            title=title,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_all_day=is_all_day,
            notify_enabled=notify_enabled,
            remind_before_minutes=remind_before_minutes,
            notification_timing_mode=notification_timing_mode,
            notification_style=notification_style,
            custom_message=custom_message,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_by_range(self, user_id: int, start: datetime, end: datetime) -> List[CalendarEvent]:
        result = await self.session.execute(
            select(CalendarEvent)
            .where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_datetime >= start,
                CalendarEvent.start_datetime <= end,
            )
            .order_by(CalendarEvent.start_datetime)
        )
        return list(result.scalars().all())

    async def get_by_id(self, event_id: int) -> Optional[CalendarEvent]:
        result = await self.session.execute(select(CalendarEvent).where(CalendarEvent.id == event_id))
        return result.scalar_one_or_none()

    async def update(self, event_id: int, **fields: Any) -> CalendarEvent:
        event = await self.get_by_id(event_id)
        if event is None:
            raise ValueError(f"CalendarEvent {event_id} não encontrado para atualização.")

        for field_name, value in fields.items():
            setattr(event, field_name, value)

        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def delete(self, event_id: int) -> None:
        event = await self.get_by_id(event_id)
        if event is not None:
            await self.session.delete(event)
            await self.session.commit()

    async def list_due_reminders(self, now_utc: datetime) -> List[CalendarEvent]:
        # start_datetime é absoluto (tz-aware) -- comparar com now_utc não
        # precisa converter fuso nenhum, diferente do Reminder.list_due.
        # Janela generosa (remind_before_minutes vai até 7 dias) filtrada
        # fino em Python -- mais simples/portável que aritmética de
        # intervalo no SQL (sqlite em teste, Postgres em produção).
        horizon = now_utc + timedelta(days=8)
        result = await self.session.execute(
            select(CalendarEvent).where(
                CalendarEvent.notify_enabled.is_(True),
                CalendarEvent.remind_before_minutes.is_not(None),
                CalendarEvent.start_datetime >= now_utc,
                CalendarEvent.start_datetime <= horizon,
            )
        )
        candidates = result.scalars().all()

        due = []
        for event in candidates:
            fire_at = event.start_datetime - timedelta(minutes=event.remind_before_minutes)
            if now_utc <= fire_at < now_utc + timedelta(minutes=1):
                due.append(event)
        return due
