"""add product_image to order_items

Revision ID: ff7a8ade3b4d
Revises: 15f53de40591
Create Date: 2026-04-15 16:13:51.772146
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "ff7a8ade3b4d"
down_revision: Union[str, None] = "15f53de40591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, table_name: str) -> bool:
    return conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = :table_name
            );
        """),
        {"table_name": table_name},
    ).scalar()


def column_exists(conn, table_name: str, column_name: str) -> bool:
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

    if table_exists(conn, "reviews"):
        op.drop_table("reviews")

    if table_exists(conn, "order_items") and not column_exists(conn, "order_items", "product_image"):
        op.add_column(
            "order_items",
            sa.Column("product_image", sa.String(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()

    if table_exists(conn, "order_items") and column_exists(conn, "order_items", "product_image"):
        op.drop_column("order_items", "product_image")