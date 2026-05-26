"""add google auth fields to users

Revision ID: 9f4c2d1b7a10
Revises: fedb43ee6d9d
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "9f4c2d1b7a10"
down_revision = "fedb43ee6d9d"
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

    if not column_exists(conn, "users", "auth_provider"):
        op.add_column(
            "users",
            sa.Column(
                "auth_provider",
                sa.String(),
                nullable=True,
                server_default="local",
            ),
        )

    if not column_exists(conn, "users", "google_id"):
        op.add_column(
            "users",
            sa.Column("google_id", sa.String(), nullable=True),
        )

    conn.execute(
        text("""
            UPDATE users
            SET auth_provider = 'local'
            WHERE auth_provider IS NULL
        """)
    )

    op.alter_column(
        "users",
        "auth_provider",
        existing_type=sa.String(),
        nullable=False,
        server_default=None,
    )

    if not index_exists(conn, "ix_users_google_id"):
        op.create_index(
            "ix_users_google_id",
            "users",
            ["google_id"],
            unique=True,
        )


def downgrade():
    pass