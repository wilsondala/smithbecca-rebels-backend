"""add video fields to home banner

Revision ID: 207b298b7015
Revises: a8a81201587e
Create Date: 2026-03-18 13:48:09.941964
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "207b298b7015"
down_revision: Union[str, None] = "a8a81201587e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("home_banners", sa.Column("video_url", sa.String(), nullable=True))
    op.add_column("home_banners", sa.Column("mobile_video_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("home_banners", "mobile_video_url")
    op.drop_column("home_banners", "video_url")