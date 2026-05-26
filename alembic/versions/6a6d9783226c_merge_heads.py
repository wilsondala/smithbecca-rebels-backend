"""merge heads

Revision ID: 6a6d9783226c
Revises: 20260325_add_variations, ff7a8ade3b4d
Create Date: 2026-04-19 20:59:53.388107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a6d9783226c'
down_revision: Union[str, None] = ('20260325_add_variations', 'ff7a8ade3b4d')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
