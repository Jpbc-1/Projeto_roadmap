"""adiciona constraint unica em mission_executions

Revision ID: a9939b0b4b4b
Revises: 6d1111db572f
Create Date: 2026-07-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9939b0b4b4b'
down_revision: Union[str, Sequence[str], None] = '6d1111db572f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Antes de adicionar a constraint, remove qualquer duplicata que já
    # exista (mantém a execução mais antiga -- menor id -- de cada par
    # mission_id+user_id, apaga o resto). Sem isso, ADD CONSTRAINT falharia
    # de cara em qualquer ambiente que já tenha sofrido a corrida que essa
    # constraint existe pra prevenir daqui pra frente.
    #
    # IMPORTANTE: isso limpa as LINHAS duplicadas, mas não recalcula
    # retroativamente user_stats.total_xp/streak -- se uma duplicata já
    # tiver acontecido antes desta migration, o XP daquele momento já foi
    # contado duas vezes e continua assim (só novas duplicatas ficam
    # impossíveis a partir daqui). Se isso importar pro seu ambiente, vale
    # conferir manualmente os totais de quem tinha `mission_executions`
    # duplicado antes de rodar esta migration.
    op.execute(
        """
        DELETE FROM mission_executions
        WHERE id NOT IN (
            SELECT MIN(id) FROM mission_executions GROUP BY mission_id, user_id
        )
        """
    )

    op.create_unique_constraint(
        "uq_mission_execution_user", "mission_executions", ["mission_id", "user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_mission_execution_user", "mission_executions", type_="unique")
