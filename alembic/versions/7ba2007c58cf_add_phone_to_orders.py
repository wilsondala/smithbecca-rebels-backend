"""add phone to orders

Revision ID: 7ba2007c58cf
Revises: 6a6d9783226c
Create Date: 2026-04-21 00:15:31.772797
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "7ba2007c58cf"
down_revision: Union[str, None] = "6a6d9783226c"
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

    if column_exists(conn, "orders", "phone"):
        return

    op.add_column(
        "orders",
        sa.Column("phone", sa.String(length=20), nullable=True)
    )


def downgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "orders"):
        return

    if not column_exists(conn, "orders", "phone"):
        return

    op.drop_column("orders", "phone")