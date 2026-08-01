"""adiciona plano/creditos/fuso ao usuario e tabela de uso de ia

Revision ID: 5196ae2e4e44
Revises: a9939b0b4b4b
Create Date: 2026-08-01 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5196ae2e4e44'
down_revision: Union[str, Sequence[str], None] = 'a9939b0b4b4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('plan', sa.String(length=20), server_default='free', nullable=False))
    op.add_column(
        'users', sa.Column('credits_remaining', sa.Integer(), server_default='500', nullable=False)
    )
    op.add_column(
        'users',
        sa.Column('timezone', sa.String(length=50), server_default='America/Sao_Paulo', nullable=False),
    )

    op.create_table(
        'ai_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('completion_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_usage_logs_user_id'), 'ai_usage_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_usage_logs_action'), 'ai_usage_logs', ['action'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_ai_usage_logs_action'), table_name='ai_usage_logs')
    op.drop_index(op.f('ix_ai_usage_logs_user_id'), table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')

    op.drop_column('users', 'timezone')
    op.drop_column('users', 'credits_remaining')
    op.drop_column('users', 'plan')
