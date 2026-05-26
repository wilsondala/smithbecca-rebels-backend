"""add facebook_id to users

Revision ID: 1497e41fe609
Revises: c7d91e4f2b55
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "1497e41fe609"
down_revision = "c7d91e4f2b55"
branch_labels = None
depends_on = None


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


def index_exists(conn, index_name):
    return conn.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE indexname = :index_name
            );
        """),
        {"index_name": index_name},
    ).scalar()


def upgrade():
    conn = op.get_bind()

    if not table_exists(conn, "users"):
        return

    if not column_exists(conn, "users", "facebook_id"):
        op.add_column(
            "users",
            sa.Column("facebook_id", sa.String(), nullable=True)
        )

    if not index_exists(conn, "ix_users_facebook_id"):
        op.create_index(
            "ix_users_facebook_id",
            "users",
            ["facebook_id"],
            unique=True
        )


def downgrade():
    pass