from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.calendar_events import (
    CalendarEventCreate,
    CalendarEventOut,
    CalendarEventUpdate,
)
from app.application.calendar_events.create_calendar_event import CreateCalendarEventUseCase
from app.application.calendar_events.delete_calendar_event import (
    CalendarEventAccessDeniedError as DeleteAccessDeniedError,
    CalendarEventNotFoundError as DeleteNotFoundError,
    DeleteCalendarEventUseCase,
)
from app.application.calendar_events.get_calendar_event import (
    CalendarEventAccessDeniedError as GetAccessDeniedError,
    CalendarEventNotFoundError as GetNotFoundError,
    GetCalendarEventUseCase,
)
from app.application.calendar_events.list_calendar_events import ListCalendarEventsUseCase
from app.application.calendar_events.update_calendar_event import (
    CalendarEventAccessDeniedError as UpdateAccessDeniedError,
    CalendarEventNotFoundError as UpdateNotFoundError,
    UpdateCalendarEventUseCase,
)
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.calendar_event_repository import SQLAlchemyCalendarEventRepository

router = APIRouter()


@router.post("", response_model=CalendarEventOut, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyCalendarEventRepository(db)
    use_case = CreateCalendarEventUseCase(repository)
    return await use_case.execute(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        is_all_day=payload.is_all_day,
        notify_enabled=payload.notify_enabled,
        remind_before_minutes=payload.remind_before_minutes,
        notification_timing_mode=payload.notification_timing_mode,
        notification_style=payload.notification_style,
        custom_message=payload.custom_message,
    )


@router.get("", response_model=List[CalendarEventOut])
async def list_calendar_events(
    start: datetime = Query(..., description="Início do intervalo, ISO 8601"),
    end: datetime = Query(..., description="Fim do intervalo, ISO 8601"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """É este endpoint que o botão 'abrir calendário' do app chama -- o
    front manda o intervalo visível (semana/mês na tela) e recebe só os
    compromissos daquela janela."""
    repository = SQLAlchemyCalendarEventRepository(db)
    use_case = ListCalendarEventsUseCase(repository)
    return await use_case.execute(current_user.id, start, end)


@router.get("/{event_id}", response_model=CalendarEventOut)
async def get_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyCalendarEventRepository(db)
    use_case = GetCalendarEventUseCase(repository)
    try:
        return await use_case.execute(event_id, current_user.id)
    except (GetNotFoundError, GetAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compromisso não encontrado.")


@router.put("/{event_id}", response_model=CalendarEventOut)
async def update_calendar_event(
    event_id: int,
    payload: CalendarEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyCalendarEventRepository(db)
    use_case = UpdateCalendarEventUseCase(repository)
    try:
        return await use_case.execute(
            event_id,
            current_user.id,
            title=payload.title,
            description=payload.description,
            start_datetime=payload.start_datetime,
            end_datetime=payload.end_datetime,
            is_all_day=payload.is_all_day,
            notify_enabled=payload.notify_enabled,
            remind_before_minutes=payload.remind_before_minutes,
            notification_timing_mode=payload.notification_timing_mode,
            notification_style=payload.notification_style,
            custom_message=payload.custom_message,
        )
    except (UpdateNotFoundError, UpdateAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compromisso não encontrado.")


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyCalendarEventRepository(db)
    use_case = DeleteCalendarEventUseCase(repository)
    try:
        await use_case.execute(event_id, current_user.id)
    except (DeleteNotFoundError, DeleteAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compromisso não encontrado.")
