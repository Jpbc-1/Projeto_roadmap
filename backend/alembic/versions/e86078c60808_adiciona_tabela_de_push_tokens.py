"""adiciona tabela de push tokens

Revision ID: e86078c60808
Revises: 9536c17085b3
Create Date: 2026-08-14 00:26:02.606838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e86078c60808'
down_revision: Union[str, Sequence[str], None] = '9536c17085b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_push_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('push_token', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_push_tokens_push_token'), 'user_push_tokens', ['push_token'], unique=True)
    op.create_index(op.f('ix_user_push_tokens_user_id'), 'user_push_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_push_tokens_user_id'), table_name='user_push_tokens')
    op.drop_index(op.f('ix_user_push_tokens_push_token'), table_name='user_push_tokens')
    op.drop_table('user_push_tokens')
