"""add photo to users

Revision ID: f2ccbdbe688e
Revises: 47ae8725a2c4
Create Date: 2026-03-01 09:24:30.143280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2ccbdbe688e'
down_revision: Union[str, None] = '47ae8725a2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
