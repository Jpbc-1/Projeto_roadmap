from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import PaginationParams, get_current_user
from app.api.v1.schemas.reminders import (
    ReminderCreate,
    ReminderOut,
    ReminderToggleRequest,
    ReminderUpdate,
)
from app.application.reminders.create_reminder import CreateReminderUseCase
from app.application.reminders.delete_reminder import (
    DeleteReminderUseCase,
    ReminderAccessDeniedError as DeleteReminderAccessDeniedError,
    ReminderNotFoundError as DeleteReminderNotFoundError,
)
from app.application.reminders.get_reminder import (
    GetReminderUseCase,
    ReminderAccessDeniedError as GetReminderAccessDeniedError,
    ReminderNotFoundError as GetReminderNotFoundError,
)
from app.application.reminders.list_reminders import ListRemindersUseCase
from app.application.reminders.toggle_reminder import (
    ReminderAccessDeniedError as ToggleReminderAccessDeniedError,
    ReminderNotFoundError as ToggleReminderNotFoundError,
    ToggleReminderUseCase,
)
from app.application.reminders.update_reminder import (
    ReminderAccessDeniedError as UpdateReminderAccessDeniedError,
    ReminderNotFoundError as UpdateReminderNotFoundError,
    UpdateReminderUseCase,
)
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.reminder_repository import SQLAlchemyReminderRepository

router = APIRouter()


@router.post("", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    payload: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = CreateReminderUseCase(repository)
    return await use_case.execute(
        user_id=current_user.id,
        label=payload.label,
        notification_timing_mode=payload.notification_timing_mode,
        notification_style=payload.notification_style,
        time_of_day=payload.time_of_day,
        days_of_week=payload.days_of_week,
        custom_message=payload.custom_message,
    )


@router.get("", response_model=List[ReminderOut])
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    pagination: PaginationParams = Depends(PaginationParams),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = ListRemindersUseCase(repository)
    return await use_case.execute(current_user.id, limit=pagination.limit, offset=pagination.offset)


@router.get("/{reminder_id}", response_model=ReminderOut)
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = GetReminderUseCase(repository)
    try:
        return await use_case.execute(reminder_id, current_user.id)
    except (GetReminderNotFoundError, GetReminderAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado.")


@router.put("/{reminder_id}", response_model=ReminderOut)
async def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = UpdateReminderUseCase(repository)
    try:
        return await use_case.execute(
            reminder_id,
            current_user.id,
            label=payload.label,
            notification_timing_mode=payload.notification_timing_mode,
            notification_style=payload.notification_style,
            time_of_day=payload.time_of_day,
            days_of_week=payload.days_of_week,
            custom_message=payload.custom_message,
        )
    except (UpdateReminderNotFoundError, UpdateReminderAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado.")


@router.patch("/{reminder_id}/toggle", response_model=ReminderOut)
async def toggle_reminder(
    reminder_id: int,
    payload: ReminderToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = ToggleReminderUseCase(repository)
    try:
        return await use_case.execute(reminder_id, current_user.id, payload.is_active)
    except (ToggleReminderNotFoundError, ToggleReminderAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado.")


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = SQLAlchemyReminderRepository(db)
    use_case = DeleteReminderUseCase(repository)
    try:
        await use_case.execute(reminder_id, current_user.id)
    except (DeleteReminderNotFoundError, DeleteReminderAccessDeniedError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lembrete não encontrado.")
