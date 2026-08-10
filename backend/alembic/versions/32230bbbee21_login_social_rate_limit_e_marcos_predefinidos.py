"""login social, rate limit (sem mudanca de schema) e marcos predefinidos

Revision ID: 32230bbbee21
Revises: 3d1b50e88466
Create Date: 2026-08-02 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32230bbbee21'
down_revision: Union[str, Sequence[str], None] = '3d1b50e88466'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# As 10 conquistas do MVP -- ver docs/adr/0004 pro porquê de serem
# predefinidas/determinísticas, não decididas pela IA. icon_url fica NULL
# de propósito: ainda não existe asset pra cada uma: preencher depois com
# um UPDATE simples (não outra migração) quando o design entregar os ícones.
ACHIEVEMENTS_SEED = [
    {"name": "Primeira Missão", "description": "Complete sua primeira missão.", "required_condition": "missions_1"},
    {"name": "Ganhando Ritmo", "description": "Complete 10 missões.", "required_condition": "missions_10"},
    {"name": "Consistência", "description": "Complete 50 missões.", "required_condition": "missions_50"},
    {"name": "Centurião", "description": "Complete 100 missões.", "required_condition": "missions_100"},
    {"name": "Primeiro Capítulo", "description": "Complete o primeiro capítulo de uma jornada.", "required_condition": "chapters_1"},
    {"name": "Trilha Andada", "description": "Complete 10 capítulos ao todo, em qualquer jornada.", "required_condition": "chapters_10"},
    {"name": "Uma Semana Seguida", "description": "Mantenha uma sequência de 7 dias.", "required_condition": "streak_7"},
    {"name": "Um Mês Inteiro", "description": "Mantenha uma sequência de 30 dias.", "required_condition": "streak_30"},
    {"name": "Hábito de Verdade", "description": "Mantenha uma sequência de 100 dias.", "required_condition": "streak_100"},
    {"name": "Objetivo Conquistado", "description": "Complete um objetivo inteiro, do início ao fim.", "required_condition": "goals_1"},
]


def upgrade() -> None:
    """Upgrade schema."""
    # --- Login social: password_hash vira opcional ---
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=True)

    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_account"),
    )
    op.create_index(op.f("ix_oauth_accounts_user_id"), "oauth_accounts", ["user_id"], unique=False)

    # --- Marcos: semeia as definições (achievements já existia, só não
    # tinha linha nenhuma -- rate limit de login não muda schema nenhum,
    # é só código em cima do que já existe) ---
    achievements_table = sa.table(
        "achievements",
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("required_condition", sa.String),
    )
    op.bulk_insert(achievements_table, ACHIEVEMENTS_SEED)


def downgrade() -> None:
    """Downgrade schema."""
    conditions = [a["required_condition"] for a in ACHIEVEMENTS_SEED]
    op.execute(
        sa.text("DELETE FROM achievements WHERE required_condition = ANY(:conditions)").bindparams(
            conditions=conditions
        )
    )

    op.drop_index(op.f("ix_oauth_accounts_user_id"), table_name="oauth_accounts")
    op.drop_table("oauth_accounts")

    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)
