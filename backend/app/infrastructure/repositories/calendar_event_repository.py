from datetime import datetime, timedelta
from typing import Any, List, Optional

from sqlalchemy import func, select, update
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
        horizon_back = now_utc - timedelta(days=8)
        result = await self.session.execute(
            select(CalendarEvent).where(
                CalendarEvent.notify_enabled.is_(True),
                CalendarEvent.remind_before_minutes.is_not(None),
                CalendarEvent.reminder_dispatched_at.is_(None),
                CalendarEvent.start_datetime >= horizon_back,
            )
        )
        candidates = result.scalars().all()

        due = []
        for event in candidates:
            fire_at = event.start_datetime - timedelta(minutes=event.remind_before_minutes)
            if fire_at <= now_utc:
                due.append(event)
        return due

    async def try_claim_dispatch(self, event_id: int) -> bool:
        result = await self.session.execute(
            update(CalendarEvent)
            .where(CalendarEvent.id == event_id, CalendarEvent.reminder_dispatched_at.is_(None))
            .values(reminder_dispatched_at=func.now())
        )
        await self.session.commit()
        return result.rowcount > 0
