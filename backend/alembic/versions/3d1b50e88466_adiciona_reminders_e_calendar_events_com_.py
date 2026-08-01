"""adiciona reminders e calendar_events com preferencias de notificacao

Revision ID: 3d1b50e88466
Revises: 5196ae2e4e44
Create Date: 2026-08-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d1b50e88466'
down_revision: Union[str, Sequence[str], None] = '5196ae2e4e44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=120), nullable=False),
        sa.Column('time_of_day', sa.Time(), nullable=False),
        sa.Column('days_of_week', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('notification_timing_mode', sa.String(length=20), server_default='app_default', nullable=False),
        sa.Column('notification_style', sa.String(length=20), server_default='app_generated', nullable=False),
        sa.Column('custom_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reminders_user_id'), 'reminders', ['user_id'], unique=False)

    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('notify_enabled', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('remind_before_minutes', sa.Integer(), nullable=True),
        sa.Column('notification_timing_mode', sa.String(length=20), server_default='app_default', nullable=False),
        sa.Column('notification_style', sa.String(length=20), server_default='app_generated', nullable=False),
        sa.Column('custom_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_calendar_events_user_id'), table_name='calendar_events')
    op.drop_table('calendar_events')

    op.drop_index(op.f('ix_reminders_user_id'), table_name='reminders')
    op.drop_table('reminders')
