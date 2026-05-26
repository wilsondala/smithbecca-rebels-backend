"""create home sections table

Revision ID: af5a3f3aed0b
Revises: 207b298b7015
Create Date: 2026-03-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "af5a3f3aed0b"
down_revision: Union[str, None] = "207b298b7015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "home_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_home_sections_id"), "home_sections", ["id"], unique=False)
    op.create_index(op.f("ix_home_sections_key"), "home_sections", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_home_sections_key"), table_name="home_sections")
    op.drop_index(op.f("ix_home_sections_id"), table_name="home_sections")
    op.drop_table("home_sections")