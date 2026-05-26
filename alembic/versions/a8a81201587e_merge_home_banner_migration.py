"""merge home banner migration

Revision ID: a8a81201587e
Revises: fedb43ee6d9d, 20260317_create_home_banners
Create Date: 2026-03-17 19:57:43.880530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8a81201587e'
down_revision: Union[str, None] = ('fedb43ee6d9d', '20260317_create_home_banners')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
