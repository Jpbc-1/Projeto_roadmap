"""adiciona controle de disparo pra dedup entre replicas

Revision ID: 9536c17085b3
Revises: 32230bbbee21
Create Date: 2026-08-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9536c17085b3'
down_revision: Union[str, Sequence[str], None] = '32230bbbee21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("reminders", sa.Column("last_dispatched_date", sa.Date(), nullable=True))
    op.add_column(
        "calendar_events", sa.Column("reminder_dispatched_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("calendar_events", "reminder_dispatched_at")
    op.drop_column("reminders", "last_dispatched_date")
