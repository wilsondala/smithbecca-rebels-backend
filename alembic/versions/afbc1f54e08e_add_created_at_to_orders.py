"""add created_at to orders

Revision ID: afbc1f54e08e
Revises: 6c59823c62f1
Create Date: 2026-02-24 01:41:01.814452
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "afbc1f54e08e"
down_revision: Union[str, None] = "6c59823c62f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name):
    return conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = :table_name
            );
        """),
        {"table_name": table_name},
    ).scalar()


def column_exists(conn, table_name, column_name):
    return conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_name = :table_name
                AND column_name = :column_name
            );
        """),
        {"table_name": table_name, "column_name": column_name},
    ).scalar()


def upgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "orders"):
        return

    if column_exists(conn, "orders", "created_at"):
        return

    op.add_column(
        "orders",
        sa.Column("created_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "orders"):
        return

    if not column_exists(conn, "orders", "created_at"):
        return

    op.drop_column("orders", "created_at")