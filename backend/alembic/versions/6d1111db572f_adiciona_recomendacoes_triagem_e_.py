"""adiciona recomendacoes, triagem inicial e adaptacao proposta

Revision ID: 6d1111db572f
Revises: 26665b359f22
Create Date: 2026-07-31 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d1111db572f'
down_revision: Union[str, Sequence[str], None] = '26665b359f22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'goal_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_paid', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_goal_recommendations_goal_id'), 'goal_recommendations', ['goal_id'], unique=False
    )

    # Triagem inicial (IntakeGoalUseCase): melhora a redação do pedido e
    # detecta informação faltando antes de gerar o roadmap de verdade.
    op.add_column('goals', sa.Column('improved_prompt', sa.Text(), nullable=True))
    op.add_column('goals', sa.Column('pending_questions', sa.JSON(), nullable=True))

    # Adaptação "git-like": proposta de operação (replace_chapter/
    # insert_chapter) fica aqui até o usuário confirmar ou rejeitar.
    op.add_column('roadmaps', sa.Column('pending_adaptation', sa.JSON(), nullable=True))

    # Trava um capítulo específico contra mudanças automáticas da IA.
    op.add_column(
        'roadmap_chapters',
        sa.Column('is_locked_from_ai', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('roadmap_chapters', 'is_locked_from_ai')
    op.drop_column('roadmaps', 'pending_adaptation')
    op.drop_column('goals', 'pending_questions')
    op.drop_column('goals', 'improved_prompt')

    op.drop_index(op.f('ix_goal_recommendations_goal_id'), table_name='goal_recommendations')
    op.drop_table('goal_recommendations')
