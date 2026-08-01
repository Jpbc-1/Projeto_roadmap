"""adiciona is_conceptual e created_by

Revision ID: 37504cc44ca1
Revises: 1c8a4cf1df49
Create Date: 2026-07-28 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37504cc44ca1'
down_revision: Union[str, Sequence[str], None] = '1c8a4cf1df49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default garante que linhas já existentes recebem um valor válido
    # na hora (diferente de outras colunas boolean/string deste projeto que
    # foram adicionadas sem default -- só funciona em tabela vazia). Aqui dá
    # pra rodar com segurança mesmo com dados de teste já no banco.
    op.add_column(
        'missions',
        sa.Column('is_conceptual', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )
    op.add_column(
        'missions',
        sa.Column('created_by', sa.String(length=10), server_default='ai', nullable=False),
    )
    op.add_column(
        'roadmap_chapters',
        sa.Column('created_by', sa.String(length=10), server_default='ai', nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('roadmap_chapters', 'created_by')
    op.drop_column('missions', 'created_by')
    op.drop_column('missions', 'is_conceptual')
