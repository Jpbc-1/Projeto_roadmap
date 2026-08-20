"""merge branches

Revision ID: 7e5dfea2e2c3
Revises: 9536c17085b3, 9de52acef24d
Create Date: 2026-08-18 09:51:09.686385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e5dfea2e2c3'
down_revision: Union[str, Sequence[str], None] = ('9536c17085b3', '9de52acef24d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
