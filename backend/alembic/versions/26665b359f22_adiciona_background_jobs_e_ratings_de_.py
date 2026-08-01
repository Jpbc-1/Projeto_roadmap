"""adiciona background_jobs e ratings de missao

Revision ID: 26665b359f22
Revises: 37504cc44ca1
Create Date: 2026-07-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26665b359f22'
down_revision: Union[str, Sequence[str], None] = '37504cc44ca1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'background_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='3', nullable=False),
        sa.Column('run_after', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_background_jobs_job_type'), 'background_jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_background_jobs_status'), 'background_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_background_jobs_user_id'), 'background_jobs', ['user_id'], unique=False)

    # Ambas nullable/opcionais de propósito -- o front decide quando vale a
    # pena perguntar isso pro usuário, nem toda missão concluída vai ter.
    op.add_column('mission_executions', sa.Column('difficulty_rating', sa.String(length=20), nullable=True))
    op.add_column('mission_executions', sa.Column('satisfaction_rating', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('mission_executions', 'satisfaction_rating')
    op.drop_column('mission_executions', 'difficulty_rating')

    op.drop_index(op.f('ix_background_jobs_user_id'), table_name='background_jobs')
    op.drop_index(op.f('ix_background_jobs_status'), table_name='background_jobs')
    op.drop_index(op.f('ix_background_jobs_job_type'), table_name='background_jobs')
    op.drop_table('background_jobs')
