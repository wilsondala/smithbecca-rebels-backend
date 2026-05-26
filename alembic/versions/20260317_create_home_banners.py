"""create home_banners table

Revision ID: 20260317_create_home_banners
Revises: 174f045ba7ac
Create Date: 2026-03-17 14:30:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260317_create_home_banners"
down_revision = "174f045ba7ac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "home_banners",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("button_text", sa.String(), nullable=True),
        sa.Column("button_link", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("mobile_image_url", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_home_banners_id", "home_banners", ["id"], unique=False)
    op.create_index("ix_home_banners_position", "home_banners", ["position"], unique=False)
    op.create_index("ix_home_banners_is_active", "home_banners", ["is_active"], unique=False)


def downgrade():
    op.drop_index("ix_home_banners_is_active", table_name="home_banners")
    op.drop_index("ix_home_banners_position", table_name="home_banners")
    op.drop_index("ix_home_banners_id", table_name="home_banners")
    op.drop_table("home_banners")