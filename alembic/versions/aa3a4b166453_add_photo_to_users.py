"""add photo to users

Revision ID: aa3a4b166453
Revises: f2ccbdbe688e
Create Date: 2026-03-01 22:39:00.047644
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "aa3a4b166453"
down_revision: Union[str, None] = "f2ccbdbe688e"
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

    if not table_exists(conn, "users"):
        return

    if column_exists(conn, "users", "photo"):
        return

    op.add_column(
        "users",
        sa.Column("photo", sa.String(), nullable=True)
    )


def downgrade() -> None:
    conn = op.get_bind()

    if not table_exists(conn, "users"):
        return

    if not column_exists(conn, "users", "photo"):
        return

    op.drop_column("users", "photo")